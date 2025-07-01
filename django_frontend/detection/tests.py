"""
测试用例
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from PIL import Image
import io
import json

from .models import DetectionRecord, ModelConfig


class DetectionModelTest(TestCase):
    """检测模型测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.model_config = ModelConfig.objects.create(
            name='test_model.pt',
            file_path='test_model.pt',
            description='测试模型',
            is_active=True
        )
    
    def test_detection_record_creation(self):
        """测试检测记录创建"""
        # 创建测试图片
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_file = SimpleUploadedFile(
            "test.jpg", 
            image_io.getvalue(), 
            content_type="image/jpeg"
        )
        
        record = DetectionRecord.objects.create(
            original_image=image_file,
            model_name='test_model.pt',
            confidence_threshold=0.25,
            iou_threshold=0.45,
            image_size=640
        )
        
        self.assertEqual(record.model_name, 'test_model.pt')
        self.assertEqual(record.confidence_threshold, 0.25)
        self.assertEqual(record.status, 'pending')
    
    def test_detection_summary(self):
        """测试检测摘要"""
        record = DetectionRecord.objects.create(
            model_name='test_model.pt',
            total_detections=10,
            with_mask_count=7,
            without_mask_count=2,
            incorrect_mask_count=1
        )
        
        summary = record.detection_summary
        self.assertEqual(summary['total'], 10)
        self.assertEqual(summary['with_mask'], 7)
        self.assertEqual(summary['compliance_rate'], 70.0)


class DetectionViewTest(TestCase):
    """检测视图测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # 创建测试模型配置
        ModelConfig.objects.create(
            name='test_model.pt',
            file_path='test_model.pt',
            description='测试模型',
            is_active=True
        )
    
    def test_index_view(self):
        """测试主页视图"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '口罩检测系统')
        self.assertContains(response, '上传图片进行口罩检测')
    
    def test_history_view(self):
        """测试历史记录视图"""
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '检测历史')
    
    def test_upload_form_validation(self):
        """测试上传表单验证"""
        # 测试无文件上传
        response = self.client.post(reverse('upload_and_detect'), {
            'model_name': 'test_model.pt',
            'confidence_threshold': 0.25,
            'iou_threshold': 0.45,
            'image_size': 640
        })
        
        # 应该重定向回主页（因为表单验证失败）
        self.assertEqual(response.status_code, 302)
    
    def test_detection_result_view(self):
        """测试检测结果视图"""
        # 创建测试记录
        record = DetectionRecord.objects.create(
            model_name='test_model.pt',
            status='completed',
            total_detections=5,
            with_mask_count=3,
            without_mask_count=2
        )
        
        response = self.client.get(reverse('detection_result', args=[record.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'检测结果 #{record.id}')


class DetectionAPITest(TestCase):
    """检测API测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.client = Client()
        
        # 创建测试模型配置
        ModelConfig.objects.create(
            name='test_model.pt',
            file_path='test_model.pt',
            description='测试模型',
            is_active=True
        )
    
    def test_api_get_models(self):
        """测试获取模型列表API"""
        response = self.client.get('/api/models/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('database_models', data)
        self.assertIn('file_models', data)
    
    def test_api_get_history(self):
        """测试获取历史记录API"""
        # 创建测试记录
        DetectionRecord.objects.create(
            model_name='test_model.pt',
            status='completed',
            total_detections=3
        )
        
        response = self.client.get('/api/history/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
    
    def test_api_get_result(self):
        """测试获取检测结果API"""
        record = DetectionRecord.objects.create(
            model_name='test_model.pt',
            status='completed',
            total_detections=5,
            with_mask_count=3,
            without_mask_count=2
        )
        
        response = self.client.get(f'/api/result/{record.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['id'], record.id)
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['total_detections'], 5)


class DetectionFormTest(TestCase):
    """检测表单测试"""
    
    def setUp(self):
        """设置测试环境"""
        ModelConfig.objects.create(
            name='test_model.pt',
            file_path='test_model.pt',
            description='测试模型',
            is_active=True
        )
    
    def test_image_upload_form_valid(self):
        """测试有效的图片上传表单"""
        from .forms import ImageUploadForm
        
        # 创建测试图片
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_file = SimpleUploadedFile(
            "test.jpg", 
            image_io.getvalue(), 
            content_type="image/jpeg"
        )
        
        form_data = {
            'model_name': 'test_model.pt',
            'confidence_threshold': 0.25,
            'iou_threshold': 0.45,
            'image_size': 640
        }
        
        form = ImageUploadForm(data=form_data, files={'original_image': image_file})
        self.assertTrue(form.is_valid())
    
    def test_image_upload_form_invalid_confidence(self):
        """测试无效置信度的表单"""
        from .forms import ImageUploadForm
        
        form_data = {
            'model_name': 'test_model.pt',
            'confidence_threshold': 1.5,  # 无效值
            'iou_threshold': 0.45,
            'image_size': 640
        }
        
        form = ImageUploadForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confidence_threshold', form.errors)
