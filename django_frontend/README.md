# Django Frontend - 口罩检测Web应用

基于Django 4.2+的现代化Web前端，提供完整的口罩检测、AI分析和用户管理功能。

## Django应用概述

Django Frontend是FaceMaskDetection项目的Web前端模块，采用现代化的Web技术栈，为用户提供直观、高效的口罩检测服务。系统集成了YOLO12推理服务和多种大模型API，支持从图像上传到结果分析的完整工作流程。

### 技术栈
- **后端框架**: Django 4.2+
- **前端框架**: Bootstrap 5 + jQuery
- **AI集成**: YOLO12 + SiliconFlow API
- **数据库**: SQLite
- **文件处理**: Pillow + OpenCV
- **PDF生成**: ReportLab

### 核心工作流程
1. **图像上传** → 用户通过Web界面上传图像
2. **参数配置** → 调整检测参数（置信度、IOU阈值等）
3. **YOLO推理** → 调用yoloserver进行目标检测
4. **结果展示** → 显示检测结果和统计信息
5. **AI分析** → 可选的大模型智能分析
6. **结果管理** → 保存历史记录和导出报告

## 功能模块详解

### 检测服务模块
#### 文件上传功能
- **支持格式**: JPG、PNG、JPEG、BMP
- **文件大小限制**: 最大10MB
- **上传方式**: 拖拽上传 + 点击选择
- **预览功能**: 上传前图像预览
- **格式验证**: 严格的文件类型和大小验证

#### AI检测功能
- **模型集成**: 调用 `yoloserver/scripts/yolo_infer.py`
- **检测类别**:
  - **正确戴口罩** (with_mask) - 绿色标注
  - **未戴口罩** (without_mask) - 红色标注
  - **错误戴口罩** (mask_weared_incorrect) - 黄色标注
- **参数配置**: 置信度阈值、IOU阈值、图像尺寸
- **模型选择**: 支持多个训练好的YOLO模型

#### 结果展示功能
- **原图展示**: 用户上传的原始图像
- **检测结果**: 带标注的检测图像（美化版本）
- **统计信息**: 检测到的人数、各类别数量、置信度分布
- **详细数据**: 检测框坐标、置信度分数、类别信息

### AI分析模块
#### 大模型集成
- **SiliconFlow API**: 主要的大模型服务提供商
- **支持模型**:
  - Qwen QwQ-32B（强大的推理模型）
  - Qwen 2.5-7B-Instruct（快速响应）
  - Qwen 2.5-14B-Instruct（平衡性能）
  - DeepSeek V2.5（深度思考模型）

#### 智能分析功能
- **检测结果评估**: 基于检测数据的专业分析
- **合规性分析**: 口罩佩戴合规性评估
- **风险评估**: 潜在风险识别和评估
- **改进建议**: 针对性的改进建议和措施
- **流式输出**: 实时显示分析过程
- **自定义提示**: 支持用户自定义分析提示词

#### 结果处理功能
- **文本复制**: 一键复制分析结果
- **PDF导出**: 生成专业的PDF分析报告
- **格式化显示**: 清晰的文本格式化和排版
- **历史保存**: 分析结果与检测记录关联保存

### 历史记录模块
#### 记录管理功能
- **完整记录**: 保存所有检测历史和分析结果
- **用户隔离**: 每个用户只能访问自己的记录
- **详情查看**: 查看完整的检测结果和分析报告
- **批量操作**: 支持批量删除和导出操作

#### 搜索筛选功能
- **时间筛选**: 按日期范围筛选记录
- **状态筛选**: 按检测状态筛选
- **关键词搜索**: 支持文件名和备注搜索
- **分页显示**: 高效的分页加载机制

### 用户认证模块
#### 多用户支持
- **用户注册**: 完整的用户注册流程
- **用户登录**: 安全的登录验证机制
- **权限管理**: 基于Django的权限系统
- **数据隔离**: 严格的用户数据隔离

