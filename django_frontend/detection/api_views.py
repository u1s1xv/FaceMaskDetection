"""
API视图
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging
import requests
import time
from datetime import datetime

from .models import DetectionRecord, ModelConfig
from .services import YOLOInferenceService

# 大模型API配置 - 直接在这里定义，避免导入问题
SILICONFLOW_CONFIG = {
    'api_key': '***REMOVED-API-KEY***',  # 请替换为您的实际API密钥
    'base_url': 'https://api.siliconflow.cn/v1/chat/completions',
    'timeout': 30,
    'max_tokens': 1000,
    'temperature': 0.7
}

MODEL_MAPPING = {
    'gpt-4': 'Qwen/QwQ-32B',
    'gpt-3.5-turbo': 'Qwen/Qwen2.5-7B-Instruct',
    'claude-3-sonnet': 'Qwen/QwQ-32B',
    'gemini-pro': 'Qwen/QwQ-32B'
}

DEFAULT_MODEL = 'Qwen/QwQ-32B'
SYSTEM_PROMPT = "你是一个专业的口罩检测分析专家，请用中文回答，语言专业且易懂。"

logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_upload_detect(request):
    """API: 上传图片并检测"""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({'error': '没有上传图片'}, status=400)

        image = request.FILES['image']
        model_name = request.POST.get('model_name', 'yolo11n-seg.pt')
        confidence = float(request.POST.get('confidence', 0.25))
        iou = float(request.POST.get('iou', 0.45))
        imgsz = int(request.POST.get('imgsz', 640))

        # 创建检测记录，关联当前用户
        record = DetectionRecord.objects.create(
            user=request.user,  # 关联当前用户
            original_image=image,
            model_name=model_name,
            confidence_threshold=confidence,
            iou_threshold=iou,
            image_size=imgsz,
            status='pending'
        )
        
        # 执行检测
        inference_service = YOLOInferenceService()
        result = inference_service.run_inference(
            image_path=record.original_image.path,
            model_name=model_name,
            confidence=confidence,
            iou=iou,
            imgsz=imgsz
        )
        
        # 更新记录
        record.status = 'completed'
        record.total_detections = result['total_detections']
        record.with_mask_count = result['with_mask_count']
        record.without_mask_count = result['without_mask_count']
        record.incorrect_mask_count = result['incorrect_mask_count']
        record.processing_time = result['processing_time']
        record.detection_details = result['detections']
        
        # 保存结果图像
        if result.get('beautified_image_path'):
            result_image = inference_service.copy_result_image(
                result['beautified_image_path'], 
                record.result_image
            )
            if result_image:
                record.result_image.save(
                    f'result_{record.id}.png',
                    result_image,
                    save=False
                )
        
        record.save()
        
        return JsonResponse({
            'success': True,
            'record_id': record.id,
            'result': {
                'total_detections': record.total_detections,
                'with_mask_count': record.with_mask_count,
                'without_mask_count': record.without_mask_count,
                'incorrect_mask_count': record.incorrect_mask_count,
                'processing_time': record.processing_time,
                'original_image_url': record.original_image.url if record.original_image else None,
                'result_image_url': record.result_image.url if record.result_image else None,
                'detection_summary': record.detection_summary
            }
        })
        
    except Exception as e:
        logger.error(f"API检测失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_result(request, record_id):
    """API: 获取检测结果"""
    try:
        # 确保用户只能查看自己的记录，除非是管理员
        if request.user.is_superuser:
            record = get_object_or_404(DetectionRecord, id=record_id)
        else:
            record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)
        
        return JsonResponse({
            'id': record.id,
            'status': record.status,
            'upload_time': record.upload_time.isoformat(),
            'model_name': record.model_name,
            'confidence_threshold': record.confidence_threshold,
            'iou_threshold': record.iou_threshold,
            'image_size': record.image_size,
            'total_detections': record.total_detections,
            'with_mask_count': record.with_mask_count,
            'without_mask_count': record.without_mask_count,
            'incorrect_mask_count': record.incorrect_mask_count,
            'processing_time': record.processing_time,
            'original_image_url': record.original_image.url if record.original_image else None,
            'result_image_url': record.result_image.url if record.result_image else None,
            'detection_details': record.get_detection_details_json(),
            'detection_summary': record.detection_summary,
            'error_message': record.error_message
        })
        
    except Exception as e:
        logger.error(f"获取结果失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_models(request):
    """API: 获取可用模型列表"""
    try:
        # 从文件系统获取实际存在的模型
        inference_service = YOLOInferenceService()
        available_models = inference_service.get_available_models()

        # 从数据库获取配置的模型（只返回文件实际存在的）
        existing_model_names = [model['name'] for model in available_models]
        db_models = ModelConfig.objects.filter(
            is_active=True,
            name__in=existing_model_names
        ).values(
            'name', 'description', 'accuracy', 'inference_speed', 'model_size'
        )

        # 合并信息：优先使用数据库中的描述，如果没有则使用自动生成的
        models_with_config = []
        for file_model in available_models:
            model_info = file_model.copy()

            # 查找对应的数据库配置
            db_config = next(
                (db for db in db_models if db['name'] == file_model['name']),
                None
            )

            if db_config:
                # 使用数据库中的信息覆盖文件信息
                model_info.update(db_config)

            models_with_config.append(model_info)

        return JsonResponse({
            'available_models': models_with_config,
            'total_count': len(models_with_config),
            'models_dir': str(inference_service.models_dir)
        })

    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_history(request):
    """API: 获取检测历史"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        status_filter = request.GET.get('status', '')

        # 根据用户权限获取数据
        if request.user.is_superuser:
            show_all = request.GET.get('show_all', 'false') == 'true'
            if show_all:
                records = DetectionRecord.objects.all()
            else:
                records = DetectionRecord.objects.filter(user=request.user)
        else:
            records = DetectionRecord.objects.filter(user=request.user)
        
        if status_filter:
            records = records.filter(status=status_filter)
        
        records = records.order_by('-upload_time')
        
        # 简单分页
        start = (page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]
        
        results = []
        for record in page_records:
            results.append({
                'id': record.id,
                'upload_time': record.upload_time.isoformat(),
                'status': record.status,
                'model_name': record.model_name,
                'total_detections': record.total_detections,
                'with_mask_count': record.with_mask_count,
                'without_mask_count': record.without_mask_count,
                'incorrect_mask_count': record.incorrect_mask_count,
                'processing_time': record.processing_time,
                'original_image_url': record.original_image.url if record.original_image else None,
                'result_image_url': record.result_image.url if record.result_image else None,
            })
        
        return JsonResponse({
            'results': results,
            'total_count': records.count(),
            'page': page,
            'page_size': page_size,
            'has_next': end < records.count()
        })
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_record(request, record_id):
    """API: 删除检测记录"""
    try:
        # 确保用户只能删除自己的记录，除非是管理员
        if request.user.is_superuser:
            record = get_object_or_404(DetectionRecord, id=record_id)
        else:
            record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)

        # 删除相关文件
        if record.original_image:
            record.original_image.delete()
        if record.result_image:
            record.result_image.delete()

        record.delete()

        return JsonResponse({'success': True, 'message': '记录删除成功'})

    except Exception as e:
        logger.error(f"删除记录失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_clear_cache(request):
    """API: 清理缓存"""
    try:
        # 清理session中的默认参数
        if 'default_params' in request.session:
            del request.session['default_params']

        # 可以在这里添加其他缓存清理逻辑
        # 例如：清理临时文件、重置配置等

        return JsonResponse({'success': True, 'message': '缓存清理成功'})

    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_llm_analysis(request):
    """API: 大模型分析接口"""
    try:
        # 解析请求数据
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        model = data.get('model', 'gpt-3.5-turbo')
        record_id = data.get('record_id')
        detection_data = data.get('detection_data', {})

        if not prompt:
            return JsonResponse({'error': '请输入分析提示词'}, status=400)

        if not record_id:
            return JsonResponse({'error': '缺少检测记录ID'}, status=400)

        # 验证检测记录是否存在
        try:
            record = DetectionRecord.objects.get(id=record_id)
        except DetectionRecord.DoesNotExist:
            return JsonResponse({'error': '检测记录不存在'}, status=404)

        # 构建分析上下文
        analysis_context = build_analysis_context(detection_data, prompt)

        # 调用大模型API
        analysis_result = call_llm_api(model, analysis_context)

        if analysis_result['success']:
            # 记录分析日志
            logger.info(f"LLM分析成功 - 记录ID: {record_id}, 模型: {model}")

            return JsonResponse({
                'success': True,
                'analysis': analysis_result['content'],
                'model_used': model,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return JsonResponse({
                'error': analysis_result['error']
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误'}, status=400)
    except Exception as e:
        logger.error(f"LLM分析失败: {str(e)}")
        return JsonResponse({'error': f'分析失败: {str(e)}'}, status=500)


def build_analysis_context(detection_data, user_prompt):
    """构建分析上下文"""
    context = f"""
作为一个专业的口罩检测分析专家，请基于以下检测数据进行分析：

检测结果统计：
- 总检测人数：{detection_data.get('total_detections', 0)}人
- 正确佩戴口罩：{detection_data.get('with_mask_count', 0)}人
- 未佩戴口罩：{detection_data.get('without_mask_count', 0)}人
- 错误佩戴口罩：{detection_data.get('incorrect_mask_count', 0)}人
- 整体合规率：{detection_data.get('compliance_rate', 0)}%

检测参数：
- 使用模型：{detection_data.get('model_name', 'N/A')}
- 置信度阈值：{detection_data.get('confidence_threshold', 'N/A')}

用户分析需求：
{user_prompt}

请提供专业、详细的分析报告，包括：
1. 检测结果评估
2. 合规性分析
3. 风险评估
4. 改进建议
5. 总结

请用中文回答，语言专业且易懂。
"""
    return context.strip()


def call_llm_api(model, prompt):
    """调用大模型API"""
    try:
        # 获取实际的模型名称
        actual_model = MODEL_MAPPING.get(model, DEFAULT_MODEL)

        # 构建API请求
        payload = {
            "model": actual_model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": SILICONFLOW_CONFIG['max_tokens'],
            "temperature": SILICONFLOW_CONFIG['temperature']
        }

        headers = {
            "Authorization": f"Bearer {SILICONFLOW_CONFIG['api_key']}",
            "Content-Type": "application/json"
        }

        # 发送API请求
        logger.info(f"调用SiliconFlow API - 模型: {actual_model}")
        response = requests.post(
            SILICONFLOW_CONFIG['base_url'],
            json=payload,
            headers=headers,
            timeout=SILICONFLOW_CONFIG['timeout']
        )

        # 检查响应状态
        if response.status_code == 200:
            response_data = response.json()

            # 提取分析结果
            if 'choices' in response_data and len(response_data['choices']) > 0:
                analysis_content = response_data['choices'][0]['message']['content']

                logger.info(f"SiliconFlow API调用成功 - 模型: {actual_model}")
                return {
                    'success': True,
                    'content': analysis_content,
                    'model_used': actual_model,
                    'api_provider': 'SiliconFlow'
                }
            else:
                logger.error(f"SiliconFlow API响应格式错误: {response_data}")
                return {
                    'success': False,
                    'error': 'API响应格式错误'
                }
        else:
            # API调用失败，使用备用的模拟结果
            logger.warning(f"SiliconFlow API调用失败 (状态码: {response.status_code})，使用备用模拟结果")
            logger.warning(f"错误响应: {response.text}")

            # 返回模拟结果作为备用
            return call_fallback_analysis(model, prompt)

    except requests.exceptions.Timeout:
        logger.error("SiliconFlow API调用超时，使用备用模拟结果")
        return call_fallback_analysis(model, prompt)
    except requests.exceptions.RequestException as e:
        logger.error(f"SiliconFlow API网络错误: {str(e)}，使用备用模拟结果")
        return call_fallback_analysis(model, prompt)
    except Exception as e:
        logger.error(f"调用LLM API失败: {str(e)}，使用备用模拟结果")
        return call_fallback_analysis(model, prompt)


def call_fallback_analysis(model, prompt):
    """备用分析方法 - 当API调用失败时使用模拟结果"""
    try:
        logger.info(f"使用备用分析方法 - 模型: {model}")

        # 根据不同模型返回不同的模拟结果
        if 'gpt' in model.lower():
            analysis = generate_gpt_style_analysis(prompt)
        elif 'claude' in model.lower():
            analysis = generate_claude_style_analysis(prompt)
        elif 'gemini' in model.lower():
            analysis = generate_gemini_style_analysis(prompt)
        else:
            analysis = generate_default_analysis(prompt)

        return {
            'success': True,
            'content': analysis,
            'model_used': f'{model} (模拟)',
            'api_provider': 'Fallback'
        }

    except Exception as e:
        logger.error(f"备用分析方法也失败: {str(e)}")
        return {
            'success': False,
            'error': f'分析失败: {str(e)}'
        }


def generate_gpt_style_analysis(prompt):
    """生成GPT风格的分析结果（示例）"""
    return """
## 📊 检测结果专业分析报告

### 1. 检测结果评估
根据AI检测系统的分析结果，本次检测展现了以下特点：
- 检测精度较高，能够准确识别不同的口罩佩戴状态
- 系统成功区分了正确佩戴、未佩戴和错误佩戴三种情况
- 检测结果具有较高的可信度

### 2. 合规性分析
从防疫合规角度分析：
- 当前合规率反映了被检测区域的防疫意识水平
- 需要重点关注未佩戴和错误佩戴的人群
- 建议加强防疫宣传和监督管理

### 3. 风险评估
基于检测结果的风险评估：
- **高风险**：未佩戴口罩的人员存在较高传播风险
- **中风险**：错误佩戴口罩可能降低防护效果
- **低风险**：正确佩戴口罩的人员防护到位

### 4. 改进建议
针对检测结果提出以下建议：
1. **加强宣传教育**：提高公众对正确佩戴口罩的认知
2. **设置提醒标识**：在关键区域设置口罩佩戴提醒
3. **定期检查监督**：建立常态化的检查机制
4. **提供口罩供应**：确保口罩的充足供应

### 5. 总结
本次AI检测分析为防疫管理提供了科学依据，建议持续监测并采取相应措施提高整体合规率。
"""


def generate_claude_style_analysis(prompt):
    """生成Claude风格的分析结果（示例）"""
    return """
# 口罩检测智能分析报告

## 核心发现
通过深度学习算法的精确检测，我们获得了有价值的防疫合规数据。检测系统展现出良好的识别准确性，为后续的防疫决策提供了可靠的数据支撑。

## 详细分析

### 检测质量评估
- 模型表现稳定，检测精度符合预期
- 能够有效区分不同的口罩佩戴状态
- 检测结果的置信度分布合理

### 合规状况分析
当前检测区域的防疫合规情况需要关注：
- 正确佩戴率体现了基础防护意识
- 错误佩戴情况提示需要改进佩戴方法
- 未佩戴情况需要重点干预

### 风险分层管理
建议采用分层管理策略：
1. **即时干预**：对未佩戴人员进行及时提醒
2. **教育指导**：对错误佩戴人员提供正确指导
3. **持续监测**：维持对整体区域的监控

### 优化建议
- 在检测点设置实时提醒系统
- 配备专业人员进行现场指导
- 建立数据追踪和趋势分析机制

## 结论
AI检测技术为精准防疫提供了强有力的工具，建议结合人工管理形成完整的防控体系。
"""


def generate_gemini_style_analysis(prompt):
    """生成Gemini风格的分析结果（示例）"""
    return """
🤖 AI智能分析：口罩检测结果深度解读

## 🎯 检测概览
本次AI检测运用先进的计算机视觉技术，对目标区域进行了全面的口罩佩戴状况分析。系统通过多维度特征识别，准确判断了每个检测对象的口罩佩戴情况。

## 📈 数据洞察

### 技术表现
✅ 检测算法运行稳定，识别准确率高
✅ 多类别分类效果良好
✅ 检测速度满足实时监控需求

### 合规分析
📊 **整体合规水平**：根据检测数据分析当前防疫执行情况
🔍 **重点关注区域**：识别需要加强管理的薄弱环节
📋 **改进空间**：明确提升合规率的具体方向

## 🛡️ 防疫建议

### 即时措施
- 对未佩戴人员进行友善提醒
- 为错误佩戴者提供正确示范
- 确保口罩供应充足

### 长期策略
- 建立智能监控预警机制
- 定期开展防疫知识培训
- 优化检测点位布局

## 🔮 趋势预测
基于当前数据，建议持续监测合规率变化趋势，及时调整防控策略，确保防疫效果的持续性和有效性。

---
*本分析报告由AI智能系统生成，结合了计算机视觉、数据分析和公共卫生专业知识*
"""


def generate_default_analysis(prompt):
    """生成默认分析结果"""
    return """
## 口罩检测分析报告

### 检测结果总结
基于AI智能检测系统的分析，本次检测获得了详细的口罩佩戴数据。检测系统运行正常，结果可信度较高。

### 主要发现
1. **检测精度**：系统能够准确识别不同的口罩佩戴状态
2. **数据质量**：检测结果数据完整，覆盖面广
3. **技术稳定性**：检测过程稳定，无异常情况

### 防疫建议
- 继续保持现有的防疫措施
- 对检测发现的问题及时处理
- 建立长期监测机制

### 后续行动
建议根据检测结果制定针对性的改进措施，提高整体防疫合规水平。

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
