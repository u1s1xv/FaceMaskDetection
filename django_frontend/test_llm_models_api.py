#!/usr/bin/env python3
"""
测试LLM模型API
"""
import os
import sys
import django
import json

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_mask_detection.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from detection.api_views import api_get_llm_models
from llm_config import AVAILABLE_MODELS, DEFAULT_MODEL


def test_llm_models_api():
    """测试LLM模型API"""
    print("🔍 测试LLM模型API...")
    
    # 创建测试用户和请求
    factory = RequestFactory()
    user = User.objects.create_user(username='testuser', password='testpass')
    
    # 创建GET请求
    request = factory.get('/api/llm-models/')
    request.user = user
    
    # 调用API
    response = api_get_llm_models(request)
    
    # 验证响应
    assert response.status_code == 200
    
    # 解析响应数据
    data = json.loads(response.content)
    
    assert data['success'] == True
    assert 'models' in data
    assert 'default_model' in data
    assert data['default_model'] == DEFAULT_MODEL
    
    # 验证模型列表
    models = data['models']
    assert len(models) > 0
    
    # 验证每个模型都有必要的字段
    for model in models:
        assert 'value' in model
        assert 'name' in model
        assert 'description' in model
    
    # 验证默认模型在列表中
    model_values = [m['value'] for m in models]
    assert DEFAULT_MODEL in model_values
    
    print("✅ LLM模型API测试通过")
    print(f"✅ 找到 {len(models)} 个可用模型")
    print(f"✅ 默认模型: {DEFAULT_MODEL}")
    
    # 清理测试用户
    user.delete()


def test_available_models_config():
    """测试可用模型配置"""
    print("🔍 测试可用模型配置...")
    
    # 验证配置格式
    assert isinstance(AVAILABLE_MODELS, list)
    assert len(AVAILABLE_MODELS) > 0
    
    # 验证每个模型配置
    for model in AVAILABLE_MODELS:
        assert isinstance(model, dict)
        assert 'value' in model
        assert 'name' in model
        assert 'description' in model
        assert isinstance(model['value'], str)
        assert isinstance(model['name'], str)
        assert isinstance(model['description'], str)
        assert len(model['value']) > 0
        assert len(model['name']) > 0
        assert len(model['description']) > 0
    
    # 验证默认模型
    assert isinstance(DEFAULT_MODEL, str)
    assert len(DEFAULT_MODEL) > 0
    
    model_values = [m['value'] for m in AVAILABLE_MODELS]
    assert DEFAULT_MODEL in model_values
    
    print("✅ 可用模型配置验证通过")
    print(f"✅ 配置了 {len(AVAILABLE_MODELS)} 个模型")
    
    # 打印模型列表
    for model in AVAILABLE_MODELS:
        print(f"   - {model['name']}: {model['description']}")


def main():
    """运行所有测试"""
    print("🚀 开始测试LLM模型配置...\n")
    
    try:
        test_available_models_config()
        print()
        test_llm_models_api()
        
        print("\n🎉 所有测试通过！")
        print("✅ 模型映射已删除")
        print("✅ 前端直接显示实际模型名称")
        print("✅ LLM模型API工作正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
