"""
用户认证相关视图
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from datetime import timedelta
import logging

from .forms import CustomUserCreationForm, CustomLoginForm
from .models import UserProfile, LoginAttempt

logger = logging.getLogger(__name__)

# 登录失败限制配置
MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
LOCKOUT_DURATION = 30  # 锁定时间（分钟）


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """获取用户代理信息"""
    return request.META.get('HTTP_USER_AGENT', '')


def check_login_attempts(username, ip_address):
    """检查登录尝试次数"""
    # 检查最近30分钟内的失败尝试
    time_threshold = timezone.now() - timedelta(minutes=LOCKOUT_DURATION)
    
    failed_attempts = LoginAttempt.objects.filter(
        username=username,
        ip_address=ip_address,
        success=False,
        attempt_time__gte=time_threshold
    ).count()
    
    return failed_attempts >= MAX_LOGIN_ATTEMPTS


def record_login_attempt(username, ip_address, user_agent, success):
    """记录登录尝试"""
    try:
        LoginAttempt.objects.create(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    except Exception as e:
        logger.error(f"记录登录尝试失败: {str(e)}")


@never_cache
def welcome_view(request):
    """欢迎页面 - 系统入口"""
    if request.user.is_authenticated:
        return redirect('index')
    
    context = {
        'page_title': '欢迎使用口罩检测系统'
    }
    return render(request, 'auth/welcome.html', context)


@csrf_protect
@never_cache
def login_view(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            
            # 检查是否被锁定
            if check_login_attempts(username, ip_address):
                messages.error(request, f'登录失败次数过多，请{LOCKOUT_DURATION}分钟后再试')
                record_login_attempt(username, ip_address, user_agent, False)
                return render(request, 'auth/login.html', {'form': form})
            
            # 尝试认证
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # 检查用户配置中的锁定状态
                    try:
                        profile = user.userprofile
                        if profile.is_account_locked():
                            messages.error(request, '账户已被锁定，请联系管理员')
                            record_login_attempt(username, ip_address, user_agent, False)
                            return render(request, 'auth/login.html', {'form': form})
                    except UserProfile.DoesNotExist:
                        # 创建用户配置
                        UserProfile.objects.create(user=user)
                    
                    # 登录成功
                    login(request, user)
                    
                    # 设置会话过期时间
                    if not remember_me:
                        request.session.set_expiry(0)  # 浏览器关闭时过期
                    else:
                        request.session.set_expiry(1209600)  # 2周
                    
                    # 更新用户配置
                    try:
                        profile = user.userprofile
                        profile.last_login_ip = ip_address
                        profile.login_count += 1
                        profile.save()
                    except UserProfile.DoesNotExist:
                        UserProfile.objects.create(
                            user=user,
                            last_login_ip=ip_address,
                            login_count=1
                        )
                    
                    # 记录成功登录
                    record_login_attempt(username, ip_address, user_agent, True)
                    
                    messages.success(request, f'欢迎回来，{user.username}！')
                    
                    # 重定向到原来要访问的页面或首页
                    next_url = request.GET.get('next', 'index')
                    return redirect(next_url)
                else:
                    messages.error(request, '账户已被禁用')
                    record_login_attempt(username, ip_address, user_agent, False)
            else:
                messages.error(request, '用户名或密码错误')
                record_login_attempt(username, ip_address, user_agent, False)
        else:
            messages.error(request, '请检查输入信息')
    else:
        form = CustomLoginForm()
    
    context = {
        'form': form,
        'page_title': '用户登录'
    }
    return render(request, 'auth/login.html', context)


@csrf_protect
@never_cache
def register_view(request):
    """用户注册视图"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # 创建用户
                user = form.save()
                
                # 创建用户配置
                UserProfile.objects.create(
                    user=user,
                    last_login_ip=get_client_ip(request),
                    login_count=0
                )
                
                messages.success(request, '注册成功！请登录您的账户。')
                logger.info(f"新用户注册成功: {user.username}")
                
                return redirect('login')
                
            except Exception as e:
                logger.error(f"用户注册失败: {str(e)}")
                messages.error(request, '注册失败，请重试')
        else:
            messages.error(request, '请检查输入信息')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'page_title': '用户注册'
    }
    return render(request, 'auth/register.html', context)


@login_required
def logout_view(request):
    """用户退出登录"""
    username = request.user.username
    logout(request)
    messages.success(request, f'再见，{username}！')
    return redirect('welcome')


@login_required
def profile_view(request):
    """用户个人资料页面"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # 获取最近的登录记录
    recent_logins = LoginAttempt.objects.filter(
        username=request.user.username,
        success=True
    ).order_by('-attempt_time')[:10]
    
    context = {
        'profile': profile,
        'recent_logins': recent_logins,
        'page_title': '个人资料'
    }
    return render(request, 'auth/profile.html', context)
