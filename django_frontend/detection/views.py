"""
视图函数
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
import json
import logging

from .models import DetectionRecord, ModelConfig, BatchDetectionSession
from .forms import ImageUploadForm, DetectionParametersForm
from .services import YOLOInferenceService

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """主页视图 - 系统概览"""
    import django
    import sys

    # 根据用户权限获取数据
    if request.user.is_superuser:
        # 管理员可以查看所有数据，但默认显示自己的数据
        show_all = request.GET.get('show_all', 'false') == 'true'
        if show_all:
            queryset = DetectionRecord.objects.filter(status='completed')
            stats_label = "全站统计"
        else:
            queryset = DetectionRecord.objects.filter(user=request.user, status='completed')
            stats_label = "我的统计"
    else:
        # 普通用户只能查看自己的数据
        queryset = DetectionRecord.objects.filter(user=request.user, status='completed')
        stats_label = "我的统计"
        show_all = False

    # 获取统计数据
    stats = queryset.aggregate(
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
    recent_records = queryset.order_by('-upload_time')[:6]

    context = {
        'stats': stats,
        'stats_label': stats_label,
        'recent_records': recent_records,
        'page_title': '口罩检测系统 - 首页',
        'django_version': django.get_version(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'is_superuser': request.user.is_superuser,
        'show_all': show_all,
    }
    return render(request, 'detection/index.html', context)


@login_required
def detect(request):
    """检测页面视图"""
    # 从session获取默认参数
    default_params = request.session.get('default_params', {})

    # 使用默认参数初始化表单
    form = ImageUploadForm(initial=default_params)

    # 只显示当前用户的最近检测记录
    recent_records = DetectionRecord.objects.filter(
        user=request.user,
        status='completed'
    ).order_by('-upload_time')[:5]

    # 获取可用的模型列表用于批量检测
    available_models = _get_available_models()

    context = {
        'form': form,
        'recent_records': recent_records,
        'available_models': available_models,
        'page_title': '图片检测'
    }
    return render(request, 'detection/detect.html', context)


@login_required
def upload_and_detect(request):
    """上传图片并进行检测"""
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # 保存记录，关联当前用户
                record = form.save(commit=False)
                record.user = request.user  # 关联当前用户
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


@login_required
def detection_result(request, record_id):
    """检测结果页面"""
    # 确保用户只能查看自己的检测记录，除非是管理员
    if request.user.is_superuser:
        record = get_object_or_404(DetectionRecord, id=record_id)
    else:
        record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)

    context = {
        'record': record,
        'detection_summary': record.detection_summary,
        'page_title': f'检测结果 #{record.id}'
    }
    return render(request, 'detection/result.html', context)


@login_required
def history(request):
    """历史记录页面"""
    # 搜索功能
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # 根据用户权限获取数据
    if request.user.is_superuser:
        show_all = request.GET.get('show_all', 'false') == 'true'
        if show_all:
            records = DetectionRecord.objects.all()
            page_title = '检测历史 - 全站数据'
        else:
            records = DetectionRecord.objects.filter(user=request.user)
            page_title = '检测历史 - 我的数据'
    else:
        records = DetectionRecord.objects.filter(user=request.user)
        page_title = '检测历史'
        show_all = False

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
        'page_title': page_title,
        'is_superuser': request.user.is_superuser,
        'show_all': show_all,
    }
    return render(request, 'detection/history.html', context)


@login_required
def delete_record(request, record_id):
    """删除检测记录"""
    if request.method == 'POST':
        # 确保用户只能删除自己的记录，除非是管理员
        if request.user.is_superuser:
            record = get_object_or_404(DetectionRecord, id=record_id)
        else:
            record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)

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


@login_required
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


@login_required
def settings_view(request):
    """设置页面"""
    if request.method == 'POST':
        form = DetectionParametersForm(request.POST)
        if form.is_valid():
            # 保存默认参数到session
            request.session['default_params'] = form.cleaned_data
            messages.success(request, '默认参数已保存')
            return redirect('settings_view')
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


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_detection_status(request, record_id):
    """获取检测状态API"""
    try:
        # 确保用户只能查看自己的记录状态，除非是管理员
        if request.user.is_superuser:
            record = get_object_or_404(DetectionRecord, id=record_id)
        else:
            record = get_object_or_404(DetectionRecord, id=record_id, user=request.user)

        return JsonResponse({
            'status': record.status,
            'progress': 100 if record.status == 'completed' else 50,
            'message': '检测完成' if record.status == 'completed' else '检测中...'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def batch_result(request, session_id):
    """批量检测结果页面"""
    # 确保用户只能查看自己的批量检测会话，除非是管理员
    if request.user.is_superuser:
        session = get_object_or_404(BatchDetectionSession, id=session_id)
    else:
        session = get_object_or_404(BatchDetectionSession, id=session_id, user=request.user)

    # 获取所有检测记录
    records = DetectionRecord.objects.filter(
        batch_session=session
    ).order_by('batch_index')

    # 分页处理
    paginator = Paginator(records, 12)  # 每页显示12个结果
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 计算统计数据
    completed_records = records.filter(status='completed')
    batch_stats = {
        'total_images': session.total_images,
        'completed_images': session.completed_images,
        'failed_images': session.failed_images,
        'success_rate': session.success_rate,
        'total_detections': sum(record.total_detections for record in completed_records),
        'total_with_mask': sum(record.with_mask_count for record in completed_records),
        'total_without_mask': sum(record.without_mask_count for record in completed_records),
        'total_incorrect_mask': sum(record.incorrect_mask_count for record in completed_records),
    }

    # 计算整体合规率
    if batch_stats['total_detections'] > 0:
        batch_stats['overall_compliance_rate'] = round(
            (batch_stats['total_with_mask'] / batch_stats['total_detections'] * 100), 2
        )
    else:
        batch_stats['overall_compliance_rate'] = 0

    context = {
        'session': session,
        'page_obj': page_obj,
        'batch_stats': batch_stats,
        'page_title': f'批量检测结果 - {session.session_name}'
    }

    return render(request, 'detection/batch_result.html', context)


@login_required
def batch_history(request):
    """批量检测历史页面"""
    # 根据用户权限获取数据
    if request.user.is_superuser:
        # 管理员可以查看所有数据，但默认显示自己的数据
        show_all = request.GET.get('show_all') == 'true'
        if show_all:
            queryset = BatchDetectionSession.objects.all()
            stats_label = "全站数据"
        else:
            queryset = BatchDetectionSession.objects.filter(user=request.user)
            stats_label = "我的数据"
    else:
        # 普通用户只能看到自己的数据
        queryset = BatchDetectionSession.objects.filter(user=request.user)
        stats_label = "我的数据"
        show_all = False

    # 搜索和筛选
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')

    if search_query:
        queryset = queryset.filter(
            Q(session_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # 分页
    paginator = Paginator(queryset.order_by('-created_time'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 状态选择
    status_choices = BatchDetectionSession.STATUS_CHOICES

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': status_choices,
        'stats_label': stats_label,
        'is_superuser': request.user.is_superuser,
        'show_all': show_all,
        'page_title': '批量检测历史'
    }

    return render(request, 'detection/batch_history.html', context)


def _get_available_models():
    """获取实际存在的模型文件 - 与表单逻辑保持一致"""
    from django.conf import settings
    from pathlib import Path

    model_choices = []
    models_dir = settings.YOLO_MODELS_DIR  # 指向 yoloserver/models/checkpoints

    if models_dir.exists():
        # 扫描checkpoints目录下的.pt文件
        for model_file in models_dir.glob('*.pt'):
            model_name = model_file.name

            # 尝试从数据库获取模型描述
            try:
                model_config = ModelConfig.objects.filter(
                    name=model_name,
                    is_active=True
                ).first()

                if model_config:
                    description = model_config.description
                else:
                    # 根据文件名生成描述
                    description = _generate_model_description(model_name)

                model_choices.append({
                    'name': model_name,
                    'description': description,
                    'display_name': f"{model_name} - {description}"
                })

            except Exception:
                # 如果数据库查询失败，使用默认描述
                description = _generate_model_description(model_name)
                model_choices.append({
                    'name': model_name,
                    'description': description,
                    'display_name': f"{model_name} - {description}"
                })

    # 如果没有找到任何模型文件，提供默认选项
    if not model_choices:
        model_choices = [{
            'name': 'yolo11n-seg.pt',
            'description': '默认模型（请确保文件存在）',
            'display_name': 'YOLO11n-seg.pt - 默认模型（请确保文件存在）'
        }]

    # 按文件名排序
    model_choices.sort(key=lambda x: x['name'])
    return model_choices


def _generate_model_description(model_name):
    """根据模型文件名生成描述"""
    name_lower = model_name.lower()

    if 'yolo11n' in name_lower:
        return 'YOLO11 Nano - 快速检测'
    elif 'yolo11s' in name_lower:
        return 'YOLO11 Small - 平衡性能'
    elif 'yolo11m' in name_lower:
        return 'YOLO11 Medium - 高精度'
    elif 'yolo11l' in name_lower:
        return 'YOLO11 Large - 超高精度'
    elif 'yolo11x' in name_lower:
        return 'YOLO11 XLarge - 最高精度'
    elif 'seg' in name_lower:
        return '分割模型'
    elif 'det' in name_lower:
        return '检测模型'
    else:
        return '自定义模型'
