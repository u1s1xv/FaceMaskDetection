"""
API视图
"""
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
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
from .pdf_service import PDFReportService

# 大模型API配置 - 直接在这里定义，避免导入问题
SILICONFLOW_CONFIG = {
    'api_key': '***REMOVED-API-KEY***',  # 请替换为您的实际API密钥
    'base_url': 'https://api.siliconflow.cn/v1/chat/completions',
    'timeout': 120,  # 增加到120秒，给AI更多时间生成完整回答
    'max_tokens': 4000,  # 增加到4000，允许更长的回答
    'temperature': 0.7
}

# 从配置文件导入可用模型
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import AVAILABLE_MODELS

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
@require_http_methods(["GET"])
def api_get_llm_models(request):
    """API: 获取可用的LLM模型列表"""
    try:
        return JsonResponse({
            'success': True,
            'models': AVAILABLE_MODELS,
            'default_model': DEFAULT_MODEL
        })
    except Exception as e:
        logger.error(f"获取LLM模型列表失败: {str(e)}")
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
        model = data.get('model', DEFAULT_MODEL)
        record_id = data.get('record_id')
        detection_data = data.get('detection_data', {})
        stream = data.get('stream', False)  # 是否启用流式输出

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

        # 如果启用流式输出
        if stream:
            return stream_llm_analysis(model, analysis_context, record_id)

        # 传统的一次性输出
        analysis_result = call_llm_api(model, analysis_context)

        if analysis_result['success']:
            # 记录分析日志
            model_used = analysis_result.get('model_used', model)
            api_provider = analysis_result.get('api_provider', 'SiliconFlow')
            logger.info(f"LLM分析成功 - 记录ID: {record_id}, 请求模型: {model}, 实际使用模型: {model_used}")

            return JsonResponse({
                'success': True,
                'analysis': analysis_result['content'],
                'model_used': model_used,
                'api_provider': api_provider,
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


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_llm_analysis_stream(request):
    """API: 大模型流式分析接口"""
    try:
        # 解析请求数据
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        model = data.get('model', DEFAULT_MODEL)
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

        # 返回流式响应
        return stream_llm_analysis(model, analysis_context, record_id)

    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误'}, status=400)
    except Exception as e:
        logger.error(f"流式LLM分析失败: {str(e)}")
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


def stream_llm_analysis(model, prompt, record_id):
    """流式输出大模型分析"""
    from django.http import StreamingHttpResponse
    import json
    import time

    def generate_stream():
        try:
            # 验证模型是否在可用列表中
            available_model_values = [m['value'] for m in AVAILABLE_MODELS]
            if model not in available_model_values:
                actual_model = DEFAULT_MODEL
            else:
                actual_model = model

            # 构建API请求（启用流式输出）
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
                "temperature": SILICONFLOW_CONFIG['temperature'],
                "stream": True  # 启用流式输出
            }

            headers = {
                "Authorization": f"Bearer {SILICONFLOW_CONFIG['api_key']}",
                "Content-Type": "application/json"
            }

            # 发送流式请求
            logger.info(f"调用SiliconFlow 流式API - 模型: {actual_model}")

            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'model': actual_model, 'timestamp': time.time()})}\n\n"

            response = requests.post(
                SILICONFLOW_CONFIG['base_url'],
                json=payload,
                headers=headers,
                timeout=SILICONFLOW_CONFIG['timeout'],
                stream=True
            )

            if response.status_code == 200:
                # 处理流式响应
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # 移除 'data: ' 前缀

                            if data_str.strip() == '[DONE]':
                                # 流式输出结束
                                yield f"data: {json.dumps({'type': 'done', 'timestamp': time.time()})}\n\n"
                                break

                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        # 发送内容片段
                                        yield f"data: {json.dumps({'type': 'content', 'content': content, 'timestamp': time.time()})}\n\n"
                            except json.JSONDecodeError:
                                continue
            else:
                # 流式API调用失败，发送错误事件
                error_msg = f'API调用失败 (状态码: {response.status_code}): {response.text}'
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg, 'timestamp': time.time()})}\n\n"

        except Exception as e:
            logger.error(f"流式LLM分析失败: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': time.time()})}\n\n"

    response = StreamingHttpResponse(generate_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    return response


def call_llm_api(model, prompt):
    """调用大模型API"""
    try:
        # 验证模型是否在可用列表中
        available_model_values = [m['value'] for m in AVAILABLE_MODELS]
        logger.info(f"请求的模型: {model}, 可用模型: {available_model_values}")
        if model not in available_model_values:
            logger.warning(f"模型 {model} 不在可用列表中，使用默认模型: {DEFAULT_MODEL}")
            model = DEFAULT_MODEL

        actual_model = model
        logger.info(f"实际使用的模型: {actual_model}")

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

                # 记录响应信息用于调试
                choice = response_data['choices'][0]
                finish_reason = choice.get('finish_reason', 'unknown')
                content_length = len(analysis_content) if analysis_content else 0

                logger.info(f"SiliconFlow API调用成功 - 模型: {actual_model}")
                logger.info(f"响应长度: {content_length} 字符, 结束原因: {finish_reason}")

                # 如果因为长度限制而截断，记录警告
                if finish_reason == 'length':
                    logger.warning(f"AI回答因长度限制被截断 - 当前max_tokens: {SILICONFLOW_CONFIG['max_tokens']}")

                return {
                    'success': True,
                    'content': analysis_content,
                    'model_used': actual_model,
                    'api_provider': 'SiliconFlow',
                    'finish_reason': finish_reason,
                    'content_length': content_length
                }
            else:
                logger.error(f"SiliconFlow API响应格式错误: {response_data}")
                return {
                    'success': False,
                    'error': 'API响应格式错误'
                }
        else:
            # API调用失败，直接返回错误
            logger.error(f"SiliconFlow API调用失败 (状态码: {response.status_code})")
            logger.error(f"错误响应: {response.text}")

            return {
                'success': False,
                'error': f'API调用失败 (状态码: {response.status_code}): {response.text}'
            }

    except requests.exceptions.Timeout:
        logger.error("SiliconFlow API调用超时")
        return {
            'success': False,
            'error': 'API调用超时，请稍后重试'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"SiliconFlow API网络错误: {str(e)}")
        return {
            'success': False,
            'error': f'网络连接错误: {str(e)}，请检查网络连接后重试'
        }
    except Exception as e:
        logger.error(f"调用LLM API失败: {str(e)}")
        return {
            'success': False,
            'error': f'API调用异常: {str(e)}，请重试'
        }


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_download_llm_pdf(request):
    """API: 下载LLM分析PDF报告"""
    try:
        # 解析请求数据
        data = json.loads(request.body)
        record_id = data.get('record_id')
        llm_content = data.get('llm_content', '').strip()
        model_used = data.get('model_used')

        if not record_id:
            return JsonResponse({'error': '缺少检测记录ID'}, status=400)

        if not llm_content:
            return JsonResponse({'error': '缺少LLM分析内容'}, status=400)

        # 验证检测记录是否存在且属于当前用户
        try:
            record = DetectionRecord.objects.get(id=record_id, user=request.user)
        except DetectionRecord.DoesNotExist:
            return JsonResponse({'error': '检测记录不存在或无权限访问'}, status=404)

        # 生成PDF
        pdf_service = PDFReportService()
        pdf_data = pdf_service.generate_llm_analysis_pdf(record, llm_content, model_used)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'口罩检测AI分析报告_{record.id}_{timestamp}.pdf'

        # 返回PDF文件
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_data)

        logger.info(f"PDF报告生成成功 - 记录ID: {record_id}, 用户: {request.user.username}")

        return response

    except json.JSONDecodeError:
        return JsonResponse({'error': '请求数据格式错误'}, status=400)
    except Exception as e:
        logger.error(f"PDF报告生成失败: {str(e)}")
        return JsonResponse({'error': f'PDF生成失败: {str(e)}'}, status=500)



