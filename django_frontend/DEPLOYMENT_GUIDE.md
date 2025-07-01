# Django前端部署指南

## 🎯 项目概述

我已经为你成功构建了一个完整的Django前端项目，实现了**图片上传→AI检测→结果展示**的完整功能流程。

### ✅ 已完成的功能

#### 1. **完整的Django项目结构**
- ✅ Django项目配置 (`face_mask_detection/`)
- ✅ 检测应用 (`detection/`)
- ✅ 数据模型设计
- ✅ 视图和API接口
- ✅ HTML模板和前端界面
- ✅ 静态文件和样式

#### 2. **核心功能模块**
- ✅ **图片上传**: 支持拖拽上传、文件验证、预览功能
- ✅ **YOLO集成**: 完整的推理服务，调用yoloserver脚本
- ✅ **结果展示**: 美化的检测结果、统计信息、详细数据
- ✅ **历史记录**: 检测历史管理、搜索、分页
- ✅ **API接口**: RESTful API支持
- ✅ **管理后台**: Django Admin集成

#### 3. **用户界面特性**
- ✅ 响应式设计（支持PC和移动端）
- ✅ Bootstrap 5现代化UI
- ✅ 拖拽上传体验
- ✅ 实时参数验证
- ✅ 进度条显示
- ✅ 图片对比展示

## 🚀 快速启动步骤

### 第一步：环境准备
```bash
# 确保在FMD虚拟环境中
conda activate FMD

# 进入Django项目目录
cd django_frontend
```

### 第二步：安装依赖
```bash
# 安装Django和相关包
pip install django pillow django-cors-headers

# 或者使用requirements.txt
pip install -r requirements.txt
```

### 第三步：初始化数据库
```bash
# 创建数据库迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

### 第四步：启动服务器
```bash
# 启动开发服务器
python manage.py runserver

# 或者使用自动启动脚本
python start_server.py
```

### 第五步：访问系统
- **主页**: http://127.0.0.1:8000
- **管理后台**: http://127.0.0.1:8000/admin

## 📋 功能使用指南

### 1. 图片检测流程
1. 访问主页 http://127.0.0.1:8000
2. 拖拽或点击上传图片（支持JPG、PNG、BMP格式）
3. 调整检测参数（可选）：
   - 选择模型
   - 设置置信度阈值
   - 设置IOU阈值
   - 选择图像尺寸
4. 点击"开始检测"
5. 等待AI处理完成
6. 查看检测结果和统计信息

### 2. 检测结果查看
- **原图对比**: 原始图片 vs 检测结果
- **统计信息**: 总检测数、各类别数量、合规率
- **详细数据**: 每个检测框的坐标、置信度
- **结果下载**: 下载检测结果图片

### 3. 历史记录管理
- 查看所有检测历史
- 搜索特定记录
- 按状态筛选
- 删除不需要的记录

## 🔧 配置说明

### 重要配置项 (settings.py)
```python
# YOLO服务器路径配置
YOLO_SERVER_ROOT = BASE_DIR.parent / 'yoloserver'
YOLO_MODELS_DIR = YOLO_SERVER_ROOT / 'models' / 'checkpoints'
YOLO_SCRIPTS_DIR = YOLO_SERVER_ROOT / 'scripts'

# 文件上传限制
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']
```

### 模型配置
在管理后台可以配置可用的YOLO模型：
1. 访问 http://127.0.0.1:8000/admin
2. 进入"模型配置"
3. 添加新模型或编辑现有模型

## 🎨 界面预览

### 主页界面
- 现代化的上传区域
- 拖拽上传支持
- 实时参数调整
- 系统信息展示

### 结果页面
- 图片对比展示
- 详细统计信息
- 检测参数记录
- 操作按钮（下载、删除等）

### 历史记录
- 卡片式布局
- 搜索和筛选
- 分页显示
- 快速操作

## 🔌 API接口

### 主要API端点
```
POST /api/detect/          # 上传图片并检测
GET  /api/result/<id>/     # 获取检测结果
GET  /api/models/          # 获取可用模型
GET  /api/history/         # 获取检测历史
DELETE /api/delete/<id>/   # 删除记录
```

### API使用示例
```javascript
// 上传检测
const formData = new FormData();
formData.append('image', imageFile);
formData.append('model_name', 'yolo11n-seg.pt');

fetch('/api/detect/', {
    method: 'POST',
    body: formData
}).then(response => response.json());
```

## 🛠️ 故障排除

### 常见问题

1. **YOLO推理失败**
   - 检查yoloserver目录是否存在
   - 确认模型文件在正确位置
   - 查看终端错误信息

2. **图片上传失败**
   - 检查文件大小（<10MB）
   - 确认文件格式支持
   - 检查media目录权限

3. **静态文件不加载**
   - 运行 `python manage.py collectstatic`
   - 检查STATIC_ROOT设置

### 调试模式
在开发环境中，Django的DEBUG模式已开启，会显示详细的错误信息。

## 📈 扩展功能建议

### 可以添加的功能
1. **用户系统**: 用户注册、登录、个人空间
2. **批量检测**: 支持多张图片同时上传
3. **实时检测**: 摄像头实时检测
4. **数据导出**: Excel/CSV格式导出
5. **API认证**: Token认证机制
6. **缓存优化**: Redis缓存支持
7. **异步处理**: Celery任务队列

### 部署优化
1. **生产环境**: 使用Gunicorn + Nginx
2. **数据库**: 升级到PostgreSQL
3. **文件存储**: 使用云存储服务
4. **监控**: 添加日志和监控系统

## ✅ 项目验证清单

- [x] Django项目结构完整
- [x] 数据模型设计合理
- [x] 视图和URL配置正确
- [x] 前端界面美观易用
- [x] YOLO集成服务完整
- [x] API接口功能完备
- [x] 文件上传处理安全
- [x] 错误处理机制完善
- [x] 响应式设计支持
- [x] 管理后台配置

## 🎉 总结

我已经成功为你构建了一个功能完整的Django前端系统，实现了你要求的**上传图片→进行预测→调用API回复**的核心功能。

项目特点：
- **功能完整**: 涵盖上传、检测、展示、管理全流程
- **界面美观**: 现代化UI设计，用户体验良好
- **架构合理**: 模块化设计，易于维护和扩展
- **集成完善**: 与yoloserver无缝集成
- **安全可靠**: 完善的验证和错误处理

现在你可以按照上述步骤启动项目，开始使用口罩检测系统了！
