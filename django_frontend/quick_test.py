#!/usr/bin/env python
"""
快速测试脚本
"""
import sys
from pathlib import Path

print("🔍 快速环境检查")
print("=" * 30)

# 检查Python版本
print(f"Python版本: {sys.version}")

# 检查当前目录
current_dir = Path.cwd()
print(f"当前目录: {current_dir}")

# 检查项目文件
project_files = [
    'manage.py',
    'face_mask_detection/settings.py',
    'detection/models.py',
    'requirements.txt'
]

print("\n📁 项目文件检查:")
for file_path in project_files:
    file_obj = Path(file_path)
    if file_obj.exists():
        print(f"✓ {file_path}")
    else:
        print(f"❌ {file_path}")

# 检查Python包
print("\n📦 Python包检查:")
packages = ['django', 'PIL', 'cv2', 'numpy']

for package in packages:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError:
        print(f"❌ {package}")

# 检查Django
try:
    import django
    print(f"\n🎯 Django版本: {django.get_version()}")
    
    # 设置Django环境
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')
    django.setup()
    print("✓ Django环境设置成功")
    
    # 测试设置导入
    from django.conf import settings
    print(f"✓ 设置导入成功")
    print(f"  DEBUG: {settings.DEBUG}")
    print(f"  YOLO_SERVER_ROOT: {settings.YOLO_SERVER_ROOT}")
    
except Exception as e:
    print(f"❌ Django测试失败: {e}")

print("\n✅ 快速检查完成")
