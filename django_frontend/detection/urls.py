"""
Detection应用URL配置
"""
from django.urls import path
from . import views, auth_views

urlpatterns = [
    # 认证相关
    path('welcome/', auth_views.welcome_view, name='welcome'),
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),

    # 主要页面（需要登录）
    path('', views.index, name='index'),
    path('detect/', views.detect, name='detect'),
    path('upload/', views.upload_and_detect, name='upload_and_detect'),
    path('result/<int:record_id>/', views.detection_result, name='detection_result'),
    path('history/', views.history, name='history'),
    path('models/', views.model_management, name='model_management'),
    path('settings/', views.settings_view, name='settings_view'),

    # 操作
    path('delete/<int:record_id>/', views.delete_record, name='delete_record'),
    path('status/<int:record_id>/', views.get_detection_status, name='detection_status'),

    # 调试
    path('debug-form/', views.debug_form, name='debug_form'),
]
