"""
API视图
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
import json
import logging

from .models import DetectionRecord, ModelConfig
from .services import YOLOInferenceService

logger = logging.getLogger(__name__)


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
        
        # 创建检测记录
        record = DetectionRecord.objects.create(
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


@require_http_methods(["GET"])
def api_get_result(request, record_id):
    """API: 获取检测结果"""
    try:
        record = get_object_or_404(DetectionRecord, id=record_id)
        
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


@require_http_methods(["GET"])
def api_get_history(request):
    """API: 获取检测历史"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        status_filter = request.GET.get('status', '')
        
        records = DetectionRecord.objects.all()
        
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


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_record(request, record_id):
    """API: 删除检测记录"""
    try:
        record = get_object_or_404(DetectionRecord, id=record_id)
        
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
