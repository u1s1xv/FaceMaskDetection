"""
Detection应用API URL配置
"""
from django.urls import path
from . import api_views

urlpatterns = [
    # API端点
    path('detect/', api_views.api_upload_detect, name='api_upload_detect'),
    path('result/<int:record_id>/', api_views.api_get_result, name='api_get_result'),
    path('models/', api_views.api_get_models, name='api_get_models'),
    path('history/', api_views.api_get_history, name='api_get_history'),
    path('delete/<int:record_id>/', api_views.api_delete_record, name='api_delete_record'),
]