#### 安全防护
- **登录保护**: 5次失败后IP锁定30分钟
- **会话管理**: 安全的会话控制和自动过期
- **CSRF保护**: Django内置CSRF防护
- **XSS防护**: 输入验证和输出转义
- **SQL注入防护**: Django ORM防护

### 模型管理模块
#### 模型发现功能
- **自动扫描**: 自动发现yoloserver/models/checkpoints/目录下的模型
- **模型信息**: 显示模型文件名、大小、修改时间
- **状态监控**: 实时显示模型可用状态
- **性能记录**: 记录模型使用情况和性能数据

#### 模型配置功能
- **模型选择**: 支持在不同模型间灵活切换
- **参数配置**: 为不同模型配置最优参数
- **性能对比**: 比较不同模型的检测性能
- **使用统计**: 统计各模型的使用频率和效果

## 项目结构

### Django应用架构
```
django_frontend/
├── face_mask_detection/          # Django项目配置
│   ├── __init__.py
│   ├── settings.py              # 项目设置和配置
│   ├── urls.py                  # 主URL路由配置
│   ├── wsgi.py                  # WSGI部署配置
│   └── asgi.py                  # ASGI异步配置
│
├── detection/                   # 主应用模块
│   ├── __init__.py
│   ├── models.py               # 数据模型定义
│   ├── views.py                # 视图函数
│   ├── api_views.py            # API接口（含大模型API）
│   ├── services.py             # YOLO推理服务
│   ├── forms.py                # 表单定义
│   ├── urls.py                 # 应用URL路由
│   ├── admin.py                # Django管理后台
│   ├── apps.py                 # 应用配置
│   ├── tests.py                # 单元测试
│   ├── migrations/             # 数据库迁移文件
│   └── management/             # 自定义管理命令
│       └── commands/
│           └── setup_auth.py   # 用户认证设置命令
│
├── templates/                  # HTML模板文件
│   ├── base.html              # 基础模板
│   ├── registration/          # 用户认证模板
│   │   ├── login.html         # 登录页面
│   │   ├── register.html      # 注册页面
│   │   └── logout.html        # 登出页面
│   └── detection/             # 检测相关模板
│       ├── index.html         # 主页（检测界面）
│       ├── result.html        # 结果页（含AI分析）
│       ├── history.html       # 历史记录页面
│       ├── models.html        # 模型管理页面
│       └── settings.html      # 系统设置页面
│
├── static/                    # 静态文件
│   ├── css/
│   │   ├── custom.css        # 自定义样式
│   │   └── bootstrap.min.css # Bootstrap样式
│   ├── js/
│   │   ├── detection.js      # 检测功能JavaScript
│   │   ├── llm-analysis.js   # AI分析JavaScript
│   │   └── bootstrap.min.js  # Bootstrap脚本
│   └── images/               # 静态图像资源
│
├── media/                     # 媒体文件目录
│   ├── uploads/              # 用户上传文件
│   ├── results/              # 检测结果图像
│   └── temp/                 # 临时文件
│
├── logs/                      # 日志文件目录
│   ├── django.log            # Django应用日志
│   ├── detection.log         # 检测服务日志
│   └── llm.log               # 大模型API日志
│
├── manage.py                  # Django管理脚本
├── requirements.txt           # Python依赖包列表
├── setup_django.py           # 项目初始化脚本
├── start_server.py           # 服务器启动脚本
├── llm_config.py             # 大模型配置文件
└── README.md                 # 项目文档（本文件）
```

### 核心组件说明

#### Django项目配置 (face_mask_detection/)
- **settings.py**: 项目核心配置，包括数据库、静态文件、安全设置
- **urls.py**: 主URL路由配置，定义应用的URL模式
- **wsgi.py**: Web服务器网关接口配置，用于部署

