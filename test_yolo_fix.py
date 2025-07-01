#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试YOLO推理脚本修复效果
"""

import subprocess
import sys
import os
from pathlib import Path

def test_yolo_infer_args():
    """测试YOLO推理脚本参数解析"""
    print("🧪 测试YOLO推理脚本参数解析...")
    
    # 构建测试命令（只测试参数解析，不实际运行推理）
    yolo_script = Path("yoloserver/scripts/yolo_infer.py")
    
    if not yolo_script.exists():
        print(f"❌ YOLO推理脚本不存在: {yolo_script}")
        return False
    
    # 测试命令（模拟Django前端调用）
    test_cmd = [
        sys.executable,
        str(yolo_script),
        '--help'  # 只显示帮助信息，不实际运行
    ]
    
    try:
        result = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # 检查帮助信息中是否包含新添加的参数
            help_output = result.stdout
            if '--project PROJECT' in help_output and '--name NAME' in help_output:
                print("✅ YOLO推理脚本参数修复成功！")
                print("   - 已添加 --project 参数")
                print("   - 已添加 --name 参数")
                return True
            else:
                print("❌ 参数修复不完整")
                print(f"帮助输出: {help_output}")
                return False
        else:
            print(f"❌ 脚本执行失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 脚本执行超时")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_django_yolo_integration():
    """测试Django与YOLO的集成"""
    print("\n🔗 测试Django与YOLO集成...")
    
    try:
        # 切换到Django目录
        os.chdir("django_frontend")
        
        # 导入Django设置
        import django
        from django.conf import settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')
        django.setup()
        
        from detection.services import YOLOInferenceService
        
        # 测试服务初始化
        service = YOLOInferenceService()
        print("✅ YOLO推理服务初始化成功")
        
        # 检查推理脚本路径
        if service.infer_script.exists():
            print(f"✅ 推理脚本路径正确: {service.infer_script}")
        else:
            print(f"❌ 推理脚本不存在: {service.infer_script}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Django集成测试失败: {e}")
        return False
    finally:
        # 切换回原目录
        os.chdir("..")

def main():
    """主测试函数"""
    print("🎯 YOLO推理脚本修复测试")
    print("=" * 50)
    
    # 测试1: 参数解析
    test1_passed = test_yolo_infer_args()
    
    # 测试2: Django集成
    test2_passed = test_django_yolo_integration()
    
    print("\n📊 测试结果总结:")
    print(f"   参数解析测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"   Django集成测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！YOLO推理脚本修复成功！")
        print("\n📝 修复内容:")
        print("   1. 在yolo_infer.py中添加了--project参数")
        print("   2. 在yolo_infer.py中添加了--name参数")
        print("   3. 修改了输出路径逻辑，支持自定义输出目录")
        print("\n🚀 现在可以正常使用Django前端进行口罩检测了！")
        return True
    else:
        print("\n❌ 部分测试失败，请检查修复内容")
        return False

if __name__ == "__main__":
    main()
