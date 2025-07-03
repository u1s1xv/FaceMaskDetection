#!/usr/bin/env python
"""
Django开发服务器启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """检查环境"""
    print("检查环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查Django是否安装
    try:
        import django
        print(f"✓ Django版本: {django.get_version()}")
    except ImportError:
        print("❌ Django未安装，请运行: pip install -r requirements.txt")
        return False
    
    # 检查yoloserver目录
    yolo_dir = Path(__file__).parent.parent / 'yoloserver'
    if not yolo_dir.exists():
        print(f"警告: yoloserver目录不存在: {yolo_dir}")
        print("   请确保yoloserver项目在正确位置")
    else:
        print(f"✓ yoloserver目录: {yolo_dir}")
    
    return True


def install_dependencies():
    """安装依赖"""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    if requirements_file.exists():
        print("安装依赖包...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True, encoding='utf-8', errors='replace')
            print("✓ 依赖包安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖包安装失败")
            return False
    return True


def setup_project():
    """设置项目"""
    setup_script = Path(__file__).parent / 'setup_django.py'
    if setup_script.exists():
        print("初始化项目...")
        try:
            subprocess.run([sys.executable, str(setup_script)], check=True, encoding='utf-8', errors='replace')
            print("✓ 项目初始化完成")
        except subprocess.CalledProcessError:
            print("❌ 项目初始化失败")
            return False
    return True


def start_server(host='127.0.0.1', port='8000'):
    """启动开发服务器"""
    print(f"启动Django开发服务器...")
    print(f"   地址: http://{host}:{port}")
    print(f"   管理后台: http://{host}:{port}/admin")
    print("   按 Ctrl+C 停止服务器")
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', f'{host}:{port}'
        ], check=True, encoding='utf-8', errors='replace')
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务器启动失败: {e}")


def main():
    """主函数"""
    print("口罩检测系统 - Django前端")
    print("=" * 50)
    
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查是否需要安装依赖
    try:
        import django
        from django.conf import settings
    except ImportError:
        print("检测到缺少依赖，开始安装...")
        if not install_dependencies():
            sys.exit(1)
    
    # 检查是否需要初始化项目
    db_file = project_dir / 'db.sqlite3'
    if not db_file.exists():
        print("检测到项目未初始化，开始设置...")
        if not setup_project():
            sys.exit(1)
    
    # 启动服务器
    start_server()


if __name__ == '__main__':
    main()
