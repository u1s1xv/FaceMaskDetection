#!/usr/bin/env python
"""
Django项目初始化脚本
"""
import os
import sys
import django
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')

# 初始化Django
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth.models import User
from detection.models import ModelConfig


def create_directories():
    """创建必要的目录"""
    directories = [
        project_root / 'media',
        project_root / 'media' / 'uploads',
        project_root / 'media' / 'uploads' / 'original',
        project_root / 'media' / 'uploads' / 'results',
        project_root / 'static',
        project_root / 'staticfiles',
        project_root / 'logs',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {directory}")


def run_migrations():
    """运行数据库迁移"""
    print("\n=== 运行数据库迁移 ===")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    print("数据库迁移完成")


def create_superuser():
    """创建超级用户"""
    print("\n=== 创建超级用户 ===")
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("超级用户创建成功")
        print("  用户名: admin")
        print("  密码: admin123")
    else:
        print("超级用户已存在")


# def create_default_models():
#     """创建默认模型配置"""
#     print("\n=== 创建默认模型配置 ===")
    
#     default_models = [
#         {
#             'name': 'yolo11n-seg.pt',
#             'file_path': 'yolo11n-seg.pt',
#             'description': 'YOLO11 Nano分割模型 - 快速检测',
#             'accuracy': 0.85,
#             'inference_speed': 15.0,
#             'model_size': 6.7
#         },
#         {
#             'name': 'yolo11s-seg.pt',
#             'file_path': 'yolo11s-seg.pt',
#             'description': 'YOLO11 Small分割模型 - 平衡性能',
#             'accuracy': 0.88,
#             'inference_speed': 25.0,
#             'model_size': 11.8
#         },
#         {
#             'name': 'yolo11m-seg.pt',
#             'file_path': 'yolo11m-seg.pt',
#             'description': 'YOLO11 Medium分割模型 - 高精度',
#             'accuracy': 0.91,
#             'inference_speed': 45.0,
#             'model_size': 22.5
#         }
#     ]
    
#     for model_data in default_models:
#         model, created = ModelConfig.objects.get_or_create(
#             name=model_data['name'],
#             defaults=model_data
#         )
#         if created:
#             print(f"创建模型配置: {model.name}")
#         else:
#             print(f"模型配置已存在: {model.name}")


def collect_static():
    """收集静态文件"""
    print("\n=== 收集静态文件 ===")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    print("静态文件收集完成")


def main():
    """主函数"""
    print("开始初始化Django项目...")
    
    try:
        # 创建目录
        create_directories()
        
        # 运行迁移
        run_migrations()
        
        # 创建超级用户
        create_superuser()
        
        # 创建默认模型配置
        # create_default_models()
        
        # 收集静态文件
        collect_static()
        
        print("\nDjango项目初始化完成！")
        print("\n接下来的步骤:")
        print("1. 确保yoloserver目录中有训练好的模型文件")
        print("2. 运行开发服务器: python manage.py runserver")
        print("3. 访问 http://127.0.0.1:8000 开始使用")
        print("4. 访问 http://127.0.0.1:8000/admin 进入管理后台")
        
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
