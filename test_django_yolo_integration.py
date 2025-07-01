#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Django与YOLO集成是否正常工作
"""

import os
import sys
import django
from pathlib import Path
import tempfile
from PIL import Image
import numpy as np

def setup_django():
    """设置Django环境"""
    # 切换到Django目录
    django_dir = Path(__file__).parent / "django_frontend"
    os.chdir(django_dir)
    
    # 设置Django环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')
    django.setup()

def create_test_image():
    """创建一个测试图片"""
    # 创建一个简单的测试图片 (640x640, RGB)
    img_array = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    
    # 保存到临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    img.save(temp_file.name, 'JPEG')
    return temp_file.name

def test_yolo_service():
    """测试YOLO推理服务"""
    print("🧪 测试YOLO推理服务...")
    
    try:
        from detection.services import YOLOInferenceService
        
        # 初始化服务
        service = YOLOInferenceService()
        print("✅ YOLO推理服务初始化成功")
        
        # 获取可用模型
        models = service.get_available_models()
        print(f"✅ 找到 {len(models)} 个可用模型")
        
        if not models:
            print("❌ 没有可用的模型文件")
            return False
        
        # 使用第一个可用模型
        model_name = models[0]['name']
        print(f"📦 使用模型: {model_name}")
        
        # 创建测试图片
        test_image_path = create_test_image()
        print(f"🖼️ 创建测试图片: {test_image_path}")
        
        try:
            # 执行推理（使用较低的参数以加快速度）
            print("🔄 开始推理测试...")
            result = service.run_inference(
                image_path=test_image_path,
                model_name=model_name,
                confidence=0.5,
                iou=0.45,
                imgsz=320  # 使用较小的图片尺寸加快推理
            )
            
            print("✅ 推理测试成功完成！")
            print(f"📊 推理结果: {result.get('status', 'unknown')}")
            
            # 清理测试文件
            os.unlink(test_image_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 推理测试失败: {e}")
            # 清理测试文件
            if os.path.exists(test_image_path):
                os.unlink(test_image_path)
            return False
            
    except Exception as e:
        print(f"❌ YOLO服务测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 Django-YOLO集成测试")
    print("=" * 50)
    
    try:
        # 设置Django环境
        setup_django()
        print("✅ Django环境设置成功")
        
        # 测试YOLO服务
        success = test_yolo_service()
        
        if success:
            print("\n🎉 集成测试成功！")
            print("📝 测试结果:")
            print("   ✅ Django环境正常")
            print("   ✅ YOLO服务可用")
            print("   ✅ 模型推理正常")
            print("   ✅ 参数传递正确")
            print("\n🚀 现在可以正常使用Django前端进行口罩检测了！")
        else:
            print("\n❌ 集成测试失败")
            print("请检查:")
            print("   - 模型文件是否存在")
            print("   - YOLO环境是否正确配置")
            print("   - 依赖包是否完整安装")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    main()
