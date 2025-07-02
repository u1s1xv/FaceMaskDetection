# 🎭 口罩检测系统 - Django前端

基于Django框架的口罩检测Web前端系统，集成YOLO深度学习模型，提供图片上传、AI检测、结果展示、大模型分析等完整功能。

## 🎯 项目概述

- **项目名称**: FaceMaskDetection Web Frontend
- **技术栈**: Django + Bootstrap + JavaScript + YOLO + 大模型API
- **核心功能**: 图片上传 → YOLO推理 → 结果展示 → AI智能分析
- **环境**: FMD conda虚拟环境

## ✅ 功能特性

### 🚀 核心功能模块

#### 📤 文件上传模块
- **支持格式**: JPG, PNG, JPEG, BMP
- **文件大小限制**: 最大10MB
- **上传方式**: 拖拽上传 + 点击选择
- **预览功能**: 上传前图片预览

#### 🤖 AI检测模块
- **模型调用**: 集成 `yoloserver/scripts/yolo_infer.py`
- **检测类别**:
  - ✅ **正确戴口罩** (with_mask) - 绿色标注
  - ❌ **未戴口罩** (without_mask) - 红色标注
  - ⚠️ **错误戴口罩** (mask_weared_incorrect) - 蓝色标注
- **可调参数**: 置信度阈值、IOU阈值、图像尺寸

#### 🧠 大模型分析模块 (新增)
- **AI智能分析**: 基于检测结果的专业分析
- **多模型支持**: GPT-4、GPT-3.5、Claude-3、Gemini Pro
- **分析功能**:
  - 检测结果评估
  - 合规性分析
  - 风险评估
  - 改进建议
- **结果操作**: 复制结果、下载分析报告

#### 📊 结果展示模块
- **原图展示**: 用户上传的原始图片
- **检测结果**: 带标注的检测图片（美化版本）
- **统计信息**: 检测到的人数、各类别数量、置信度
- **详细数据**: 检测框坐标、置信度分数

#### 📈 增强功能模块
- **历史记录**: 保存检测历史，支持查看和删除
- **模型管理**: 选择不同的训练模型，自动发现模型文件
- **参数调节**: 实时调整检测参数
- **结果导出**: 下载检测结果和统计报告
- **系统设置**: 默认参数配置、缓存管理

## 🏗️ 系统架构

### 项目结构
```
FaceMaskDetection/
├── yoloserver/                    # 原有的YOLO服务端
│   ├── scripts/yolo_infer.py     # 推理脚本
│   ├── models/checkpoints/       # 训练好的模型
│   └── utils/                    # 工具模块
│
└── django_frontend/              # Django前端系统 ⭐
    ├── face_mask_detection/      # Django项目配置
    │   ├── settings.py          # 项目设置
    │   ├── urls.py              # 主URL配置
    │   └── wsgi.py              # WSGI配置
    │
    ├── detection/               # 主应用模块
    │   ├── models.py           # 数据模型
    │   ├── views.py            # 视图函数
    │   ├── forms.py            # 表单定义
    │   ├── services.py         # YOLO推理服务
    │   ├── api_views.py        # API接口（含大模型API）
    │   ├── urls.py             # 应用URL
    │   ├── admin.py            # 管理后台
    │   └── tests.py            # 测试用例
    │
    ├── templates/              # HTML模板
    │   ├── base.html          # 基础模板
    │   └── detection/         # 检测相关模板
    │       ├── index.html     # 主页
    │       ├── result.html    # 结果页（含大模型分析）
    │       ├── history.html   # 历史记录
    │       ├── models.html    # 模型管理
    │       └── settings.html  # 系统设置
    │
    ├── static/                # 静态文件
    │   ├── css/custom.css    # 自定义样式（含大模型样式）
    │   └── js/detection.js   # 前端JavaScript
    │
    ├── media/                 # 媒体文件目录
    │   └── uploads/          # 上传文件存储
    │
    ├── manage.py             # Django管理脚本
    ├── requirements.txt      # Python依赖
    ├── setup_django.py      # 项目初始化脚本
    ├── start_server.py      # 服务器启动脚本
    └── README.md            # 项目说明（本文档）
```

