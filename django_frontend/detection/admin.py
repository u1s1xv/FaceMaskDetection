"""
Django管理后台配置
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import DetectionRecord, ModelConfig, UserProfile, LoginAttempt


@admin.register(DetectionRecord)
class DetectionRecordAdmin(admin.ModelAdmin):
    """检测记录管理"""
    
    list_display = [
        'id',
        'user',
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
        'user',
        'model_name',
        'upload_time',
        'confidence_threshold'
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


# 重新注册User模型
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
