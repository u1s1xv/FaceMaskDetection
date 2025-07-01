"""
口罩检测应用的数据模型
"""
from django.db import models
from django.utils import timezone
import json


class DetectionRecord(models.Model):
    """检测记录模型"""
    
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
