"""
口罩检测应用的数据模型
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class BatchDetectionSession(models.Model):
    """批量检测会话模型"""

    # 状态选择
    STATUS_CHOICES = [
        ('pending', '等待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('partial_completed', '部分完成'),
        ('failed', '处理失败'),
        ('cancelled', '已取消'),
    ]

    # 基本信息
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="用户",
        help_text="批量检测会话所属用户"
    )
    session_name = models.CharField(
        max_length=200,
        verbose_name="会话名称",
        help_text="批量检测会话的名称"
    )
    created_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_time = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    # 统计信息
    total_images = models.IntegerField(
        default=0,
        verbose_name="总图片数量"
    )
    completed_images = models.IntegerField(
        default=0,
        verbose_name="已完成图片数量"
    )
    failed_images = models.IntegerField(
        default=0,
        verbose_name="失败图片数量"
    )

    # 状态信息
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="处理状态"
    )

    # 统一的检测参数
    model_name = models.CharField(
        max_length=100,
        default="yolo11n-seg.pt",
        verbose_name="使用的模型"
    )
    confidence_threshold = models.FloatField(
        default=0.25,
        verbose_name="置信度阈值"
    )
    iou_threshold = models.FloatField(
        default=0.45,
        verbose_name="IOU阈值"
    )
    image_size = models.IntegerField(
        default=640,
        verbose_name="图像尺寸"
    )

    # 处理时间统计
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="开始处理时间"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="结束处理时间"
    )
    total_processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name="总处理时间(秒)"
    )

    # 错误信息
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="错误信息"
    )

    class Meta:
        verbose_name = "批量检测会话"
        verbose_name_plural = "批量检测会话"
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['user', '-created_time']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.session_name} - {self.user.username} ({self.get_status_display()})"

    @property
    def progress_percentage(self):
        """获取进度百分比"""
        if self.total_images == 0:
            return 0
        return round((self.completed_images + self.failed_images) / self.total_images * 100, 2)

    @property
    def success_rate(self):
        """获取成功率"""
        if self.total_images == 0:
            return 0
        return round(self.completed_images / self.total_images * 100, 2)

    @property
    def is_completed(self):
        """检查是否已完成"""
        return self.status in ['completed', 'partial_completed', 'failed', 'cancelled']

    @property
    def batch_summary(self):
        """获取批量检测摘要"""
        # 计算总的检测统计
        records = self.detectionrecord_set.filter(status='completed')
        total_detections = sum(record.total_detections for record in records)
        total_with_mask = sum(record.with_mask_count for record in records)
        total_without_mask = sum(record.without_mask_count for record in records)
        total_incorrect_mask = sum(record.incorrect_mask_count for record in records)

        return {
            'total_images': self.total_images,
            'completed_images': self.completed_images,
            'failed_images': self.failed_images,
            'total_detections': total_detections,
            'with_mask_count': total_with_mask,
            'without_mask_count': total_without_mask,
            'incorrect_mask_count': total_incorrect_mask,
            'compliance_rate': round(
                (total_with_mask / total_detections * 100)
                if total_detections > 0 else 0, 2
            ),
            'progress_percentage': self.progress_percentage,
            'success_rate': self.success_rate
        }


class DetectionRecord(models.Model):
    """检测记录模型"""

    # 用户关联
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="用户",
        help_text="检测记录所属用户"
    )

    # 批量检测关联
    batch_session = models.ForeignKey(
        BatchDetectionSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="批量检测会话",
        help_text="所属的批量检测会话，单张检测时为空"
    )
    batch_index = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="批次内序号",
        help_text="在批量检测会话中的序号"
    )
    is_batch_detection = models.BooleanField(
        default=False,
        verbose_name="是否为批量检测",
        help_text="标识是否为批量检测的一部分"
    )

    # 基本信息
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")
    original_image = models.ImageField(
        upload_to='uploads/original/%Y/%m/%d/', 
        verbose_name="原始图片"
    )
    result_image = models.ImageField(
        upload_to='uploads/results/%Y/%m/%d/', 
        verbose_name="检测结果图片",
        blank=True,
        null=True
    )
    
    # 检测参数
    model_name = models.CharField(
        max_length=100, 
        default="yolo11n-seg.pt",
        verbose_name="使用的模型"
    )
    confidence_threshold = models.FloatField(
        default=0.25, 
        verbose_name="置信度阈值"
    )
    iou_threshold = models.FloatField(
        default=0.45, 
        verbose_name="IOU阈值"
    )
    image_size = models.IntegerField(
        default=640, 
        verbose_name="图像尺寸"
    )
    
    # 检测结果统计
    total_detections = models.IntegerField(
        default=0, 
        verbose_name="总检测数量"
    )
    with_mask_count = models.IntegerField(
        default=0, 
        verbose_name="正确戴口罩数量"
    )
    without_mask_count = models.IntegerField(
        default=0, 
        verbose_name="未戴口罩数量"
    )
    incorrect_mask_count = models.IntegerField(
        default=0, 
        verbose_name="错误戴口罩数量"
    )
    
    # 详细结果和性能信息
    detection_details = models.JSONField(
        default=dict, 
        verbose_name="检测详细结果",
        help_text="包含每个检测框的坐标、置信度等详细信息"
    )
    processing_time = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="处理时间(秒)"
    )
    
    # 状态字段
    STATUS_CHOICES = [
        ('pending', '等待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '处理失败'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="处理状态"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="错误信息"
    )
    
    class Meta:
        verbose_name = "检测记录"
        verbose_name_plural = "检测记录"
        ordering = ['-upload_time']
        indexes = [
            models.Index(fields=['user', '-upload_time']),
            models.Index(fields=['batch_session', 'batch_index']),
            models.Index(fields=['status']),
            models.Index(fields=['is_batch_detection']),
        ]
    
    def __str__(self):
        return f"检测记录 {self.id} - {self.upload_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def detection_summary(self):
        """获取检测结果摘要"""
        return {
            'total': self.total_detections,
            'with_mask': self.with_mask_count,
            'without_mask': self.without_mask_count,
            'incorrect_mask': self.incorrect_mask_count,
            'compliance_rate': round(
                (self.with_mask_count / self.total_detections * 100) 
                if self.total_detections > 0 else 0, 2
            )
        }
    
    def get_detection_details_json(self):
        """获取格式化的检测详情"""
        if isinstance(self.detection_details, str):
            try:
                return json.loads(self.detection_details)
            except json.JSONDecodeError:
                return {}
        return self.detection_details or {}

    @property
    def is_single_detection(self):
        """检查是否为单张检测"""
        return not self.is_batch_detection

    @property
    def batch_info(self):
        """获取批量检测信息"""
        if not self.is_batch_detection or not self.batch_session:
            return None

        return {
            'session_id': self.batch_session.id,
            'session_name': self.batch_session.session_name,
            'batch_index': self.batch_index,
            'total_images': self.batch_session.total_images,
            'session_status': self.batch_session.status
        }

    @property
    def filename(self):
        """获取原始文件名"""
        if self.original_image:
            return self.original_image.name.split('/')[-1]
        return "未知文件"

    @property
    def detection_summary(self):
        """获取检测结果摘要"""
        if self.total_detections == 0:
            return {
                'compliance_rate': 0,
                'risk_level': 'unknown'
            }

        compliance_rate = round((self.with_mask_count / self.total_detections) * 100, 2)

        # 风险等级评估
        if compliance_rate >= 90:
            risk_level = 'low'
        elif compliance_rate >= 70:
            risk_level = 'medium'
        else:
            risk_level = 'high'

        return {
            'compliance_rate': compliance_rate,
            'risk_level': risk_level
        }


class ModelConfig(models.Model):
    """模型配置模型"""
    
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="模型名称"
    )
    file_path = models.CharField(
        max_length=255, 
        verbose_name="模型文件路径"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="模型描述"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="是否启用"
    )
    created_time = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="创建时间"
    )
    
    # 模型性能参数
    accuracy = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="准确率"
    )
    inference_speed = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="推理速度(ms)"
    )
    model_size = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="模型大小(MB)"
    )
    
    class Meta:
        verbose_name = "模型配置"
        verbose_name_plural = "模型配置"
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.name} ({'启用' if self.is_active else '禁用'})"


class UserProfile(models.Model):
    """用户配置模型"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    created_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="最后登录IP"
    )
    login_count = models.IntegerField(
        default=0,
        verbose_name="登录次数"
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name="账户是否锁定"
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="锁定到期时间"
    )

    class Meta:
        verbose_name = "用户配置"
        verbose_name_plural = "用户配置"
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.user.username} 的配置"

    def is_account_locked(self):
        """检查账户是否被锁定"""
        if not self.is_locked:
            return False
        if self.locked_until and timezone.now() > self.locked_until:
            # 锁定时间已过，自动解锁
            self.is_locked = False
            self.locked_until = None
            self.save()
            return False
        return True


class LoginAttempt(models.Model):
    """登录尝试记录模型"""

    username = models.CharField(
        max_length=150,
        verbose_name="用户名"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP地址"
    )
    success = models.BooleanField(
        default=False,
        verbose_name="是否成功"
    )
    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="尝试时间"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="用户代理"
    )

    class Meta:
        verbose_name = "登录尝试"
        verbose_name_plural = "登录尝试"
        ordering = ['-attempt_time']
        indexes = [
            models.Index(fields=['username', 'ip_address', 'attempt_time']),
            models.Index(fields=['success', 'attempt_time']),
        ]

    def __str__(self):
        status = "成功" if self.success else "失败"
        return f"{self.username} - {status} - {self.attempt_time}"
