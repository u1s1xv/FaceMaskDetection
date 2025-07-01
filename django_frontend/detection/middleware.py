"""
安全中间件
"""
import logging
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from datetime import timedelta

from .models import LoginAttempt

logger = logging.getLogger(__name__)

# 安全配置
MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
LOCKOUT_DURATION = 30  # 锁定时间（分钟）
MONITOR_WINDOW = 30  # 监控窗口（分钟）


class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 在视图处理之前执行
        response = self.process_request(request)
        if response:
            return response
        
        # 处理视图
        response = self.get_response(request)
        
        # 在视图处理之后执行
        return self.process_response(request, response)
    
    def process_request(self, request):
        """请求预处理"""
        # 检查IP是否被锁定
        if self.is_ip_locked(request):
            return self.handle_locked_ip(request)
        
        return None
    
    def process_response(self, request, response):
        """响应后处理"""
        # 添加安全头
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_locked(self, request):
        """检查IP是否被锁定"""
        ip_address = self.get_client_ip(request)
        
        # 检查最近时间窗口内的失败尝试
        time_threshold = timezone.now() - timedelta(minutes=MONITOR_WINDOW)
        
        failed_attempts = LoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            attempt_time__gte=time_threshold
        ).count()
        
        return failed_attempts >= MAX_LOGIN_ATTEMPTS
    
    def handle_locked_ip(self, request):
        """处理被锁定的IP"""
        logger.warning(f"IP {self.get_client_ip(request)} 被锁定，尝试访问 {request.path}")
        
        # 如果是AJAX请求，返回JSON响应
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'error': f'IP地址已被锁定，请{LOCKOUT_DURATION}分钟后再试'
            }, status=429)
        
        # 普通请求重定向到欢迎页面并显示消息
        messages.error(request, f'您的IP地址因多次登录失败已被锁定，请{LOCKOUT_DURATION}分钟后再试')
        return redirect('welcome')


class CSRFFailureMiddleware:
    """CSRF失败处理中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """处理CSRF异常"""
        from django.middleware.csrf import CsrfViewMiddleware
        
        if isinstance(exception, CsrfViewMiddleware):
            logger.warning(f"CSRF验证失败 - IP: {self.get_client_ip(request)}, Path: {request.path}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'CSRF验证失败，请刷新页面重试'
                }, status=403)
            
            messages.error(request, 'CSRF验证失败，请刷新页面重试')
            return redirect('welcome')
        
        return None
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestLoggingMiddleware:
    """请求日志中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 记录请求开始时间
        start_time = timezone.now()
        
        # 处理请求
        response = self.get_response(request)
        
        # 计算处理时间
        process_time = (timezone.now() - start_time).total_seconds()
        
        # 记录请求日志
        if process_time > 5:  # 只记录处理时间超过5秒的请求
            logger.warning(
                f"慢请求 - IP: {self.get_client_ip(request)}, "
                f"Path: {request.path}, "
                f"Method: {request.method}, "
                f"Time: {process_time:.2f}s, "
                f"Status: {response.status_code}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
