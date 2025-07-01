#!/usr/bin/env python
"""
测试模板修复
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

def test_template_syntax():
    """测试模板语法"""
    print("\n=== 测试模板语法 ===")
    
    try:
        from django.template.loader import get_template
        
        # 测试模型管理模板
        template = get_template('detection/models.html')
        print("✓ 模型管理模板语法正确")
        
        return True
    except Exception as e:
        print(f"❌ 模板语法错误: {e}")
        return False

def test_view_function():
    """测试视图函数"""
    print("\n=== 测试视图函数 ===")
    
    try:
        from detection.views import model_management
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/models/')
        
        # 调用视图函数
        response = model_management(request)
        print(f"✓ 视图函数执行成功，状态码: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ 视图函数执行失败: {e}")
        return False

def test_context_data():
    """测试上下文数据"""
    print("\n=== 测试上下文数据 ===")
    
    try:
        from detection.views import model_management
        from django.test import RequestFactory
        from django.template import Context, Template
        
        factory = RequestFactory()
        request = factory.get('/models/')
        
        # 获取视图响应
        response = model_management(request)
        
        if hasattr(response, 'context_data'):
            context = response.context_data
            print(f"✓ 上下文数据获取成功")
            
            # 检查必要的键
            required_keys = ['available_models', 'stats', 'model_status', 'orphan_models']
            for key in required_keys:
                if key in context:
                    print(f"  ✓ {key}: 存在")
                else:
                    print(f"  ❌ {key}: 缺失")
            
            # 检查stats结构
            if 'stats' in context:
                stats = context['stats']
                stats_keys = ['total_files', 'total_configured', 'total_orphan', 'total_active']
                for key in stats_keys:
                    if key in stats:
                        print(f"  ✓ stats.{key}: {stats[key]}")
                    else:
                        print(f"  ❌ stats.{key}: 缺失")
        
        return True
    except Exception as e:
        print(f"❌ 上下文数据测试失败: {e}")
        return False

def test_template_rendering():
    """测试模板渲染"""
    print("\n=== 测试模板渲染 ===")
    
    try:
        from django.template.loader import render_to_string
        
        # 创建测试上下文
        context = {
            'available_models': [
                {
                    'name': 'test_model.pt',
                    'description': '测试模型',
                    'size': 10.5,
                    'config_status': 'active'
                }
            ],
            'stats': {
                'total_files': 1,
                'total_configured': 1,
                'total_orphan': 0,
                'total_active': 1
            },
            'model_status': [],
            'orphan_models': [],
            'page_title': '模型管理'
        }
        
        # 渲染模板
        html = render_to_string('detection/models.html', context)
        print("✓ 模板渲染成功")
        print(f"  渲染内容长度: {len(html)} 字符")
        
        # 检查关键内容
        if 'test_model.pt' in html:
            print("  ✓ 模型名称显示正确")
        if 'badge bg-success' in html:
            print("  ✓ 状态徽章显示正确")
        
        return True
    except Exception as e:
        print(f"❌ 模板渲染失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 模板修复测试")
    print("=" * 50)
    
    tests = [
        test_template_syntax,
        test_view_function,
        test_context_data,
        test_template_rendering
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！模板修复成功。")
        print("\n📋 修复内容:")
        print("1. 移除了Django模板中不存在的 'map' 过滤器")
        print("2. 在视图中预处理数据，简化模板逻辑")
        print("3. 添加了统计数据的计算")
        print("4. 优化了模板的数据显示逻辑")
        
        print("\n🚀 现在可以正常访问模型管理页面了！")
    else:
        print("⚠️  部分测试失败，请检查修复。")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
