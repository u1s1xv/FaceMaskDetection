"""
Django管理后台配置
"""
from django.contrib import admin
from .models import DetectionRecord, ModelConfig


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