#### 主应用模块 (detection/)
- **models.py**: 定义数据模型（用户、检测记录、模型信息）
- **views.py**: 处理HTTP请求的视图函数
- **api_views.py**: RESTful API接口，包括大模型分析API
- **services.py**: YOLO推理服务的封装和调用
- **forms.py**: Django表单定义，用于数据验证

#### 模板系统 (templates/)
- **base.html**: 基础模板，定义页面布局和通用元素
- **detection/**: 检测相关页面模板
- **registration/**: 用户认证相关页面模板

#### 静态资源 (static/)
- **CSS**: 样式文件，包括自定义样式和第三方框架
- **JavaScript**: 前端交互脚本，包括检测和分析功能
- **Images**: 静态图像资源

## 快速启动指南

### 环境要求
- **Python**: 3.8+
- **Django**: 4.2+
- **操作系统**: Windows
- **内存**: 建议4GB以上
- **存储**: 至少1GB可用空间

### 依赖要求
```
Django>=4.2.0
Pillow>=9.0.0
django-cors-headers>=4.0.0
ultralytics>=8.0.0
opencv-python>=4.7.0
numpy>=1.21.0
PyYAML>=6.0
reportlab>=4.0.0
requests>=2.25.1
```

### 一键启动（推荐）
```bash
# 激活conda虚拟环境
conda activate

# 进入Django项目目录
cd django_frontend

# 运行启动脚本（自动安装依赖、初始化项目、启动服务器）
python start_server.py
```

### 手动安装步骤
```bash
# 1. 激活conda虚拟环境
conda activate

# 2. 进入Django项目目录
cd django_frontend

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化项目结构（如果需要）
python setup_django.py

# 5. 创建数据库迁移
python manage.py makemigrations

# 6. 应用迁移
python manage.py migrate

# 7. 设置用户认证系统
python manage.py setup_auth

# 8. 收集静态文件
python manage.py collectstatic --noinput

# 9. 启动开发服务器
python manage.py runserver
```

### 访问系统
启动成功后，通过以下地址访问系统：
- **主页**: http://127.0.0.1:8000/
- **检测页面**: http://127.0.0.1:8000/detect/
- **历史记录**: http://127.0.0.1:8000/history/
- **模型管理**: http://127.0.0.1:8000/models/
- **管理后台**: http://127.0.0.1:8000/admin/

### 默认账户
系统初始化后会创建默认管理员账户：
- **用户名**: admin
- **密码**: admin123

### 验证安装
```bash
# 检查Django版本
python manage.py --version

# 检查数据库连接
python manage.py check

# 运行测试
python manage.py test

# 检查YOLO服务连接
python -c "from detection.services import YOLOInferenceService; print('YOLO服务可用')"
```

## 功能模块详解

### 检测界面使用说明
1. **访问主页** http://127.0.0.1:8000
2. **上传图片**: 拖拽或点击上传图片（支持JPG、PNG、BMP格式，最大10MB）
3. **参数配置**（可选）：
   - **模型选择**: 从可用的YOLO模型中选择
   - **置信度阈值**: 0.1-1.0范围，控制检测敏感度
   - **IOU阈值**: 0.1-1.0范围，控制重叠检测框过滤
   - **图像尺寸**: 320/640/1280像素，影响检测精度和速度
4. **开始检测**: 点击"开始检测"按钮
5. **查看结果**: 查看检测结果、统计信息和美化图像

### AI分析功能使用说明
1. **在检测结果页面**，找到"AI智能分析"模块
2. **配置分析参数**：
   - **分析提示词**: 自定义分析需求
   - **AI模型选择**:
     - Qwen QwQ-32B（强大推理能力）
     - Qwen 2.5-7B-Instruct（快速响应）
     - Qwen 2.5-14B-Instruct（平衡性能）
     - DeepSeek V2.5（深度思考）
3. **开始分析**: 点击"开始AI分析"按钮
4. **查看结果**: 实时查看流式分析输出
5. **结果操作**: 复制文本或下载PDF报告

### 历史记录管理
1. **访问历史页面**: 点击导航栏"检测历史"
2. **记录浏览**: 卡片式展示所有检测记录
3. **搜索筛选**:
   - 按检测状态筛选（成功、失败、处理中）
   - 按时间范围筛选
   - 按文件名搜索
4. **详情查看**: 查看完整的检测结果和分析报告
5. **记录管理**: 删除不需要的检测记录

### 模型管理功能
1. **访问模型页面**: 点击导航栏"模型管理"
2. **模型列表**: 查看所有可用的YOLO模型
3. **模型信息**: 查看模型文件大小、修改时间、使用统计
4. **模型切换**: 选择不同模型进行检测
5. **性能监控**: 查看各模型的检测性能和使用情况

### 用户认证系统
1. **用户注册**: 创建新用户账户
2. **用户登录**: 安全的登录验证
3. **权限管理**: 基于用户角色的权限控制
4. **数据隔离**: 每个用户只能访问自己的数据
5. **安全防护**: 登录失败保护、会话管理

## API接口文档

### RESTful API端点

| 端点 | 方法 | 功能说明 | 认证要求 |
|------|------|----------|----------|
| `/api/detect/` | POST | 上传图片并执行检测 | 是 |
| `/api/result/<id>/` | GET | 获取检测结果详情 | 是 |
| `/api/models/` | GET | 获取可用模型列表 | 是 |
| `/api/history/` | GET | 获取用户检测历史 | 是 |
| `/api/delete/<id>/` | DELETE | 删除检测记录 | 是 |
| `/api/llm-analysis/` | POST | 大模型分析接口 | 是 |
| `/api/download-pdf/<id>/` | GET | 下载PDF分析报告 | 是 |

### API使用示例

#### 1. 图片检测API
```javascript
// 上传图片并检测
const formData = new FormData();
formData.append('image', imageFile);
formData.append('model_name', 'YOLO12n-seg.pt');
formData.append('confidence', 0.25);
formData.append('iou', 0.45);
formData.append('imgsz', 640);

fetch('/api/detect/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('检测成功:', data.result);
        // 处理检测结果
    } else {
        console.error('检测失败:', data.error);
    }
});
```

#### 2. 大模型分析API
```javascript
// 调用大模型分析
const analysisData = {
    prompt: "请分析这张图片中的口罩佩戴情况，给出专业建议",
    model: "Qwen/QwQ-32B",
    record_id: 17,
    detection_data: {
        total_detections: 5,
        with_mask_count: 3,
        without_mask_count: 1,
        incorrect_mask_count: 1,
        confidence_scores: [0.95, 0.87, 0.92, 0.78, 0.89]
    }
};

fetch('/api/llm-analysis/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify(analysisData)
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('分析结果:', data.analysis);
    } else {
        console.error('分析失败:', data.error);
    }
});
```

#### 3. 获取检测历史API
```javascript
// 获取用户检测历史
fetch('/api/history/?page=1&status=success', {
    method: 'GET',
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
})
.then(response => response.json())
.then(data => {
    console.log('历史记录:', data.records);
    console.log('总数:', data.total);
    console.log('页数:', data.pages);
});
```

#### 4. 获取可用模型API
```javascript
// 获取可用模型列表
fetch('/api/models/', {
    method: 'GET',
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
})
.then(response => response.json())
.then(data => {
    console.log('可用模型:', data.models);
    data.models.forEach(model => {
        console.log(`模型: ${model.name}, 状态: ${model.status}`);
    });
});
```

### API响应格式

#### 成功响应
```json
{
    "success": true,
    "data": {
        // 具体数据内容
    },
    "message": "操作成功"
}
```

#### 错误响应
```json
{
    "success": false,
    "error": "错误描述",
    "code": "ERROR_CODE"
}
```

### 检测结果数据结构
```json
{
    "record_id": 17,
    "original_image_url": "/media/uploads/original/image.jpg",
    "result_image_url": "/media/uploads/results/image_result.jpg",
    "detection_data": {
        "total_detections": 5,
        "with_mask_count": 3,
        "without_mask_count": 1,
        "incorrect_mask_count": 1,
        "detections": [
            {
                "class": "with_mask",
                "confidence": 0.95,
                "bbox": [100, 150, 200, 250]
            }
        ]
    },
    "parameters": {
        "model_name": "YOLO12n-seg.pt",
        "confidence": 0.25,
        "iou": 0.45,
        "imgsz": 640
    },
    "upload_time": "2025-07-03T10:30:00Z",
    "processing_time": 2.5
}

## 配置说明

### Django项目配置 (settings.py)
```python
# YOLO服务器路径配置
YOLO_SERVER_ROOT = BASE_DIR.parent / 'yoloserver'
YOLO_MODELS_DIR = YOLO_SERVER_ROOT / 'models' / 'checkpoints'
YOLO_SCRIPTS_DIR = YOLO_SERVER_ROOT / 'scripts'

# 文件上传限制
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 安全配置
CSRF_COOKIE_SECURE = False  # 开发环境设为False
SESSION_COOKIE_SECURE = False  # 开发环境设为False
SECURE_SSL_REDIRECT = False  # 开发环境设为False

# 登录保护配置
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_LOCKOUT_TIME = 1800  # 30分钟
```

### 大模型集成配置 (llm_config.py)
```python
import os

# SiliconFlow API配置
SILICONFLOW_CONFIG = {
    'api_key': os.getenv('SILICONFLOW_API_KEY', 'sk-your-api-key-here'),
    'base_url': 'https://api.siliconflow.cn/v1/chat/completions',
    'timeout': 120,
    'max_tokens': 4000,
    'temperature': 0.7
}

# 可用模型列表
AVAILABLE_MODELS = [
    {
        'id': 'Qwen/QwQ-32B',
        'name': 'Qwen QwQ-32B',
        'description': '强大的推理模型，适合复杂分析',
        'max_tokens': 4000
    },
    {
        'id': 'Qwen/Qwen2.5-7B-Instruct',
        'name': 'Qwen 2.5-7B-Instruct',
        'description': '快速响应，适合一般分析',
        'max_tokens': 2000
    },
    {
        'id': 'Qwen/Qwen2.5-14B-Instruct',
        'name': 'Qwen 2.5-14B-Instruct',
        'description': '平衡性能，综合分析能力强',
        'max_tokens': 3000
    },
    {
        'id': 'deepseek-ai/DeepSeek-V2.5',
        'name': 'DeepSeek V2.5',
        'description': '深度思考模型，适合专业分析',
        'max_tokens': 4000
    }
]

# 默认模型
DEFAULT_MODEL = 'Qwen/QwQ-32B'

# 默认分析提示词
DEFAULT_PROMPT = """
基于以下口罩检测结果，请提供专业的分析报告：

检测统计：
- 总检测人数：{total_detections}
- 正确戴口罩：{with_mask_count}人
- 未戴口罩：{without_mask_count}人
- 错误戴口罩：{incorrect_mask_count}人

请从以下角度进行分析：
1. 整体合规性评估
2. 潜在风险识别
3. 改进建议和措施
4. 注意事项和提醒

请提供专业、客观的分析结果。
"""
```

### 数据库模型设计
```python
# detection/models.py

class DetectionRecord(models.Model):
    """检测记录模型"""
    # 用户关联
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='detection_records')

    # 基本信息
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    original_image = models.ImageField(upload_to='uploads/original/', verbose_name='原始图片')
    result_image = models.ImageField(upload_to='uploads/results/', verbose_name='检测结果图片')

    # 检测参数
    model_name = models.CharField(max_length=100, verbose_name='使用模型')
    confidence_threshold = models.FloatField(default=0.25, verbose_name='置信度阈值')
    iou_threshold = models.FloatField(default=0.45, verbose_name='IOU阈值')
    image_size = models.IntegerField(default=640, verbose_name='图像尺寸')

    # 检测结果统计
    total_detections = models.IntegerField(default=0, verbose_name='总检测数')
    with_mask_count = models.IntegerField(default=0, verbose_name='正确戴口罩数')
    without_mask_count = models.IntegerField(default=0, verbose_name='未戴口罩数')
    incorrect_mask_count = models.IntegerField(default=0, verbose_name='错误戴口罩数')

    # 详细检测数据（JSON格式）
    detection_data = models.JSONField(default=dict, verbose_name='详细检测数据')

    # 处理状态
    status = models.CharField(max_length=20, default='processing', verbose_name='处理状态')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # AI分析结果
    llm_analysis = models.TextField(blank=True, verbose_name='AI分析结果')
    analysis_model = models.CharField(max_length=100, blank=True, verbose_name='分析模型')
    analysis_time = models.DateTimeField(null=True, blank=True, verbose_name='分析时间')

class YOLOModel(models.Model):
    """YOLO模型信息"""
    name = models.CharField(max_length=100, unique=True, verbose_name='模型名称')
    file_path = models.CharField(max_length=255, verbose_name='文件路径')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    created_time = models.DateTimeField(verbose_name='创建时间')
    modified_time = models.DateTimeField(verbose_name='修改时间')

    # 模型性能信息
    accuracy = models.FloatField(null=True, blank=True, verbose_name='准确率')
    inference_speed = models.FloatField(null=True, blank=True, verbose_name='推理速度(ms)')
    description = models.TextField(blank=True, verbose_name='模型描述')

    # 使用统计
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')
    last_used = models.DateTimeField(null=True, blank=True, verbose_name='最后使用时间')

    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_configured = models.BooleanField(default=False, verbose_name='是否已配置')
```

## 前端界面使用说明

### 主要页面功能

#### 检测页面 (index.html)
- **文件上传区域**: 支持拖拽和点击上传
- **参数配置面板**: 模型选择、置信度、IOU阈值、图像尺寸
- **检测按钮**: 触发检测流程
- **进度显示**: 实时显示检测进度

#### 结果页面 (result.html)
- **图像对比**: 原图与检测结果对比显示
- **统计信息**: 检测数量、类别分布、置信度统计
- **AI分析模块**: 大模型分析功能
- **操作按钮**: 重新检测、保存结果、下载报告

#### 历史记录页面 (history.html)
- **记录列表**: 卡片式展示历史记录
- **搜索筛选**: 按时间、状态、文件名筛选
- **批量操作**: 批量删除、导出功能
- **详情查看**: 查看完整检测结果

#### 模型管理页面 (models.html)
- **模型列表**: 显示所有可用模型
- **状态指示**: 模型可用状态和配置状态
- **性能信息**: 模型准确率、推理速度等
- **使用统计**: 模型使用频率和历史

### JavaScript功能模块

#### 检测功能 (detection.js)
```javascript
// 主要功能函数
function uploadAndDetect() {
    // 图片上传和检测逻辑
}

function updateProgress(percentage) {
    // 更新检测进度
}

function displayResults(data) {
    // 显示检测结果
}

function handleError(error) {
    // 错误处理
}
```

#### AI分析功能 (llm-analysis.js)
```javascript
// AI分析相关函数
function startLLMAnalysis() {
    // 启动AI分析
}

function streamAnalysisResult() {
    // 流式显示分析结果
}

function downloadPDFReport() {
    // 下载PDF报告
}
```

## 开发指南和代码结构

### 视图函数结构 (views.py)
```python
# 主要视图函数
def index(request):
    """主页视图 - 检测界面"""

def detect_image(request):
    """图像检测视图"""

def detection_result(request, record_id):
    """检测结果视图"""

def detection_history(request):
    """历史记录视图"""

def model_management(request):
    """模型管理视图"""
```

### API视图结构 (api_views.py)
```python
# API接口视图
@csrf_exempt
def api_detect(request):
    """检测API接口"""

@csrf_exempt
def api_llm_analysis(request):
    """大模型分析API接口"""

def api_models(request):
    """模型列表API接口"""

def api_history(request):
    """历史记录API接口"""
```

### 服务层结构 (services.py)
```python
class YOLOInferenceService:
    """YOLO推理服务封装"""

    def __init__(self):
        self.yolo_script_path = settings.YOLO_SCRIPTS_DIR / 'yolo_infer.py'

    def detect_image(self, image_path, **params):
        """执行图像检测"""

    def parse_results(self, result_output):
        """解析检测结果"""

class LLMAnalysisService:
    """大模型分析服务"""

    def __init__(self):
        self.config = SILICONFLOW_CONFIG

    def analyze_detection_result(self, prompt, model, detection_data):
        """分析检测结果"""

    def stream_analysis(self, prompt, model, detection_data):
        """流式分析"""
```

## 部署说明

### 开发环境部署
```bash
# 1. 激活虚拟环境
conda activate FMD

# 2. 进入项目目录
cd django_frontend

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
export SILICONFLOW_API_KEY="your-api-key-here"

# 5. 初始化数据库
python manage.py migrate

# 6. 创建超级用户
python manage.py createsuperuser

# 7. 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 生产环境部署

#### 使用Gunicorn + Nginx
```bash
# 1. 安装生产环境依赖
pip install gunicorn

# 2. 配置生产环境设置
export DJANGO_SETTINGS_MODULE=face_mask_detection.settings_production

# 3. 收集静态文件
python manage.py collectstatic --noinput

# 4. 启动Gunicorn
gunicorn face_mask_detection.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100
```

#### Nginx配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location /static/ {
        alias /path/to/django_frontend/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/django_frontend/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

#### Docker部署
```dockerfile
# Dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "face_mask_detection.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
      - ../yoloserver:/app/yoloserver
    environment:
      - SILICONFLOW_API_KEY=${SILICONFLOW_API_KEY}
    depends_on:
      - db

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=facemask_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password

volumes:
  postgres_data:
```

### 环境变量配置
```bash
# .env文件
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/facemask_db

# 大模型API配置
SILICONFLOW_API_KEY=sk-your-api-key-here

# 文件存储配置
MEDIA_ROOT=/path/to/media
STATIC_ROOT=/path/to/static
```

## 故障排除

### 常见问题及解决方案

#### 1. Django服务启动失败
**问题现象**: 运行 `python manage.py runserver` 失败
**解决方案**:
```bash
# 检查Python环境
python --version

# 检查Django安装
python -c "import django; print(django.get_version())"

# 检查数据库迁移
python manage.py showmigrations

# 重新迁移数据库
python manage.py migrate

# 检查端口占用
netstat -an | grep 8000
```

#### 2. YOLO推理失败
**问题现象**: 检测失败，显示推理错误
**解决方案**:
```bash
# 检查yoloserver目录
ls -la ../yoloserver/

# 检查模型文件
ls -la ../yoloserver/models/checkpoints/

# 检查YOLO脚本
python ../yoloserver/scripts/yolo_infer.py --help

# 测试YOLO推理
cd ../yoloserver
python scripts/yolo_infer.py --weights models/checkpoints/best.pt --source test_image.jpg
```

#### 3. 图片上传失败
**问题现象**: 上传按钮无响应或显示上传错误
**解决方案**:
```bash
# 检查media目录权限
ls -la media/

# 创建必要目录
mkdir -p media/uploads/original media/uploads/results

# 检查文件大小限制
python -c "from django.conf import settings; print(f'最大文件大小: {settings.MAX_IMAGE_SIZE}')"

# 检查允许的文件格式
python -c "from django.conf import settings; print(f'允许格式: {settings.ALLOWED_IMAGE_EXTENSIONS}')"
```

#### 4. 大模型API调用失败
**问题现象**: AI分析功能无响应或返回错误
**解决方案**:
```bash
# 检查API密钥配置
python -c "from llm_config import SILICONFLOW_CONFIG; print('API配置正确' if SILICONFLOW_CONFIG['api_key'] else 'API密钥未配置')"

# 测试网络连接
curl -I https://api.siliconflow.cn/v1/chat/completions

# 检查API调用日志
tail -f logs/llm.log

# 手动测试API
python -c "
import requests
from llm_config import SILICONFLOW_CONFIG
response = requests.get('https://api.siliconflow.cn/v1/models',
                       headers={'Authorization': f'Bearer {SILICONFLOW_CONFIG[\"api_key\"]}'})
print(f'API状态: {response.status_code}')
"
```

#### 5. 静态文件加载失败
**问题现象**: CSS、JS文件无法加载，页面样式异常
**解决方案**:
```bash
# 收集静态文件
python manage.py collectstatic --noinput

# 检查静态文件配置
python -c "from django.conf import settings; print(f'STATIC_URL: {settings.STATIC_URL}'); print(f'STATIC_ROOT: {settings.STATIC_ROOT}')"

# 检查静态文件目录
ls -la static/ staticfiles/

# 开发环境下确保DEBUG=True
python -c "from django.conf import settings; print(f'DEBUG: {settings.DEBUG}')"
```

#### 6. 数据库相关问题
**问题现象**: 数据库操作失败或数据丢失
**解决方案**:
```bash
# 检查数据库文件
ls -la db.sqlite3

# 重新创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 如果数据库损坏，重新初始化
rm db.sqlite3
python manage.py migrate
python manage.py setup_auth
```

#### 7. 用户认证问题
**问题现象**: 登录失败或权限错误
**解决方案**:
```bash
# 创建超级用户
python manage.py createsuperuser

# 重置用户密码
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.set_password('new_password')
user.save()
print('密码重置成功')
"

# 检查用户权限
python manage.py shell -c "
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
print(f'用户: {user.username}, 超级用户: {user.is_superuser}')
"
```

### 日志分析

#### 查看Django日志
```bash
# 查看应用日志
tail -f logs/django.log

# 查看检测服务日志
tail -f logs/detection.log

# 查看大模型API日志
tail -f logs/llm.log

# 搜索错误信息
grep -i error logs/*.log
```

#### 调试模式
```bash
# 启用详细日志
export DJANGO_LOG_LEVEL=DEBUG

# 启用Django调试模式
export DJANGO_DEBUG=True

# 重启服务器
python manage.py runserver --verbosity=2
```

### 性能优化建议

#### 数据库优化
```python
# 在settings.py中添加数据库优化配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}
```

#### 文件处理优化
```python
# 在settings.py中配置文件处理
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
```

## 技术支持

### 获取帮助
1. **查看日志**: 首先检查 `logs/` 目录下的相关日志文件
2. **运行诊断**: 使用 `python manage.py check` 进行系统诊断
3. **检查配置**: 验证 `settings.py` 和 `llm_config.py` 配置
4. **测试组件**: 分别测试YOLO服务和大模型API

### 报告问题
提交问题时请包含：
- 完整的错误信息和堆栈跟踪
- 使用的浏览器和版本
- 上传的图片信息（大小、格式）
- Django和Python版本信息
- 相关的日志文件内容

### 版本信息
- **Django版本**: 4.2+
- **Python版本**: 3.8+
- **Bootstrap版本**: 5.x
- **支持的浏览器**: Chrome 80+, Firefox 75+, Safari 13+

---

**最后更新**: 2025-07-03
**维护状态**: 积极维护
**技术支持**: 完整的文档和示例代码
**部署状态**: 生产就绪
