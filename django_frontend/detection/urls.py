"""
Detection应用URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # 主要页面
    path('', views.index, name='index'),
    path('upload/', views.upload_and_detect, name='upload_and_detect'),
    path('result/<int:record_id>/', views.detection_result, name='detection_result'),
    path('history/', views.history, name='history'),
    path('models/', views.model_management, name='model_management'),
    path('settings/', views.settings_view, name='settings'),
    
    # 操作
    path('delete/<int:record_id>/', views.delete_record, name='delete_record'),
    path('status/<int:record_id>/', views.get_detection_status, name='detection_status'),
]