### 核心功能流程
1. **用户上传图片** → Django接收处理
2. **调用YOLO推理** → 返回检测结果
3. **前端展示结果** → 图片对比、统计信息
4. **AI智能分析** → 大模型API分析检测结果
5. **历史记录管理** → 保存、查看、删除记录

## 🚀 快速启动

### 环境要求
- **Python**: 3.8+
- **Django**: 4.2+
- **虚拟环境**: FMD conda环境（已配置YOLO相关依赖）

### 一键启动（推荐）
```bash
# 确保在FMD虚拟环境中
conda activate FMD

# 进入Django项目目录
cd django_frontend

# 运行启动脚本（自动安装依赖、初始化项目、启动服务器）
python start_server.py
```

### 手动安装步骤
```bash
# 1. 激活虚拟环境
conda activate FMD

# 2. 进入Django项目目录
cd django_frontend

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建数据库迁移
python manage.py makemigrations

# 5. 应用迁移
python manage.py migrate

# 6. 创建超级用户（可选）
python manage.py createsuperuser

# 7. 收集静态文件
python manage.py collectstatic

# 8. 启动开发服务器
python manage.py runserver
```

### 访问地址
- **主页**: http://127.0.0.1:8000
- **检测页面**: http://127.0.0.1:8000/detect/
- **历史记录**: http://127.0.0.1:8000/history/
- **模型管理**: http://127.0.0.1:8000/models/
- **系统设置**: http://127.0.0.1:8000/settings/
- **管理后台**: http://127.0.0.1:8000/admin
  - 默认用户名: `admin`
  - 默认密码: `admin123`

## 📱 使用指南

### 1. 图片检测流程
1. **访问主页** http://127.0.0.1:8000
2. **上传图片**: 拖拽或点击上传图片（支持JPG、PNG、BMP格式）
3. **调整参数**（可选）：
   - **模型选择**: 从实际存在的模型文件中选择
   - **置信度阈值**: 0.1-1.0范围，越高越严格
   - **IOU阈值**: 重叠度控制，0.1-1.0范围
   - **图像尺寸**: 320/640/1280像素，越大精度越高
4. **开始检测**: 点击"开始检测"按钮
5. **查看结果**: 等待AI处理完成，查看检测结果和统计信息

### 2. AI智能分析功能 (新增)
1. **在检测结果页面**，找到"AI智能分析"模块（位于检测结果对比下方）
2. **输入分析提示词**：
   - 默认提示：基于检测结果分析口罩佩戴情况
   - 自定义提示：如"给出改进建议"、"评估合规性"等
3. **选择AI模型**：
   - GPT-4（精准）
   - GPT-3.5 Turbo（快速）
   - Claude-3 Sonnet
   - Gemini Pro
4. **开始分析**: 点击"开始AI分析"按钮
5. **查看分析结果**: 获取专业的智能分析报告
6. **操作结果**: 复制结果或下载分析报告

### 3. 历史记录管理
1. **访问历史页面**: 点击导航栏"检测历史"
2. **浏览记录**: 查看所有检测记录的卡片式展示
3. **搜索筛选**:
   - 按状态筛选（完成、失败、处理中）
   - 按时间范围搜索
4. **查看详情**: 点击"查看详情"查看完整结果
5. **删除记录**: 删除不需要的检测记录

### 4. 模型管理
1. **添加模型**: 将训练好的.pt模型文件放入 `yoloserver/models/checkpoints/` 目录
2. **自动发现**: 系统会自动扫描目录下的模型文件
3. **查看状态**: 访问"模型管理"页面查看所有模型状态
   - 🟢 **已激活**: 模型已配置且处于激活状态
   - 🔵 **已配置**: 模型已配置但未激活
   - 🟡 **未配置**: 模型文件存在但未在数据库中配置
4. **配置模型**: 在管理后台为模型添加详细描述、准确率、推理速度等信息
5. **实时更新**: 添加新模型文件后刷新页面即可使用

