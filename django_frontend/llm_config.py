"""
大模型API配置文件
"""
import os

# SiliconFlow API配置
SILICONFLOW_CONFIG = {
    'api_key': os.getenv('SILICONFLOW_API_KEY', 'sk-your-api-key-here'),
    'base_url': 'https://api.siliconflow.cn/v1/chat/completions',
    'timeout': 120,  # 增加到120秒，给AI更多时间生成完整回答
    'max_tokens': 4000,  # 增加到4000，允许更长的回答
    'temperature': 0.7
}

# 可用的SiliconFlow模型列表
AVAILABLE_MODELS = [
    {
        'value': 'Qwen/QwQ-32B',
        'name': 'Qwen QwQ-32B',
        'description': '强大的推理模型，适合复杂分析'
    },
    {
        'value': 'Qwen/Qwen2.5-7B-Instruct',
        'name': 'Qwen 2.5-7B-Instruct',
        'description': '快速响应，适合一般分析'
    },
    {
        'value': 'Qwen/Qwen2.5-14B-Instruct',
        'name': 'Qwen 2.5-14B-Instruct',
        'description': '平衡性能，综合分析能力强'
    },
    {
        'value': 'deepseek-ai/DeepSeek-V2.5',
        'name': 'DeepSeek V2.5',
        'description': '深度思考模型，适合专业分析'
    }
]

# 默认模型
DEFAULT_MODEL = 'Qwen/QwQ-32B'

# 系统提示词
SYSTEM_PROMPT = "你是一个专业的口罩检测分析专家，请用中文回答，语言专业且易懂。"

# API重试配置
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1,  # 秒
    'backoff_factor': 2
}

# 日志配置
LOGGING_CONFIG = {
    'log_requests': True,
    'log_responses': True,
    'log_errors': True
}
