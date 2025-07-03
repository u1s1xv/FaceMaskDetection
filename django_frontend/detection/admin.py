"""
Django管理后台配置
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import DetectionRecord, ModelConfig, UserProfile, LoginAttempt, BatchDetectionSession


@admin.register(DetectionRecord)
class DetectionRecordAdmin(admin.ModelAdmin):
    """检测记录管理"""
    
    list_display = [
        'id',
        'user',
        'upload_time',
        'model_name',
        'is_batch_detection',
        'batch_session',
        'batch_index',
        'total_detections',
        'with_mask_count',
        'without_mask_count',
        'incorrect_mask_count',
        'processing_time',
        'status'
    ]
    list_filter = [
        'status',
        'is_batch_detection',
        'user',
        'model_name',
        'upload_time',
        'confidence_threshold',
        'batch_session'
    ]
    search_fields = ['id', 'model_name', 'user__username']
    readonly_fields = [
        'upload_time', 
        'processing_time', 
        'detection_details'
    ]
    list_per_page = 20
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'original_image', 'result_image', 'upload_time', 'status', 'error_message')
        }),
        ('批量检测信息', {
            'fields': ('is_batch_detection', 'batch_session', 'batch_index'),
            'classes': ('collapse',)
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户配置管理"""

    list_display = [
        'user',
        'created_time',
        'last_login_ip',
        'login_count',
        'is_locked',
        'locked_until'
    ]
    list_filter = ['is_locked', 'created_time']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_time']
    list_editable = ['is_locked']

    fieldsets = (
        ('用户信息', {
            'fields': ('user', 'created_time')
        }),
        ('登录信息', {
            'fields': ('last_login_ip', 'login_count')
        }),
        ('安全设置', {
            'fields': ('is_locked', 'locked_until')
        }),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """登录尝试管理"""

    list_display = [
        'username',
        'ip_address',
        'success',
        'attempt_time',
        'user_agent_short'
    ]
    list_filter = ['success', 'attempt_time']
    search_fields = ['username', 'ip_address']
    readonly_fields = ['attempt_time']
    date_hierarchy = 'attempt_time'

    def user_agent_short(self, obj):
        """显示简短的用户代理信息"""
        if obj.user_agent:
            return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
        return '未知'
    user_agent_short.short_description = '用户代理'

    fieldsets = (
        ('登录信息', {
            'fields': ('username', 'ip_address', 'success', 'attempt_time')
        }),
        ('详细信息', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
    )


# 扩展用户管理
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户配置'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


@admin.register(BatchDetectionSession)
class BatchDetectionSessionAdmin(admin.ModelAdmin):
    """批量检测会话管理"""

    list_display = [
        'id',
        'session_name',
        'user',
        'total_images',
        'completed_images',
        'failed_images',
        'progress_percentage',
        'status',
        'created_time'
    ]
    list_filter = [
        'status',
        'user',
        'created_time',
        'model_name'
    ]
    search_fields = ['session_name', 'user__username']
    readonly_fields = [
        'created_time',
        'updated_time',
        'start_time',
        'end_time',
        'total_processing_time',
        'progress_percentage',
        'success_rate'
    ]
    list_per_page = 20

    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'session_name', 'created_time', 'updated_time', 'status', 'error_message')
        }),
        ('统计信息', {
            'fields': ('total_images', 'completed_images', 'failed_images', 'progress_percentage', 'success_rate')
        }),
        ('检测参数', {
            'fields': ('model_name', 'confidence_threshold', 'iou_threshold', 'image_size')
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time', 'total_processing_time'),
            'classes': ('collapse',)
        }),
    )

    def progress_percentage(self, obj):
        """显示进度百分比"""
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = '进度'

    def success_rate(self, obj):
        """显示成功率"""
        return f"{obj.success_rate}%"
    success_rate.short_description = '成功率'


class DetectionRecordInline(admin.TabularInline):
    """检测记录内联显示"""
    model = DetectionRecord
    extra = 0
    readonly_fields = ['upload_time', 'status', 'total_detections', 'processing_time']
    fields = ['batch_index', 'original_image', 'status', 'total_detections', 'processing_time']

    def has_add_permission(self, request, obj=None):
        return False


# 将内联添加到BatchDetectionSessionAdmin
BatchDetectionSessionAdmin.inlines = [DetectionRecordInline]


# 重新注册User模型
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
