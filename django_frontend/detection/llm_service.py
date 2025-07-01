"""
大模型API集成服务
处理与各种大模型API的交互
"""
import json
import time
import logging
from typing import Dict, Any, Optional
from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class LLMService:
    """大模型服务基类"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'LLM_API_KEY', '')
        self.api_base_url = getattr(settings, 'LLM_API_BASE_URL', '')
        self.model_name = getattr(settings, 'LLM_MODEL_NAME', 'gpt-3.5-turbo')
        self.timeout = getattr(settings, 'LLM_API_TIMEOUT', 30)
        self.max_tokens = getattr(settings, 'LLM_MAX_TOKENS', 1000)
        
    def analyze_detection_result(self, detection_record, user_prompt: str) -> Dict[str, Any]:
        """
        分析检测结果
        
        Args:
            detection_record: 检测记录对象
            user_prompt: 用户输入的提示词
            
        Returns:
            包含分析结果的字典
        """
        try:
            start_time = time.time()
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt(detection_record)
            
            # 构建完整的提示词
            full_prompt = self._build_full_prompt(system_prompt, user_prompt, detection_record)
            
            # 调用API
            response = self._call_api(full_prompt)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': True,
                'analysis': response.get('content', ''),
                'response_time': response_time,
                'token_usage': response.get('token_usage', {}),
                'model_name': self.model_name
            }
            
        except Exception as e:
            logger.error(f"LLM分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis': '',
                'response_time': 0,
                'token_usage': {},
                'model_name': self.model_name
            }
    
    def _build_system_prompt(self, detection_record) -> str:
        """构建系统提示词"""
        return f"""你是一个专业的口罩检测分析专家。请基于以下检测数据，为用户提供专业、准确的分析和建议。

检测基本信息：
- 检测时间: {detection_record.upload_time.strftime('%Y-%m-%d %H:%M:%S')}
- 使用模型: {detection_record.model_name}
- 置信度阈值: {detection_record.confidence_threshold}
- IOU阈值: {detection_record.iou_threshold}
- 处理时间: {detection_record.processing_time:.2f}秒

检测结果统计：
- 总检测人数: {detection_record.total_detections}
- 正确佩戴口罩: {detection_record.with_mask_count}人
- 未佩戴口罩: {detection_record.without_mask_count}人  
- 错误佩戴口罩: {detection_record.incorrect_mask_count}人
- 合规率: {detection_record.detection_summary.get('compliance_rate', 0)}%

请用专业但易懂的语言回答用户的问题，提供实用的建议和见解。"""

    def _build_full_prompt(self, system_prompt: str, user_prompt: str, detection_record) -> str:
        """构建完整的提示词"""
        context = f"""
{system_prompt}

用户问题: {user_prompt}

请提供详细的分析和建议。"""
        return context
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """调用API的基础方法，子类需要重写"""
        raise NotImplementedError("子类必须实现_call_api方法")


class OpenAIService(LLMService):
    """OpenAI API服务"""
    
    def __init__(self):
        super().__init__()
        self.api_base_url = self.api_base_url or 'https://api.openai.com/v1'
        
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """调用OpenAI API"""
        if not self.api_key:
            raise ValueError("未配置OpenAI API密钥")
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model_name,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': self.max_tokens,
            'temperature': 0.7
        }
        
        response = requests.post(
            f'{self.api_base_url}/chat/completions',
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
            
        result = response.json()
        
        return {
            'content': result['choices'][0]['message']['content'],
            'token_usage': result.get('usage', {})
        }


class MockLLMService(LLMService):
    """模拟LLM服务，用于开发和测试"""
    
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """模拟API调用"""
        # 模拟API延迟
        time.sleep(1)
        
        # 生成模拟响应
        mock_response = self._generate_mock_response(prompt)
        
        return {
            'content': mock_response,
            'token_usage': {
                'prompt_tokens': len(prompt.split()),
                'completion_tokens': len(mock_response.split()),
                'total_tokens': len(prompt.split()) + len(mock_response.split())
            }
        }
    
    def _generate_mock_response(self, prompt: str) -> str:
        """生成模拟响应"""
        if "整体分析" in prompt or "整体情况" in prompt:
            return """基于检测结果的整体分析：

1. **检测概况**：
   - 本次检测共识别到多个目标，系统运行正常
   - 检测模型表现稳定，置信度设置合理

2. **合规情况**：
   - 正确佩戴口罩的比例较高，说明整体防护意识良好
   - 仍有部分人员存在未佩戴或错误佩戴的情况

3. **主要发现**：
   - 大部分人员能够正确佩戴口罩
   - 需要关注未佩戴口罩的人员，加强宣传教育
   - 错误佩戴的情况需要具体指导改正

4. **建议措施**：
   - 继续保持良好的防护习惯
   - 对未合规人员进行针对性教育
   - 定期开展口罩佩戴规范培训"""
        
        elif "建议" in prompt:
            return """改进口罩佩戴情况的具体建议：

1. **教育宣传**：
   - 制作口罩正确佩戴的图文指南
   - 在显眼位置张贴提醒标识
   - 定期组织防护知识培训

2. **监督管理**：
   - 增加检查频次，及时发现问题
   - 建立奖惩机制，鼓励正确佩戴
   - 设置专人负责监督提醒

3. **环境优化**：
   - 在入口处设置口罩佩戴检查点
   - 提供备用口罩供临时使用
   - 改善通风条件，提高佩戴舒适度

4. **技术支持**：
   - 继续使用AI检测系统进行监控
   - 优化检测参数，提高识别准确率
   - 建立数据档案，跟踪改进效果"""
        
        else:
            return """感谢您的询问。基于当前的检测数据，我为您提供以下分析：

检测系统运行正常，能够有效识别不同的口罩佩戴状态。从数据来看，大部分人员都有良好的防护意识，但仍有改进空间。

建议：
1. 继续保持现有的良好做法
2. 针对性地改进不合规情况
3. 定期评估和调整防护措施
4. 加强宣传教育，提高整体合规率

如果您有更具体的问题，欢迎继续询问。"""


def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    service_type = getattr(settings, 'LLM_SERVICE_TYPE', 'mock')
    
    if service_type == 'openai':
        return OpenAIService()
    else:
        return MockLLMService()
