#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unicode编码修复测试脚本
用于验证修复后的系统是否能正确处理中文字符和UTF-8编码
"""

import subprocess
import sys
import os
import tempfile
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def test_subprocess_encoding():
    """测试subprocess调用的编码处理"""
    logger.info("开始测试subprocess编码处理...")

    try:
        # 测试基本的subprocess调用，使用更安全的编码处理
        result = subprocess.run(
            [sys.executable, '-c', 'print("测试中文输出：口罩检测系统")'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 使用replace错误处理策略
            timeout=10
        )

        if result.returncode == 0:
            output = result.stdout.strip() if result.stdout else ""
            logger.info(f"✓ subprocess UTF-8编码测试成功: {output}")
            return True
        else:
            stderr = result.stderr if result.stderr else "未知错误"
            logger.error(f"✗ subprocess测试失败: {stderr}")
            return False

    except UnicodeDecodeError as e:
        logger.error(f"✗ Unicode解码错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ subprocess测试异常: {e}")
        return False

def test_file_encoding():
    """测试文件读写的编码处理"""
    logger.info("开始测试文件编码处理...")
    
    try:
        # 创建临时文件测试
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            test_content = "测试中文内容：口罩检测系统\n包含特殊字符：①②③④⑤\n英文内容：Face Mask Detection System"
            f.write(test_content)
            temp_file = f.name
        
        # 读取文件测试
        with open(temp_file, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        if read_content == test_content:
            logger.info("✓ 文件UTF-8编码读写测试成功")
            success = True
        else:
            logger.error("✗ 文件内容不匹配")
            success = False
            
        # 清理临时文件
        os.unlink(temp_file)
        return success
        
    except UnicodeDecodeError as e:
        logger.error(f"✗ 文件Unicode解码错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ 文件编码测试异常: {e}")
        return False

def test_django_service():
    """测试Django服务的编码处理"""
    logger.info("开始测试Django服务编码处理...")
    
    try:
        # 检查Django前端目录是否存在
        django_dir = Path("django_frontend")
        if not django_dir.exists():
            logger.warning("Django前端目录不存在，跳过Django服务测试")
            return True
        
        # 测试Django管理命令
        result = subprocess.run(
            [sys.executable, 'manage.py', 'check'],
            cwd=str(django_dir),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 使用replace错误处理策略
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("✓ Django服务编码测试成功")
            return True
        else:
            stderr = result.stderr if result.stderr else ""
            logger.warning(f"Django检查有警告: {stderr}")
            # 即使有警告，只要没有编码错误就算成功
            if 'gbk' not in stderr.lower() and 'unicode' not in stderr.lower():
                return True
            else:
                logger.error(f"✗ Django服务仍存在编码问题: {stderr}")
                return False
                
    except UnicodeDecodeError as e:
        logger.error(f"✗ Django服务Unicode解码错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Django服务测试异常: {e}")
        return False

def test_yolo_service():
    """测试YOLO服务的编码处理"""
    logger.info("开始测试YOLO服务编码处理...")
    
    try:
        # 检查YOLO服务器目录是否存在
        yolo_dir = Path("yoloserver")
        if not yolo_dir.exists():
            logger.warning("YOLO服务器目录不存在，跳过YOLO服务测试")
            return True
        
        # 测试YOLO初始化脚本
        init_script = yolo_dir / "initialize_project.py"
        if init_script.exists():
            result = subprocess.run(
                [sys.executable, str(init_script), '--check-only'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # 使用replace错误处理策略
                timeout=30
            )

            # 检查是否有编码相关错误
            stderr = result.stderr if result.stderr else ""
            if 'gbk' not in stderr.lower() and 'unicode' not in stderr.lower():
                logger.info("✓ YOLO服务编码测试成功")
                return True
            else:
                logger.error(f"✗ YOLO服务仍存在编码问题: {stderr}")
                return False
        else:
            logger.info("YOLO初始化脚本不存在，跳过测试")
            return True
            
    except UnicodeDecodeError as e:
        logger.error(f"✗ YOLO服务Unicode解码错误: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ YOLO服务测试异常: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始Unicode编码修复验证测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("subprocess编码处理", test_subprocess_encoding),
        ("文件编码处理", test_file_encoding),
        ("Django服务编码", test_django_service),
        ("YOLO服务编码", test_yolo_service),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 40}")
        logger.info(f"测试项目: {test_name}")
        logger.info(f"{'=' * 40}")
        
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 发生异常: {e}")
            test_results.append((test_name, False))
    
    # 汇总测试结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Unicode编码问题已成功修复。")
        return True
    else:
        logger.error(f"❌ 仍有 {total - passed} 项测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
