# SiliconFlow API 集成说明

## 🎯 概述

本项目已成功集成SiliconFlow API，支持调用Qwen系列大模型进行智能分析。

## 🔧 API配置

### 1. 获取API密钥

1. 访问 [SiliconFlow官网](https://api.siliconflow.cn/)
2. 注册账号并登录
3. 获取您的API密钥

### 2. 配置API密钥

在 `django_frontend/detection/api_views.py` 文件中找到以下配置：

```python
SILICONFLOW_CONFIG = {
    'api_key': 'sk-your-api-key-here',  # 请替换为您的实际API密钥
    'base_url': 'https://api.siliconflow.cn/v1/chat/completions',
    'timeout': 30,
    'max_tokens': 1000,
    'temperature': 0.7
}
```

将 `sk-your-api-key-here` 替换为您的真实API密钥。

### 3. 模型映射

系统将前端选择的模型映射到SiliconFlow的实际模型：

| 前端显示 | SiliconFlow模型 | 说明 |
|---------|----------------|------|
| GPT-4 (精准) | Qwen/QwQ-32B | 推理能力强，适合复杂分析 |
| GPT-3.5 Turbo (快速) | Qwen/Qwen2.5-7B-Instruct | 响应快速，适合简单分析 |
| Claude-3 Sonnet | Qwen/QwQ-32B | 备用映射 |
| Gemini Pro | Qwen/QwQ-32B | 备用映射 |

## 🚀 使用方法

### 1. 在检测结果页面
1. 完成图片检测后，滚动到"AI智能分析"模块
2. 输入分析提示词（或使用默认提示）
3. 选择AI模型
4. 点击"开始AI分析"按钮

### 2. API调用流程
```
前端请求 → Django API → SiliconFlow API → 返回分析结果
```

### 3. 备用机制
- 如果SiliconFlow API调用失败（网络问题、密钥无效等）
- 系统会自动使用预设的模拟分析结果
- 确保功能的可用性和稳定性

## 🔍 测试验证

### 运行测试脚本
```bash
python test_siliconflow_api.py
```

### 测试内容
1. **模型映射测试** - 验证前端模型到SiliconFlow模型的映射
2. **直接API测试** - 直接调用SiliconFlow API
3. **Django API测试** - 测试完整的Django API流程

### 预期结果
- ✅ 模型映射配置正确
- ✅ SiliconFlow API调用成功（需要有效密钥）
- ✅ Django API调用成功
- ✅ 备用机制正常工作

## 📊 API响应格式

### 成功响应
```json
{
    "success": true,
    "analysis": "详细的分析结果文本...",
    "model_used": "Qwen/QwQ-32B",
    "api_provider": "SiliconFlow",
    "timestamp": "2025-07-01T16:16:56.363154"
}
```

### 失败响应
```json
{
    "success": false,
    "error": "错误信息描述"
}
```

## 🛠️ 故障排除

### 1. API密钥无效
**错误**: "Api key is invalid"
**解决**: 检查并更新API密钥

### 2. 网络连接问题
**错误**: 连接超时或网络错误
**解决**: 检查网络连接，或使用备用分析结果

### 3. 模型不可用
**错误**: 指定模型不存在
**解决**: 检查模型映射配置，使用可用的模型

### 4. 请求频率限制
**错误**: Rate limit exceeded
**解决**: 降低请求频率，或升级API套餐

## 💡 优化建议

### 1. 环境变量配置
建议使用环境变量管理API密钥：

```python
import os
SILICONFLOW_CONFIG = {
    'api_key': os.getenv('SILICONFLOW_API_KEY', 'sk-your-api-key-here'),
    # ... 其他配置
}
```

### 2. 错误重试机制
可以添加自动重试逻辑：

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator
```

### 3. 缓存机制
对于相同的分析请求，可以实现缓存机制避免重复调用API。

## 📈 扩展功能

1. **多API支持**: 可以集成其他大模型API作为备选
2. **分析历史**: 保存分析结果到数据库
3. **自定义模板**: 支持用户自定义分析模板
4. **批量分析**: 支持批量检测结果的分析

---

**配置完成后，您就可以享受真正的AI智能分析功能了！** 🎉
