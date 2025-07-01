"""
视图函数
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging

from .models import DetectionRecord, ModelConfig
from .forms import ImageUploadForm, DetectionParametersForm
from .services import YOLOInferenceService

logger = logging.getLogger(__name__)


def index(request):
    """主页视图 - 系统概览"""
    from django.db.models import Sum
    import django
    import sys

    # 获取统计数据
    stats = DetectionRecord.objects.filter(status='completed').aggregate(
        total_detections=Sum('total_detections'),
        with_mask_count=Sum('with_mask_count'),
        without_mask_count=Sum('without_mask_count'),
        incorrect_mask_count=Sum('incorrect_mask_count')
    )

    # 处理空值
    for key, value in stats.items():
        if value is None:
            stats[key] = 0

    # 获取最近检测记录
    recent_records = DetectionRecord.objects.filter(
        status='completed'
    ).order_by('-upload_time')[:6]

    context = {
        'stats': stats,
        'recent_records': recent_records,
        'page_title': '口罩检测系统 - 首页',
        'django_version': django.get_version(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    return render(request, 'detection/index.html', context)


def detect(request):
    """检测页面视图"""
    form = ImageUploadForm()
    recent_records = DetectionRecord.objects.filter(
        status='completed'
    ).order_by('-upload_time')[:5]

    context = {
        'form': form,
        'recent_records': recent_records,
        'page_title': '图片检测'
    }
    return render(request, 'detection/detect.html', context)


def upload_and_detect(request):
    """上传图片并进行检测"""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # 保存记录
                record = form.save(commit=False)
                record.status = 'pending'
                record.save()
                
                # 执行检测
                inference_service = YOLOInferenceService()
                result = inference_service.run_inference(
                    image_path=record.original_image.path,
                    model_name=record.model_name,
                    confidence=record.confidence_threshold,
                    iou=record.iou_threshold,
                    imgsz=record.image_size
                )
                
                # 更新记录
                record.status = 'processing'
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
                
                record.status = 'completed'
                record.save()
                
                messages.success(request, '检测完成！')
                return redirect('detection_result', record_id=record.id)
                
            except Exception as e:
                logger.error(f"检测失败: {str(e)}")
                if 'record' in locals():
                    record.status = 'failed'
                    record.error_message = str(e)
                    record.save()
                messages.error(request, f'检测失败: {str(e)}')
                return redirect('index')
        else:
            messages.error(request, '表单验证失败，请检查输入')
    
    return redirect('index')


def detection_result(request, record_id):
    """检测结果页面"""
    record = get_object_or_404(DetectionRecord, id=record_id)
    
    context = {
        'record': record,
        'detection_summary': record.detection_summary,
        'page_title': f'检测结果 #{record.id}'
    }
    return render(request, 'detection/result.html', context)


def history(request):
    """历史记录页面"""
    # 搜索功能
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    records = DetectionRecord.objects.all()
    
    if search_query:
        records = records.filter(
            Q(id__icontains=search_query) |
            Q(model_name__icontains=search_query)
        )
    
    if status_filter:
        records = records.filter(status=status_filter)
    
    records = records.order_by('-upload_time')
    
    # 分页
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': DetectionRecord.STATUS_CHOICES,
        'page_title': '检测历史'
    }
    return render(request, 'detection/history.html', context)


def delete_record(request, record_id):
    """删除检测记录"""
    if request.method == 'POST':
        record = get_object_or_404(DetectionRecord, id=record_id)
        try:
            # 删除相关文件
            if record.original_image:
                record.original_image.delete()
            if record.result_image:
                record.result_image.delete()
            
            record.delete()
            messages.success(request, '记录删除成功')
        except Exception as e:
            logger.error(f"删除记录失败: {str(e)}")
            messages.error(request, '删除失败')
    
    return redirect('history')


def model_management(request):
    """模型管理页面"""
    # 获取数据库中的模型配置
    db_models = ModelConfig.objects.all().order_by('-created_time')

    # 获取实际存在的模型文件
    try:
        inference_service = YOLOInferenceService()
        available_models = inference_service.get_available_models()
    except Exception as e:
        logger.error(f"获取可用模型失败: {str(e)}")
        available_models = []

    # 检查数据库模型与实际文件的匹配情况
    model_status = []
    for db_model in db_models:
        file_exists = any(am['name'] == db_model.name for am in available_models)
        model_status.append({
            'config': db_model,
            'file_exists': file_exists
        })

    # 检查是否有文件但没有数据库配置的模型
    orphan_models = []
    db_model_names = set(db_models.values_list('name', flat=True))
    for available_model in available_models:
        if available_model['name'] not in db_model_names:
            orphan_models.append(available_model)

    # 为每个可用模型添加配置状态信息
    models_with_status = []
    for model in available_models:
        # 查找对应的数据库配置
        db_config = db_models.filter(name=model['name']).first()

        model_info = model.copy()
        if db_config:
            model_info['config_status'] = 'active' if db_config.is_active else 'configured'
            model_info['config'] = db_config
        else:
            model_info['config_status'] = 'unconfigured'
            model_info['config'] = None

        models_with_status.append(model_info)

    # 计算统计数字
    total_files = len(available_models)
    total_configured = len(db_models)
    total_orphan = len(orphan_models)
    total_active = sum(1 for model in models_with_status if model['config_status'] == 'active')

    context = {
        'model_status': model_status,
        'available_models': models_with_status,
        'orphan_models': orphan_models,
        'stats': {
            'total_files': total_files,
            'total_configured': total_configured,
            'total_orphan': total_orphan,
            'total_active': total_active,
        },
        'page_title': '模型管理'
    }
    return render(request, 'detection/models.html', context)


def settings_view(request):
    """设置页面"""
    if request.method == 'POST':
        form = DetectionParametersForm(request.POST)
        if form.is_valid():
            # 保存默认参数到session
            request.session['default_params'] = form.cleaned_data
            messages.success(request, '默认参数已保存')
            return redirect('settings')
    else:
        # 从session加载默认参数
        initial_data = request.session.get('default_params', {})
        form = DetectionParametersForm(initial=initial_data)

    # 获取系统信息
    import django
    import sys

    context = {
        'form': form,
        'page_title': '系统设置',
        'django_version': django.get_version(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    return render(request, 'detection/settings.html', context)


@csrf_exempt
@require_http_methods(["GET"])
def get_detection_status(request, record_id):
    """获取检测状态API"""
    try:
        record = get_object_or_404(DetectionRecord, id=record_id)
        return JsonResponse({
            'status': record.status,
            'progress': 100 if record.status == 'completed' else 50,
            'message': '检测完成' if record.status == 'completed' else '检测中...'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
