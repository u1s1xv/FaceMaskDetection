# 🖼️ 多图片批量检测功能设计文档

## 📋 项目概述

为人脸口罩检测系统添加多图片批量上传、检测和分析功能，提升用户体验和工作效率。

## 🎯 功能需求分析

### 1. 核心功能需求

#### 1.1 多图片上传
- **批量选择**：支持一次选择多张图片（最多20张）
- **拖拽上传**：支持多文件拖拽到上传区域
- **文件验证**：统一的文件格式、大小验证
- **预览管理**：多图片缩略图预览和管理

#### 1.2 批量检测处理
- **队列处理**：按顺序处理多张图片
- **进度跟踪**：实时显示整体和单张图片处理进度
- **并发控制**：合理控制并发数量避免系统过载
- **错误处理**：单张图片失败不影响其他图片处理

#### 1.3 批量结果展示
- **统计汇总**：多图片检测结果的统计分析
- **结果对比**：支持多图片结果的对比查看
- **批量操作**：支持批量下载、删除等操作
- **AI分析**：支持对批量结果进行综合AI分析

## 🏗️ 技术架构设计

### 2. 数据库模型设计

#### 2.1 新增批量检测会话模型
```python
class BatchDetectionSession(models.Model):
    """批量检测会话模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_name = models.CharField(max_length=200, default="批量检测")
    created_time = models.DateTimeField(auto_now_add=True)
    total_images = models.IntegerField(default=0)
    completed_images = models.IntegerField(default=0)
    failed_images = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # 统一的检测参数
    model_name = models.CharField(max_length=100)
    confidence_threshold = models.FloatField(default=0.25)
    iou_threshold = models.FloatField(default=0.45)
    image_size = models.IntegerField(default=640)
```

#### 2.2 扩展检测记录模型
```python
class DetectionRecord(models.Model):
    # 新增字段
    batch_session = models.ForeignKey(
        BatchDetectionSession, 
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="批量检测会话"
    )
    batch_index = models.IntegerField(
        null=True, blank=True,
        verbose_name="批次内序号"
    )
    is_batch_detection = models.BooleanField(
        default=False,
        verbose_name="是否为批量检测"
    )
```

### 3. 前端界面设计

#### 3.1 检测页面改进
```html
<!-- 上传模式切换 -->
<div class="upload-mode-selector mb-3">
    <div class="btn-group" role="group">
        <input type="radio" class="btn-check" name="uploadMode" id="singleMode" value="single" checked>
        <label class="btn btn-outline-primary" for="singleMode">
            <i class="fas fa-image"></i> 单张检测
        </label>
        <input type="radio" class="btn-check" name="uploadMode" id="batchMode" value="batch">
        <label class="btn btn-outline-primary" for="batchMode">
            <i class="fas fa-images"></i> 批量检测
        </label>
    </div>
</div>

<!-- 批量上传区域 -->
<div id="batchUploadArea" class="upload-area-batch" style="display: none;">
    <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
    <h5>拖拽多张图片到此处或点击选择文件</h5>
    <p class="text-muted">支持同时选择多张图片，最多20张，每张最大10MB</p>
    <input type="file" id="batchImageInput" multiple accept="image/*" style="display: none;">
</div>

<!-- 多图片预览区域 -->
<div id="batchPreviewArea" class="batch-preview-container">
    <div class="preview-header">
        <h6>已选择图片 (<span id="selectedCount">0</span>/20)</h6>
        <button type="button" class="btn btn-sm btn-outline-danger" id="clearAllBtn">
            <i class="fas fa-trash"></i> 清空所有
        </button>
    </div>
    <div class="preview-grid" id="previewGrid">
        <!-- 动态生成预览项 -->
    </div>
</div>
```