### 5. 系统设置
1. **访问设置页面**: http://127.0.0.1:8000/settings/
2. **配置默认参数**: 设置检测的默认参数
3. **查看系统信息**: Django版本、Python版本、服务状态
4. **缓存管理**: 清理保存的默认参数

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
```

### 数据库设计
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

### 模型管理机制
1. **自动发现**: 系统启动时扫描 `yoloserver/models/checkpoints/` 目录
2. **文件过滤**: 只识别 `.pt` 扩展名的文件
3. **动态加载**: 每次表单初始化时重新扫描，确保实时性
4. **智能描述**: 根据文件名自动生成模型描述
5. **状态管理**:
   - 🟢 **已激活**: 模型已配置且处于激活状态
   - 🔵 **已配置**: 模型已配置但未激活
   - 🟡 **未配置**: 模型文件存在但未在数据库中配置

## 🛠️ API接口

### RESTful API端点
| 端点 | 方法 | 功能说明 |
|------|------|----------|
| `/api/detect/` | POST | 上传图片并检测 |
| `/api/result/<id>/` | GET | 获取检测结果 |
| `/api/models/` | GET | 获取可用模型列表 |
| `/api/history/` | GET | 获取检测历史 |
| `/api/delete/<id>/` | DELETE | 删除检测记录 |
| `/api/clear-cache/` | POST | 清理缓存 |
| `/api/llm-analysis/` | POST | 大模型分析接口 (新增) |

### API使用示例

#### 1. 图片检测
```javascript
// 上传图片检测
const formData = new FormData();
formData.append('image', imageFile);
formData.append('model_name', 'yolo11n-seg.pt');
formData.append('confidence', 0.25);
formData.append('iou', 0.45);
formData.append('imgsz', 640);

fetch('/api/detect/', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('检测结果:', data);
    // 处理检测结果
});
```

#### 2. 大模型分析 (新增)
```javascript
// 调用大模型分析
const analysisData = {
    prompt: "请分析这张图片中的口罩佩戴情况，并给出专业的评估和建议。",
    model: "Qwen/QwQ-32B",
    record_id: 17,
    detection_data: {
        total_detections: 5,
        with_mask_count: 3,
        without_mask_count: 1,
        incorrect_mask_count: 1,
        compliance_rate: 60.0,
        model_name: "yolo11n-seg.pt",
        confidence_threshold: 0.25
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
        console.log('使用模型:', data.model_used);
    }
});
```

#### 3. 获取模型列表
```javascript
// 获取可用模型
fetch('/api/models/')
.then(response => response.json())
.then(data => {
    console.log('可用模型:', data.available_models);
    console.log('模型总数:', data.total_count);
});
```

### 数据格式
- **JSON响应**: 标准化的API响应格式
- **错误处理**: 完善的错误信息返回
- **状态码**: 标准HTTP状态码使用

## 🎨 界面特性

### 现代化设计
- **Bootstrap 5**: 响应式框架，支持桌面端和移动端
- **Font Awesome**: 丰富的图标库
- **自定义CSS**: 美观的样式设计，渐变效果
- **移动端适配**: 完美支持手机和平板访问

### 用户体验优化
- **拖拽上传**: 直观的文件上传方式
- **实时验证**: 参数输入即时验证
- **进度反馈**: 检测过程可视化
- **图片预览**: 上传前图片预览
- **结果对比**: 原图 vs 检测结果对比展示
- **错误提示**: 友好的错误信息提示

### 页面布局
- **主页**: Logo + 功能菜单 + 上传区域 + 参数设置
- **结果页**: 图片对比 + 统计信息 + AI分析 + 操作按钮
- **历史页**: 卡片式布局 + 搜索筛选 + 分页显示
- **管理页**: 模型状态 + 配置信息 + 快捷操作

### 交互功能
- **拖拽上传**: 支持拖拽和点击上传
- **实时参数验证**: 输入参数即时验证范围
- **进度条显示**: 检测过程可视化
- **图片预览**: 上传前图片预览
- **结果对比展示**: 原图与检测结果对比
- **AI分析交互**: 智能分析模块的完整交互流程

## 🔍 故障排除

### 常见问题及解决方案

#### 1. YOLO推理失败
**问题现象**: 检测失败，显示推理错误
**解决方案**:
- 检查 `yoloserver` 目录是否存在
- 确认模型文件在 `yoloserver/models/checkpoints/` 目录下
- 检查模型文件是否为有效的 `.pt` 文件
- 查看Django终端日志获取详细错误信息
- 确认Python环境中已安装ultralytics包

#### 2. 图片上传失败
**问题现象**: 上传按钮无响应或显示上传错误
**解决方案**:
- 检查文件大小是否超过10MB限制
- 确认文件格式是否为支持的格式（JPG、PNG、BMP）
- 检查 `media` 目录是否存在且有写入权限
- 确认Django设置中的MEDIA_ROOT配置正确

#### 3. 静态文件加载失败
**问题现象**: 页面样式丢失，CSS/JS文件404错误
**解决方案**:
```bash
# 收集静态文件
python manage.py collectstatic

