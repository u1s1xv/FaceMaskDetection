# 口罩检测系统 - Django前端

基于Django框架的口罩检测Web前端系统，集成YOLO深度学习模型，提供图片上传、AI检测、结果展示等功能。

## 🎯 功能特性

### 核心功能
- **图片上传**: 支持拖拽上传、点击选择，多种图片格式
- **AI检测**: 集成YOLO模型，检测口罩佩戴情况
- **结果展示**: 美化的检测结果图片和详细统计信息
- **历史记录**: 检测历史查看、搜索、删除功能
- **模型管理**: 多模型支持，参数调节
- **响应式设计**: 支持PC和移动端访问

### 检测类别
- ✅ **正确戴口罩** (with_mask) - 绿色标注
- ❌ **未戴口罩** (without_mask) - 红色标注  
- ⚠️ **错误戴口罩** (mask_weared_incorrect) - 蓝色标注

## 🏗️ 系统架构

```
django_frontend/
├── face_mask_detection/     # Django项目配置
│   ├── settings.py         # 项目设置
│   ├── urls.py            # URL路由
│   └── wsgi.py            # WSGI配置
├── detection/              # 主应用
│   ├── models.py          # 数据模型
│   ├── views.py           # 视图函数
│   ├── forms.py           # 表单定义
│   ├── services.py        # YOLO推理服务
│   ├── api_views.py       # API接口
│   └── admin.py           # 管理后台
├── templates/              # HTML模板
│   ├── base.html          # 基础模板
│   └── detection/         # 检测相关模板
├── static/                 # 静态文件
│   ├── css/               # 样式文件
│   └── js/                # JavaScript文件
├── media/                  # 媒体文件（上传的图片）
├── requirements.txt        # Python依赖
├── setup_django.py        # 项目初始化脚本
└── start_server.py        # 服务器启动脚本
```

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- Django 4.2+
- FMD conda虚拟环境（已配置YOLO相关依赖）

### 2. 安装和启动

#### 方法一：自动启动（推荐）
```bash
# 激活虚拟环境
conda activate FMD

# 进入Django项目目录
cd django_frontend

# 运行启动脚本（自动安装依赖、初始化项目、启动服务器）
python start_server.py
```

#### 方法二：手动安装
```bash
# 激活虚拟环境
conda activate FMD

# 进入Django项目目录
cd django_frontend

# 安装依赖
pip install -r requirements.txt

# 初始化项目
python setup_django.py

# 启动开发服务器
python manage.py runserver
```

### 3. 访问系统
- **主页**: http://127.0.0.1:8000
- **管理后台**: http://127.0.0.1:8000/admin
  - 用户名: `admin`
  - 密码: `admin123`

## 📱 使用指南

### 上传和检测
1. 访问主页，点击或拖拽上传图片
2. 调整检测参数（可选）：
   - 模型选择
   - 置信度阈值
   - IOU阈值
   - 图像尺寸
3. 点击"开始检测"按钮
4. 等待AI处理完成
5. 查看检测结果和统计信息

### 查看历史
1. 点击导航栏"检测历史"
2. 浏览所有检测记录
3. 使用搜索和筛选功能
4. 点击"查看详情"查看完整结果

### 模型管理
1. 将训练好的.pt模型文件放入 `yoloserver/models/checkpoints/` 目录
2. 访问"模型管理"页面查看所有模型状态
3. 系统会自动扫描目录下的模型文件
4. 只有实际存在的模型文件才会出现在检测页面的下拉菜单中
5. 可以在管理后台配置模型的详细信息和描述

## 🔧 配置说明

### 主要配置文件
- `face_mask_detection/settings.py`: Django项目设置
- `detection/services.py`: YOLO推理服务配置

### 重要设置
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
系统会自动扫描 `yoloserver/models/checkpoints/` 目录下的模型文件：

1. **自动发现**: 系统自动扫描.pt文件，无需手动配置
2. **实时更新**: 添加新模型文件后刷新页面即可使用
3. **文件验证**: 只有实际存在的模型文件才能被选择
4. **详细配置**: 在管理后台可以为模型添加描述和性能参数
   - 访问 http://127.0.0.1:8000/admin
   - 进入"模型配置"
   - 添加新模型或编辑现有模型
5. **状态管理**: 在模型管理页面查看所有模型的状态和配置情况

## 🛠️ API接口

### RESTful API端点
- `POST /api/detect/` - 上传图片并检测
- `GET /api/result/<id>/` - 获取检测结果
- `GET /api/models/` - 获取可用模型列表
- `GET /api/history/` - 获取检测历史
- `DELETE /api/delete/<id>/` - 删除检测记录

### API使用示例
```javascript
// 上传图片检测
const formData = new FormData();
formData.append('image', imageFile);
formData.append('model_name', 'yolo11n-seg.pt');
formData.append('confidence', 0.25);

fetch('/api/detect/', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🎨 界面特性

### 响应式设计
- 支持桌面端和移动端
- Bootstrap 5框架
- 现代化UI设计

### 交互功能
- 拖拽上传
- 实时参数验证
- 进度条显示
- 图片预览
- 结果对比展示

## 🔍 故障排除

### 常见问题

1. **YOLO推理失败**
   - 检查yoloserver目录是否存在
   - 确认模型文件路径正确
   - 查看Django日志获取详细错误信息

2. **图片上传失败**
   - 检查文件大小是否超过10MB
   - 确认文件格式是否支持
   - 检查media目录权限

3. **静态文件加载失败**
   - 运行 `python manage.py collectstatic`
   - 检查STATIC_ROOT设置

### 日志查看
```bash
# Django开发服务器日志会直接显示在终端
# 也可以查看具体的日志文件
tail -f logs/django.log
```

## 🔒 安全考虑

- CSRF保护已启用
- 文件类型验证
- 文件大小限制
- 路径遍历防护
- 输入参数验证

## 📈 性能优化

- 异步文件处理
- 图片压缩
- 缓存机制
- 数据库查询优化
- 静态文件CDN支持

## 🤝 开发指南

### 添加新功能
1. 在`detection/models.py`中定义数据模型
2. 在`detection/views.py`中添加视图函数
3. 在`detection/urls.py`中配置URL路由
4. 创建对应的HTML模板
5. 运行数据库迁移

### 自定义样式
- 编辑`static/css/custom.css`
- 修改Bootstrap变量
- 添加自定义JavaScript

## 📞 技术支持

如有问题或建议，请联系开发团队或查看项目文档。

---

**版本**: 1.0.0  
**更新时间**: 2025-07-01  
**技术栈**: Django + Bootstrap + YOLO + OpenCV