#### 3.2 批量进度显示
```html
<!-- 批量处理进度 -->
<div id="batchProgressArea" class="batch-progress-container" style="display: none;">
    <div class="overall-progress mb-3">
        <div class="d-flex justify-content-between mb-2">
            <span>整体进度</span>
            <span id="overallProgressText">0/0</span>
        </div>
        <div class="progress">
            <div class="progress-bar" id="overallProgressBar" style="width: 0%"></div>
        </div>
    </div>
    
    <div class="individual-progress">
        <h6>处理详情</h6>
        <div id="individualProgressList">
            <!-- 动态生成单张图片进度 -->
        </div>
    </div>
</div>
```

### 4. 后端API设计

#### 4.1 批量检测API
```python
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_batch_upload_detect(request):
    """API: 批量上传图片并检测"""
    try:
        # 获取上传的多个文件
        images = request.FILES.getlist('images')
        if not images:
            return JsonResponse({'error': '没有上传图片'}, status=400)
        
        if len(images) > 20:
            return JsonResponse({'error': '最多支持20张图片'}, status=400)
        
        # 创建批量检测会话
        session = BatchDetectionSession.objects.create(
            user=request.user,
            session_name=request.POST.get('session_name', f'批量检测_{timezone.now().strftime("%Y%m%d_%H%M%S")}'),
            total_images=len(images),
            model_name=request.POST.get('model_name', 'yolo11n-seg.pt'),
            confidence_threshold=float(request.POST.get('confidence', 0.25)),
            iou_threshold=float(request.POST.get('iou', 0.45)),
            image_size=int(request.POST.get('imgsz', 640)),
            status='pending'
        )
        
        # 创建检测记录
        records = []
        for idx, image in enumerate(images):
            record = DetectionRecord.objects.create(
                user=request.user,
                batch_session=session,
                batch_index=idx,
                is_batch_detection=True,
                original_image=image,
                model_name=session.model_name,
                confidence_threshold=session.confidence_threshold,
                iou_threshold=session.iou_threshold,
                image_size=session.image_size,
                status='pending'
            )
            records.append(record)
        
        # 启动异步批量处理
        process_batch_detection.delay(session.id)
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'total_images': len(images),
            'message': '批量检测已开始'
        })
        
    except Exception as e:
        logger.error(f"批量检测失败: {str(e)}")
        return JsonResponse({'error': f'批量检测失败: {str(e)}'}, status=500)
```

#### 4.2 批量进度查询API
```python
@login_required
@require_http_methods(["GET"])
def api_batch_progress(request, session_id):
    """API: 查询批量检测进度"""
    try:
        session = get_object_or_404(BatchDetectionSession, id=session_id, user=request.user)
        
        # 获取所有记录的状态
        records = DetectionRecord.objects.filter(
            batch_session=session
        ).order_by('batch_index')
        
        progress_data = {
            'session_id': session.id,
            'session_name': session.session_name,
            'total_images': session.total_images,
            'completed_images': session.completed_images,
            'failed_images': session.failed_images,
            'status': session.status,
            'overall_progress': (session.completed_images + session.failed_images) / session.total_images * 100,
            'records': []
        }
        
        for record in records:
            progress_data['records'].append({
                'id': record.id,
                'batch_index': record.batch_index,
                'filename': record.original_image.name.split('/')[-1],
                'status': record.status,
                'error_message': record.error_message,
                'processing_time': record.processing_time,
                'total_detections': record.total_detections
            })
        
        return JsonResponse(progress_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

### 5. 异步处理设计

#### 5.1 Celery任务配置
```python
from celery import shared_task
from django.utils import timezone