# 检查静态文件配置
# 确认settings.py中STATIC_URL和STATIC_ROOT设置正确
```

#### 4. 模板错误
**问题现象**: TemplateSyntaxError或TemplateDoesNotExist
**解决方案**:
- 检查模板文件是否存在于正确路径
- 确认模板语法正确，避免使用不支持的过滤器
- 检查视图函数中的模板路径是否正确

#### 5. 大模型API调用失败
**问题现象**: AI分析功能无响应或返回错误
**解决方案**:
- 检查网络连接是否正常
- 确认API接口路径正确 (`/api/llm-analysis/`)
- 检查请求数据格式是否正确
- 查看Django日志中的详细错误信息

#### 6. 数据库相关问题
**问题现象**: 数据库操作失败或数据丢失
**解决方案**:
```bash
# 重新创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 如果数据库损坏，删除db.sqlite3重新初始化
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### 调试模式
在开发环境中，Django的DEBUG模式已开启，会显示详细的错误信息。

### 日志查看
```bash
# Django开发服务器日志会直接显示在终端
# 查看详细日志
python manage.py runserver --verbosity=2

# 如果配置了日志文件
tail -f logs/django.log
```

### 性能问题
1. **检测速度慢**: 尝试使用较小的图像尺寸或更轻量的模型
2. **页面加载慢**: 检查静态文件是否正确收集和压缩
3. **内存占用高**: 定期清理media目录中的临时文件

## 🛡️ 安全与性能

### 安全措施
- **CSRF保护**: Django内置CSRF防护，所有表单和API请求都受保护
- **文件验证**: 严格的文件类型和大小限制
- **路径安全**: 防止路径遍历攻击
- **输入验证**: 所有用户输入都经过严格验证
- **权限控制**: 基于Django的权限系统
- **SQL注入防护**: 使用Django ORM防止SQL注入

### 性能优化
- **异步处理**: 避免页面阻塞，提升用户体验
- **文件管理**: 自动清理临时文件，节省存储空间
- **数据库优化**: 高效的查询设计，合理的索引配置
- **静态文件**: CDN就绪的静态资源管理
- **缓存机制**: Session缓存用户设置，减少重复计算
- **图片处理**: 智能图片压缩和格式转换

## 📊 技术栈总结

### 后端技术
- **Django 4.2+**: 现代化Web框架
- **SQLite**: 轻量级数据库（可升级到PostgreSQL）
- **Pillow**: 图像处理库
- **Ultralytics**: YOLO框架支持
- **Python 3.8+**: 编程语言

### 前端技术
- **Bootstrap 5**: 响应式CSS框架
- **jQuery**: JavaScript库
- **Font Awesome**: 图标库
- **自定义CSS/JS**: 增强用户体验

### AI集成
- **YOLO11**: 最新的深度学习模型
- **自定义推理服务**: YOLO推理封装
- **大模型API**: GPT、Claude、Gemini等多模型支持
- **智能分析**: 基于检测结果的专业分析

### 开发工具
- **Django Admin**: 管理后台
- **Django ORM**: 数据库操作
- **Django Forms**: 表单处理
- **Django Templates**: 模板引擎

## 🤝 开发指南

### 添加新功能
1. **数据模型**: 在 `detection/models.py` 中定义新的数据模型
2. **视图函数**: 在 `detection/views.py` 中添加视图逻辑
3. **URL路由**: 在 `detection/urls.py` 中配置URL路由
4. **HTML模板**: 在 `templates/detection/` 中创建模板
5. **API接口**: 在 `detection/api_views.py` 中添加API端点
6. **数据库迁移**: 运行 `python manage.py makemigrations` 和 `migrate`

