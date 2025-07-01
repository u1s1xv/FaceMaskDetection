#!/usr/bin/env python
"""
Django项目测试脚本
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')

try:
    django.setup()
    print("✓ Django环境初始化成功")
except Exception as e:
    print(f"❌ Django环境初始化失败: {e}")
    sys.exit(1)

def test_imports():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        from django.conf import settings
        print("✓ Django settings导入成功")
        
        from detection.models import DetectionRecord, ModelConfig
        print("✓ 检测模型导入成功")
        
        from detection.forms import ImageUploadForm
        print("✓ 表单类导入成功")
        
        from detection.views import index, upload_and_detect
        print("✓ 视图函数导入成功")
        
        from detection.services import YOLOInferenceService
        print("✓ YOLO服务导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_settings():
    """测试Django设置"""
    print("\n=== 测试Django设置 ===")
    
    try:
        from django.conf import settings
        
        # 检查基本设置
        print(f"✓ SECRET_KEY: {'已设置' if settings.SECRET_KEY else '未设置'}")
        print(f"✓ DEBUG: {settings.DEBUG}")
        print(f"✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # 检查应用配置
        required_apps = ['detection', 'corsheaders']
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                print(f"✓ 应用 {app} 已安装")
            else:
                print(f"❌ 应用 {app} 未安装")
        
        # 检查路径配置
        print(f"✓ MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"✓ STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"✓ YOLO_SERVER_ROOT: {settings.YOLO_SERVER_ROOT}")
        
        return True
    except Exception as e:
        print(f"❌ 设置检查失败: {e}")
        return False

def test_database():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    
    try:
        from django.db import connection
        
        # 测试数据库连接
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✓ 数据库连接成功")
            else:
                print("❌ 数据库连接异常")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_urls():
    """测试URL配置"""
    print("\n=== 测试URL配置 ===")
    
    try:
        from django.urls import reverse
        
        # 测试主要URL
        urls_to_test = [
            'index',
            'history',
            'upload_and_detect',
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✓ URL {url_name}: {url}")
            except Exception as e:
                print(f"❌ URL {url_name} 配置错误: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ URL测试失败: {e}")
        return False

def test_models():
    """测试数据模型"""
    print("\n=== 测试数据模型 ===")
    
    try:
        from detection.models import DetectionRecord, ModelConfig
        
        # 测试模型字段
        record_fields = [f.name for f in DetectionRecord._meta.fields]
        required_fields = ['original_image', 'model_name', 'confidence_threshold', 'status']
        
        for field in required_fields:
            if field in record_fields:
                print(f"✓ DetectionRecord.{field} 字段存在")
            else:
                print(f"❌ DetectionRecord.{field} 字段缺失")
                return False
        
        # 测试模型方法
        if hasattr(DetectionRecord, 'detection_summary'):
            print("✓ DetectionRecord.detection_summary 方法存在")
        else:
            print("❌ DetectionRecord.detection_summary 方法缺失")
        
        return True
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False

def test_yolo_integration():
    """测试YOLO集成"""
    print("\n=== 测试YOLO集成 ===")
    
    try:
        from detection.services import YOLOInferenceService
        from django.conf import settings
        
        # 检查YOLO路径
        yolo_root = settings.YOLO_SERVER_ROOT
        if yolo_root.exists():
            print(f"✓ YOLO服务器根目录存在: {yolo_root}")
        else:
            print(f"⚠️  YOLO服务器根目录不存在: {yolo_root}")
        
        # 检查推理脚本
        infer_script = settings.YOLO_SCRIPTS_DIR / 'yolo_infer.py'
        if infer_script.exists():
            print(f"✓ YOLO推理脚本存在: {infer_script}")
        else:
            print(f"⚠️  YOLO推理脚本不存在: {infer_script}")
        
        # 测试服务初始化
        try:
            service = YOLOInferenceService()
            print("✓ YOLO推理服务初始化成功")
        except Exception as e:
            print(f"⚠️  YOLO推理服务初始化失败: {e}")
        
        return True
    except Exception as e:
        print(f"❌ YOLO集成测试失败: {e}")
        return False

def create_directories():
    """创建必要目录"""
    print("\n=== 创建必要目录 ===")
    
    directories = [
        project_root / 'media',
        project_root / 'media' / 'uploads',
        project_root / 'media' / 'uploads' / 'original',
        project_root / 'media' / 'uploads' / 'results',
        project_root / 'static',
        project_root / 'staticfiles',
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ 目录创建成功: {directory.name}")
        except Exception as e:
            print(f"❌ 目录创建失败 {directory}: {e}")

def main():
    """主测试函数"""
    print("🧪 Django项目配置测试")
    print("=" * 50)
    
    # 创建目录
    create_directories()
    
    # 运行测试
    tests = [
        test_imports,
        test_settings,
        test_database,
        test_urls,
        test_models,
        test_yolo_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目配置正确。")
        print("\n📋 下一步:")
        print("1. 运行 python manage.py makemigrations")
        print("2. 运行 python manage.py migrate")
        print("3. 运行 python manage.py runserver")
    else:
        print("⚠️  部分测试失败，请检查配置。")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
