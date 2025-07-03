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
    path('clear-cache/', api_views.api_clear_cache, name='api_clear_cache'),
    # 推理缓存管理API
    path('clear-inference-cache/', api_views.api_clear_inference_cache, name='api_clear_inference_cache'),
    path('cache-stats/', api_views.api_get_cache_stats, name='api_get_cache_stats'),
    # 批量检测API
    path('batch-detect/', api_views.api_batch_upload_detect, name='api_batch_upload_detect'),
    path('batch-progress/<int:session_id>/', api_views.api_batch_progress, name='api_batch_progress'),
    path('batch-session/<int:session_id>/delete/', api_views.api_delete_batch_session, name='api_delete_batch_session'),
    # 大模型API
    path('llm-models/', api_views.api_get_llm_models, name='api_get_llm_models'),
    path('llm-analysis/', api_views.api_llm_analysis, name='api_llm_analysis'),
    path('llm-analysis-stream/', api_views.api_llm_analysis_stream, name='api_llm_analysis_stream'),
    path('llm-pdf-download/', api_views.api_download_llm_pdf, name='api_download_llm_pdf'),
]