### 自定义样式
- **CSS样式**: 编辑 `static/css/custom.css`
- **Bootstrap主题**: 修改Bootstrap变量
- **JavaScript**: 添加自定义交互逻辑
- **模板继承**: 基于 `base.html` 创建新页面

### 代码结构
```python
# 视图函数示例
def new_feature_view(request):
    if request.method == 'POST':
        # 处理POST请求
        pass
    else:
        # 处理GET请求
        pass
    return render(request, 'detection/new_feature.html', context)

# API接口示例
@csrf_exempt
@require_http_methods(["POST"])
def api_new_feature(request):
    try:
        data = json.loads(request.body)
        # 处理业务逻辑
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

## 📈 扩展建议

### 短期扩展
1. **用户系统**: 用户注册、登录、个人空间
2. **批量检测**: 支持多张图片同时上传检测
3. **数据导出**: Excel/CSV格式导出检测结果
4. **检测报告**: 自动生成PDF格式的检测报告
5. **API认证**: Token认证机制，支持第三方集成

### 中期规划
1. **实时检测**: 摄像头实时检测功能
2. **移动端APP**: React Native或Flutter移动应用
3. **缓存优化**: Redis缓存支持，提升性能
4. **异步处理**: Celery任务队列，处理大量并发
5. **监控系统**: 添加日志和性能监控

### 长期愿景
1. **云端部署**: AWS/Azure/阿里云部署方案
2. **微服务架构**: 拆分为多个独立服务
3. **大数据分析**: 检测数据的深度分析和可视化
4. **AI模型训练**: 在线模型训练和优化平台
5. **多语言支持**: 国际化和本地化

### 部署优化
1. **生产环境**: 使用Gunicorn + Nginx部署
2. **数据库**: 升级到PostgreSQL或MySQL
3. **文件存储**: 使用云存储服务（OSS、S3等）
4. **CDN加速**: 静态文件CDN分发
5. **负载均衡**: 多实例负载均衡

## 🎉 项目亮点

1. **功能完整**: 涵盖上传、检测、展示、分析、管理全流程
2. **界面美观**: 现代化UI设计，用户体验优秀
3. **架构合理**: 模块化设计，易于维护和扩展
4. **集成完善**: YOLO + 大模型API无缝集成
5. **安全可靠**: 完善的验证和错误处理机制
6. **文档齐全**: 详细的使用和开发文档
7. **智能分析**: 独创的大模型分析功能
8. **自动发现**: 智能的模型文件管理

## 📋 项目验证清单

- [x] Django项目结构完整
- [x] 数据模型设计合理
- [x] 视图和URL配置正确
- [x] 前端界面美观易用
- [x] YOLO集成服务完整
- [x] API接口功能完备
- [x] 大模型分析功能正常
- [x] 文件上传处理安全
- [x] 错误处理机制完善
- [x] 响应式设计支持
- [x] 管理后台配置完整
- [x] 模型自动发现功能
- [x] 系统设置页面完整

## 📞 技术支持

如有问题或建议，请：
1. 查看本文档的故障排除部分
2. 检查Django终端日志信息
3. 访问Django管理后台查看系统状态
4. 联系开发团队获取技术支持

---

## 📝 更新日志

### v1.2.0 (2025-07-01)
- ✨ 新增大模型API分析功能
- ✨ 新增AI智能分析模块
- 🔧 优化模型自动发现机制
- 🔧 完善系统设置页面
- 🐛 修复模板语法错误
- 📚 更新完整项目文档

### v1.1.0 (2025-06-30)
- ✨ 新增模型管理功能
- ✨ 新增系统设置页面
- 🔧 优化文件上传处理
- 🔧 改进错误处理机制

### v1.0.0 (2025-06-29)
- 🎉 项目初始版本发布
- ✨ 基础检测功能完成
- ✨ 历史记录管理
- ✨ API接口完整

---

**当前版本**: v1.2.0
**最后更新**: 2025-07-01
**技术栈**: Django + Bootstrap + YOLO + 大模型API
**开发状态**: ✅ 生产就绪
