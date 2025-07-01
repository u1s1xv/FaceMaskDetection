📋 FaceMaskDetection Web Frontend 系统设计文档
=======================

🎯 **项目概述**
--------------
- **项目名称**: FaceMaskDetection Web Frontend  
- **技术栈**: Django + Bootstrap + JavaScript  
- **核心功能**: 图片上传 → YOLO推理 → 结果展示  
- **环境**: FMD conda虚拟环境  

🏗️ **系统架构设计**
----------------

### 1. 核心功能流程
1. 用户上传图片  
2. Django接收处理  
3. 调用YOLO推理  
4. 返回检测结果  
5. 前端展示结果  

### 2. 功能模块设计
#### 📤 文件上传模块
- 支持格式: JPG, PNG, JPEG, BMP  
- 文件大小限制: 最大10MB  
- 上传方式: 拖拽上传 + 点击选择  
- 预览功能: 上传前图片预览  

#### 🤖 AI检测模块
- 模型调用: 集成 `yoloserver/scripts/yolo_infer.py`  
- 检测类别:
  - ✅ 正确戴口罩 (`with_mask`) - 绿色  
  - ❌ 未戴口罩 (`without_mask`) - 红色  
  - ⚠️ 错误戴口罩 (`mask_weared_incorrect`) - 蓝色  
- 可调参数: 置信度阈值、IOU阈值、图像尺寸  

#### 📊 结果展示模块
- 原图展示: 用户上传的原始图片  
- 检测结果: 带标注的检测图片（美化版本）  
- 统计信息: 检测到的人数、各类别数量、置信度  
- 详细数据: 检测框坐标、置信度分数  

#### 📈 增强功能模块
- 历史记录: 保存检测历史，支持查看和删除  
- 批量检测: 支持多张图片同时上传检测  
- 模型管理: 选择不同的训练模型  
- 参数调节: 实时调整检测参数  
- 结果导出: 下载检测结果和统计报告  

🗂️ **数据库设计**
--------------
```python
class DetectionRecord(models.Model):
    # 基本信息
    upload_time = models.DateTimeField(auto_now_add=True)
    original_image = models.ImageField(upload_to='uploads/original/')
    result_image = models.ImageField(upload_to='uploads/results/')
    
    # 检测参数
    model_name = models.CharField(max_length=100)
    confidence_threshold = models.FloatField(default=0.25)
    iou_threshold = models.FloatField(default=0.45)
    image_size = models.IntegerField(default=640)
    
    # 检测结果
    total_detections = models.IntegerField(default=0)
    with_mask_count = models.IntegerField(default=0)
    without_mask_count = models.IntegerField(default=0)
    incorrect_mask_count = models.IntegerField(default=0)
    
    # 详细数据
    detection_details = models.JSONField(default=dict)
    processing_time = models.FloatField(null=True)
```

🎨 **前端界面设计**
--------------

### 主页面布局
- **顶部导航栏**: Logo + 功能菜单  
- **上传区域**: 拖拽上传 + 参数设置  
- **结果展示区**: 原图 + 检测结果 + 统计信息  
- **历史记录**: 侧边栏显示最近检测记录  

### 页面结构
- `/` - 主页（上传和检测）  
- `/history/` - 历史记录页面  
- `/api/detect/` - 检测API接口  
- `/api/models/` - 模型列表API  
- `/settings/` - 参数设置页面  

🔧 **技术实现方案**
--------------

### 后端API设计
| 端点                     | 方法   | 功能说明                   |
|--------------------------|--------|----------------------------|
| `/api/upload/`         | POST   | 文件上传                  |
| `/api/detect/`         | POST   | 执行检测                  |
| `/api/results/<id>/`   | GET    | 获取检测结果              |
| `/api/history/`        | GET    | 获取历史记录              |
| `/api/models/`         | GET    | 获取可用模型列表          |
| `/api/records/<id>/`   | DELETE | 删除记录                  |

### YOLO集成方案
- 创建独立的推理服务模块  
- 异步任务处理（使用Celery或线程）  
- 结果文件管理和清理  
- 错误处理和日志记录  

### 前端交互设计
- Ajax异步请求: 无刷新上传和检测  
- 进度条显示: 检测过程可视化  
- 实时预览: 图片上传即时预览  
- 响应式设计: 支持移动端访问  

📱 **用户体验优化**
--------------

### 性能优化
- 图片压缩和格式转换  
- 缓存机制减少重复计算  
- 异步处理避免页面阻塞  
- 结果文件定期清理  

### 交互优化
- 拖拽上传体验  
- 检测进度实时显示  
- 结果对比查看  
- 一键分享功能  

🔒 **安全考虑**
--------------
- 文件类型验证  
- 文件大小限制  
- 路径遍历防护  
- CSRF保护  
- 文件存储安全  