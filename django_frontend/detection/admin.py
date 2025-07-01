"""
Django管理后台配置
"""
from django.contrib import admin
from .models import DetectionRecord, ModelConfig, LLMAnalysisRecord


@admin.register(DetectionRecord)
class DetectionRecordAdmin(admin.ModelAdmin):
    """检测记录管理"""
    
    list_display = [
        'id', 
        'upload_time', 
        'model_name', 
        'total_detections',
        'with_mask_count',
        'without_mask_count', 
        'incorrect_mask_count',
        'processing_time',
        'status'
    ]
    list_filter = [
        'status', 
        'model_name', 
        'upload_time',
        'confidence_threshold'
    ]
    search_fields = ['id', 'model_name']
    readonly_fields = [
        'upload_time', 
        'processing_time', 
        'detection_details'
    ]
    list_per_page = 20
    
    fieldsets = (
        ('基本信息', {
            'fields': ('original_image', 'result_image', 'upload_time', 'status', 'error_message')
        }),
        ('检测参数', {
            'fields': ('model_name', 'confidence_threshold', 'iou_threshold', 'image_size')
        }),
        ('检测结果', {
            'fields': (
                'total_detections', 
                'with_mask_count', 
                'without_mask_count', 
                'incorrect_mask_count',
                'processing_time'
            )
        }),
        ('详细数据', {
            'fields': ('detection_details',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ModelConfig)
class ModelConfigAdmin(admin.ModelAdmin):
    """模型配置管理"""
    
    list_display = [
        'name', 
        'is_active', 
        'accuracy', 
        'inference_speed', 
        'model_size',
        'created_time'
    ]
    list_filter = ['is_active', 'created_time']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'file_path', 'description', 'is_active')
        }),
        ('性能参数', {
            'fields': ('accuracy', 'inference_speed', 'model_size')
        }),
    )


@admin.register(LLMAnalysisRecord)
class LLMAnalysisRecordAdmin(admin.ModelAdmin):
    """LLM分析记录管理"""

    list_display = (
        'id',
        'detection_record',
        'prompt_preview',
        'status',
        'api_provider',
        'model_name',
        'response_time',
        'created_time'
    )

    list_filter = (
        'status',
        'api_provider',
        'model_name',
        'created_time'
    )

    search_fields = (
        'user_prompt',
        'llm_response',
        'detection_record__id'
    )

    readonly_fields = (
        'created_time',
        'response_time',
        'token_usage'
    )

    list_per_page = 20

    fieldsets = (
        ('关联信息', {
            'fields': ('detection_record',)
        }),
        ('用户输入', {
            'fields': ('user_prompt',)
        }),
        ('LLM响应', {
            'fields': ('llm_response', 'status', 'error_message')
        }),
        ('API信息', {
            'fields': ('api_provider', 'model_name', 'response_time', 'token_usage')
        }),
        ('时间信息', {
            'fields': ('created_time',)
        }),
    )

    def prompt_preview(self, obj):
        """显示提示词预览"""
        return obj.prompt_preview
    prompt_preview.short_description = '提示词预览'
