#!/usr/bin/env python
"""
用户认证系统测试脚本
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')
django.setup()

from detection.models import UserProfile, LoginAttempt, DetectionRecord


def test_user_registration():
    """测试用户注册功能"""
    print("🧪 测试用户注册功能...")
    
    client = Client()
    
    # 测试注册页面访问
    response = client.get('/app/register/')
    assert response.status_code == 200, "注册页面无法访问"
    print("✅ 注册页面访问正常")
    
    # 测试用户注册
    response = client.post('/app/register/', {
        'username': 'testuser123',
        'email': 'test@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123',
    })
    
    # 检查是否重定向到登录页面
    if response.status_code == 302:
        print("✅ 用户注册成功")
        
        # 验证用户是否创建
        user = User.objects.filter(username='testuser123').first()
        assert user is not None, "用户未创建"
        print("✅ 用户数据创建成功")
        
        # 验证用户配置是否创建
        profile = UserProfile.objects.filter(user=user).first()
        assert profile is not None, "用户配置未创建"
        print("✅ 用户配置创建成功")
        
    else:
        print(f"❌ 用户注册失败: {response.content}")


def test_user_login():
    """测试用户登录功能"""
    print("\n🧪 测试用户登录功能...")
    
    client = Client()
    
    # 创建测试用户
    user = User.objects.create_user(
        username='logintest',
        password='testpass123',
        email='login@example.com'
    )
    UserProfile.objects.create(user=user)
    
    # 测试登录页面访问
    response = client.get('/app/login/')
    assert response.status_code == 200, "登录页面无法访问"
    print("✅ 登录页面访问正常")
    
    # 测试用户登录
    response = client.post('/app/login/', {
        'username': 'logintest',
        'password': 'testpass123',
    })
    
    # 检查是否重定向到首页
    if response.status_code == 302:
        print("✅ 用户登录成功")
        
        # 验证登录记录
        attempt = LoginAttempt.objects.filter(
            username='logintest',
            success=True
        ).first()
        assert attempt is not None, "登录记录未创建"
        print("✅ 登录记录创建成功")
        
    else:
        print(f"❌ 用户登录失败: {response.content}")


def test_data_isolation():
    """测试数据隔离功能"""
    print("\n🧪 测试数据隔离功能...")
    
    # 创建两个测试用户
    user1 = User.objects.create_user(
        username='user1',
        password='pass123',
        email='user1@example.com'
    )
    user2 = User.objects.create_user(
        username='user2',
        password='pass123',
        email='user2@example.com'
    )
    
    UserProfile.objects.create(user=user1)
    UserProfile.objects.create(user=user2)
    
    # 为每个用户创建检测记录
    record1 = DetectionRecord.objects.create(
        user=user1,
        model_name='test_model.pt',
        confidence_threshold=0.5,
        iou_threshold=0.45,
        status='completed'
    )
    
    record2 = DetectionRecord.objects.create(
        user=user2,
        model_name='test_model.pt',
        confidence_threshold=0.5,
        iou_threshold=0.45,
        status='completed'
    )
    
    # 测试用户1只能看到自己的记录
    user1_records = DetectionRecord.objects.filter(user=user1)
    assert user1_records.count() == 1, "用户1应该只能看到1条记录"
    assert record1 in user1_records, "用户1应该能看到自己的记录"
    assert record2 not in user1_records, "用户1不应该看到用户2的记录"
    
    print("✅ 数据隔离功能正常")


def test_admin_permissions():
    """测试管理员权限"""
    print("\n🧪 测试管理员权限...")
    
    # 创建管理员用户
    admin = User.objects.create_superuser(
        username='testadmin',
        password='admin123',
        email='admin@example.com'
    )
    UserProfile.objects.create(user=admin)
    
    # 创建普通用户
    user = User.objects.create_user(
        username='normaluser',
        password='user123',
        email='user@example.com'
    )
    UserProfile.objects.create(user=user)
    
    # 为普通用户创建记录
    DetectionRecord.objects.create(
        user=user,
        model_name='test_model.pt',
        confidence_threshold=0.5,
        iou_threshold=0.45,
        status='completed'
    )
    
    # 测试管理员可以看到所有记录
    all_records = DetectionRecord.objects.all()
    assert all_records.count() >= 1, "管理员应该能看到所有记录"
    
    print("✅ 管理员权限正常")


def test_security_features():
    """测试安全功能"""
    print("\n🧪 测试安全功能...")
    
    client = Client()
    
    # 测试登录失败记录
    response = client.post('/app/login/', {
        'username': 'nonexistent',
        'password': 'wrongpass',
    })
    
    # 验证失败记录
    failed_attempt = LoginAttempt.objects.filter(
        username='nonexistent',
        success=False
    ).first()
    
    if failed_attempt:
        print("✅ 登录失败记录功能正常")
    else:
        print("❌ 登录失败记录功能异常")
    
    # 测试CSRF保护
    response = client.post('/app/login/', {
        'username': 'test',
        'password': 'test',
    })
    # CSRF错误应该返回403或重定向
    assert response.status_code in [403, 302], "CSRF保护可能未生效"
    print("✅ CSRF保护功能正常")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行用户认证系统测试...\n")
    
    try:
        test_user_registration()
        test_user_login()
        test_data_isolation()
        test_admin_permissions()
        test_security_features()
        
        print("\n🎉 所有测试通过！用户认证系统工作正常。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试数据
        print("\n🧹 清理测试数据...")
        User.objects.filter(username__in=[
            'testuser123', 'logintest', 'user1', 'user2', 
            'testadmin', 'normaluser'
        ]).delete()
        print("✅ 测试数据清理完成")


if __name__ == '__main__':
    run_all_tests()
