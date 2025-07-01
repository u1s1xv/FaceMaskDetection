#!/usr/bin/env python
"""
测试模型选择功能
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')

try:
    django.setup()
    print("✓ Django环境初始化成功")
except Exception as e:
    print(f"❌ Django环境初始化失败: {e}")
    sys.exit(1)

def test_model_directory():
    """测试模型目录"""
    print("\n=== 测试模型目录 ===")
    
    from django.conf import settings
    
    models_dir = settings.YOLO_MODELS_DIR
    print(f"模型目录: {models_dir}")
    
    if models_dir.exists():
        print("✓ 模型目录存在")
        
        # 列出所有.pt文件
        pt_files = list(models_dir.glob('*.pt'))
        print(f"找到 {len(pt_files)} 个模型文件:")
        
        for pt_file in pt_files:
            size_mb = pt_file.stat().st_size / (1024 * 1024)
            print(f"  - {pt_file.name} ({size_mb:.1f} MB)")
        
        return pt_files
    else:
        print(f"❌ 模型目录不存在: {models_dir}")
        return []

def test_yolo_service():
    """测试YOLO服务"""
    print("\n=== 测试YOLO服务 ===")
    
    try:
        from detection.services import YOLOInferenceService
        
        service = YOLOInferenceService()
        print("✓ YOLO服务初始化成功")
        
        models = service.get_available_models()
        print(f"✓ 获取到 {len(models)} 个可用模型:")
        
        for model in models:
            print(f"  - {model['name']}: {model['description']} ({model['size']} MB)")
        
        return models
    except Exception as e:
        print(f"❌ YOLO服务测试失败: {e}")
        return []

def test_form_choices():
    """测试表单选择"""
    print("\n=== 测试表单选择 ===")
    
    try:
        from detection.forms import ImageUploadForm, DetectionParametersForm
        
        # 测试ImageUploadForm
        upload_form = ImageUploadForm()
        model_choices = upload_form.fields['model_name'].widget.choices
        print(f"✓ ImageUploadForm 模型选择数量: {len(model_choices)}")
        
        for choice in model_choices:
            print(f"  - {choice[0]}: {choice[1]}")
        
        # 测试DetectionParametersForm
        params_form = DetectionParametersForm()
        param_choices = params_form.fields['model_name'].choices
        print(f"✓ DetectionParametersForm 模型选择数量: {len(param_choices)}")
        
        return model_choices
    except Exception as e:
        print(f"❌ 表单测试失败: {e}")
        return []

def test_api_models():
    """测试API模型获取"""
    print("\n=== 测试API模型获取 ===")
    
    try:
        from detection.api_views import api_get_models
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/api/models/')
        
        response = api_get_models(request)
        print(f"✓ API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            import json
            data = json.loads(response.content)
            models = data.get('available_models', [])
            print(f"✓ API返回 {len(models)} 个模型")
            
            for model in models:
                print(f"  - {model['name']}: {model.get('description', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def create_test_model_file():
    """创建测试模型文件"""
    print("\n=== 创建测试模型文件 ===")
    
    from django.conf import settings
    
    models_dir = settings.YOLO_MODELS_DIR
    
    # 确保目录存在
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一个空的测试文件
    test_model = models_dir / 'test_yolo11n.pt'
    
    if not test_model.exists():
        test_model.write_text("# 这是一个测试模型文件")
        print(f"✓ 创建测试模型文件: {test_model}")
    else:
        print(f"✓ 测试模型文件已存在: {test_model}")
    
    return test_model

def main():
    """主测试函数"""
    print("🧪 模型选择功能测试")
    print("=" * 50)
    
    # 测试模型目录
    pt_files = test_model_directory()
    
    # 如果没有模型文件，创建一个测试文件
    if not pt_files:
        print("\n⚠️  没有找到模型文件，创建测试文件...")
        create_test_model_file()
        pt_files = test_model_directory()
    
    # 测试YOLO服务
    models = test_yolo_service()
    
    # 测试表单选择
    choices = test_form_choices()
    
    # 测试API
    api_success = test_api_models()
    
    # 总结
    print("\n📊 测试总结:")
    print(f"  - 模型文件数量: {len(pt_files)}")
    print(f"  - YOLO服务模型: {len(models)}")
    print(f"  - 表单选择项: {len(choices)}")
    print(f"  - API测试: {'成功' if api_success else '失败'}")
    
    if pt_files and models and choices and api_success:
        print("\n🎉 所有测试通过！模型选择功能正常工作。")
        
        print("\n📋 使用说明:")
        print("1. 将训练好的.pt模型文件放入 yoloserver/models/checkpoints/ 目录")
        print("2. 刷新Django页面，模型会自动出现在下拉菜单中")
        print("3. 只有实际存在的模型文件才能被选择")
        print("4. 可以在模型管理页面查看所有模型状态")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

if __name__ == '__main__':
    main()
