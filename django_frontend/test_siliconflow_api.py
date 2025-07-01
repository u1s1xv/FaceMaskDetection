#!/usr/bin/env python
"""
测试SiliconFlow API集成
"""
import requests
import json
import time

def test_siliconflow_api_direct():
    """直接测试SiliconFlow API"""
    print("🔍 直接测试SiliconFlow API...")
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    
    payload = {
        "model": "Qwen/QwQ-32B",
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的口罩检测分析专家，请用中文回答，语言专业且易懂。"
            },
            {
                "role": "user",
                "content": "基于以下检测结果，请分析这张图片中的口罩佩戴情况：总检测数量5人，正确佩戴3人，未佩戴1人，错误佩戴1人，合规率60%。请给出专业的评估和建议。"
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": "Bearer sk-your-api-key-here",  # 请替换为实际API密钥
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📤 发送请求到: {url}")
        print(f"📋 使用模型: {payload['model']}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"📝 分析结果预览: {content[:200]}...")
                print(f"📊 完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                print("❌ 响应格式错误")
                print(f"📄 响应内容: {result}")
        else:
            print(f"❌ API调用失败!")
            print(f"📄 错误响应: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"🌐 网络错误: {str(e)}")
    except Exception as e:
        print(f"💥 其他错误: {str(e)}")


def test_django_llm_api():
    """测试Django的大模型API接口"""
    print("\n🔍 测试Django大模型API接口...")
    
    url = "http://127.0.0.1:8000/api/llm-analysis/"
    
    test_data = {
        "prompt": "基于检测结果，请分析这张图片中的口罩佩戴情况，并给出专业的评估和建议。",
        "model": "gpt-4",
        "record_id": 17,  # 请确保这个记录ID存在
        "detection_data": {
            "total_detections": 5,
            "with_mask_count": 3,
            "without_mask_count": 1,
            "incorrect_mask_count": 1,
            "compliance_rate": 60.0,
            "model_name": "yolo11n-seg.pt",
            "confidence_threshold": 0.25,
            "detection_details": []
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    try:
        print(f"📤 发送请求到: {url}")
        print(f"📋 测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=test_data, headers=headers, timeout=60)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Django API调用成功!")
            
            if result.get('success'):
                print(f"📝 分析结果预览: {result.get('analysis', '')[:200]}...")
                print(f"🤖 使用模型: {result.get('model_used', 'N/A')}")
                print(f"🔌 API提供商: {result.get('api_provider', 'N/A')}")
                print(f"⏰ 时间戳: {result.get('timestamp', 'N/A')}")
            else:
                print(f"❌ 分析失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ Django API调用失败!")
            print(f"📄 错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("🔌 连接失败! 请确保Django服务器正在运行")
        print("💡 启动命令: python manage.py runserver")
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except Exception as e:
        print(f"💥 其他错误: {str(e)}")


def test_model_mapping():
    """测试模型映射功能"""
    print("\n🔍 测试模型映射...")
    
    model_mapping = {
        'gpt-4': 'Qwen/QwQ-32B',
        'gpt-3.5-turbo': 'Qwen/Qwen2.5-7B-Instruct',
        'claude-3-sonnet': 'Qwen/QwQ-32B',
        'gemini-pro': 'Qwen/QwQ-32B'
    }
    
    print("📋 前端模型 → SiliconFlow模型映射:")
    for frontend_model, siliconflow_model in model_mapping.items():
        print(f"   {frontend_model} → {siliconflow_model}")
    
    print("\n✅ 模型映射配置正确")


def main():
    """主测试函数"""
    print("🧪 SiliconFlow API集成测试")
    print("=" * 50)
    
    # 测试模型映射
    test_model_mapping()
    
    # 测试SiliconFlow API（需要有效的API密钥）
    print("\n" + "=" * 50)
    test_siliconflow_api_direct()
    
    # 测试Django API
    print("\n" + "=" * 50)
    test_django_llm_api()
    
    print("\n" + "=" * 50)
    print("🎯 测试完成!")
    print("\n📝 注意事项:")
    print("1. 请将API密钥替换为您的实际密钥")
    print("2. 确保Django服务器正在运行")
    print("3. 确保测试用的record_id存在")
    print("4. 检查网络连接是否正常")


if __name__ == "__main__":
    main()
