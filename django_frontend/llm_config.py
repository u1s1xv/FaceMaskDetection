"""
大模型API配置文件
"""
import os

# SiliconFlow API配置
SILICONFLOW_CONFIG = {
    'api_key': os.getenv('SILICONFLOW_API_KEY', 'sk-your-api-key-here'),
    'base_url': 'https://api.siliconflow.cn/v1/chat/completions',
    'timeout': 30,
    'max_tokens': 1000,
    'temperature': 0.7
}

# 模型映射配置 - 将前端选择的模型映射到SiliconFlow的实际模型
MODEL_MAPPING = {
    'gpt-4': 'Qwen/QwQ-32B',
    'gpt-3.5-turbo': 'Qwen/Qwen2.5-7B-Instruct', 
    'claude-3-sonnet': 'Qwen/QwQ-32B',
    'gemini-pro': 'Qwen/QwQ-32B'
}

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