@shared_task
def process_batch_detection(session_id):
    """异步处理批量检测任务"""
    try:
        session = BatchDetectionSession.objects.get(id=session_id)
        session.status = 'processing'
        session.save()
        
        records = DetectionRecord.objects.filter(
            batch_session=session,
            status='pending'
        ).order_by('batch_index')
        
        inference_service = YOLOInferenceService()
        
        for record in records:
            try:
                # 更新记录状态
                record.status = 'processing'
                record.save()
                
                # 执行检测
                result = inference_service.run_inference(
                    image_path=record.original_image.path,
                    model_name=record.model_name,
                    confidence=record.confidence_threshold,
                    iou=record.iou_threshold,
                    imgsz=record.image_size
                )
                
                # 更新检测结果
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
                            f'batch_result_{record.id}.png',
                            result_image,
                            save=False
                        )
                
                record.save()
                
                # 更新会话统计
                session.completed_images += 1
                session.save()
                
            except Exception as e:
                logger.error(f"批量检测单张图片失败 (记录ID: {record.id}): {str(e)}")
                record.status = 'failed'
                record.error_message = str(e)
                record.save()
                
                session.failed_images += 1
                session.save()
        
        # 更新会话最终状态
        if session.failed_images == 0:
            session.status = 'completed'
        elif session.completed_images == 0:
            session.status = 'failed'
        else:
            session.status = 'partial_completed'
        
        session.save()
        
    except Exception as e:
        logger.error(f"批量检测任务失败 (会话ID: {session_id}): {str(e)}")
        try:
            session = BatchDetectionSession.objects.get(id=session_id)
            session.status = 'failed'
            session.save()
        except:
            pass
```

## 📊 用户体验设计

### 6. 交互流程设计

#### 6.1 批量上传流程
1. **模式选择**：用户选择"批量检测"模式
2. **文件选择**：支持拖拽或点击选择多个文件
3. **预览管理**：显示选中文件的缩略图，支持单独删除
4. **参数设置**：统一设置检测参数
5. **开始检测**：提交批量检测任务

#### 6.2 进度监控流程
1. **任务提交**：显示任务已提交的确认信息
2. **实时进度**：通过轮询API更新进度信息
3. **状态展示**：显示每张图片的处理状态
4. **错误处理**：显示失败图片的错误信息
5. **完成通知**：处理完成后的通知和跳转

#### 6.3 结果查看流程
1. **批量结果页**：展示所有图片的检测结果
2. **统计汇总**：显示整体统计数据
3. **单独查看**：支持查看单张图片的详细结果
4. **批量操作**：支持批量下载、删除等操作

### 7. 性能优化策略

#### 7.1 前端优化
- **图片压缩**：上传前对大图片进行适当压缩
- **分页加载**：结果页面支持分页显示
- **懒加载**：图片预览采用懒加载策略
- **缓存机制**：合理缓存检测结果

#### 7.2 后端优化
- **队列管理**：使用Celery进行异步任务处理
- **并发控制**：限制同时处理的图片数量
- **资源管理**：及时清理临时文件
- **数据库优化**：优化查询和索引

## 🔧 实施计划

### 8. 开发阶段划分

#### 阶段1：数据库模型扩展
- 创建BatchDetectionSession模型
- 扩展DetectionRecord模型
- 数据库迁移和测试

#### 阶段2：前端界面改进
- 修改检测页面支持模式切换
- 实现多图片选择和预览
- 添加批量进度显示组件

#### 阶段3：后端API开发
- 开发批量检测API
- 实现进度查询API
- 集成异步任务处理

#### 阶段4：结果展示优化
- 设计批量结果展示页面
- 实现统计分析功能
- 添加批量操作功能

#### 阶段5：测试与优化
- 功能测试和性能测试
- 用户体验优化
- 文档完善

## 📋 技术要点总结

1. **保持兼容性**：新功能不影响现有单图片检测功能
2. **用户体验**：提供直观的进度反馈和错误处理
3. **性能考虑**：合理控制并发和资源使用
4. **扩展性**：设计支持未来功能扩展的架构
5. **安全性**：保持现有的用户认证和数据隔离机制

这个设计文档为多图片批量检测功能提供了完整的技术方案，确保在现有系统基础上平滑扩展新功能。
