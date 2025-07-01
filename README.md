# 🎯 YOLO口罩检测系统 v2.0

基于YOLO11深度学习的智能口罩佩戴检测平台，现已支持**多用户认证和权限管理**！

## 🆕 v2.0 新功能

### 🔐 用户认证系统
- **多用户支持**: 完整的用户注册、登录、权限管理
- **数据隔离**: 每个用户只能查看和管理自己的检测记录
- **权限分级**: 管理员可查看全站数据，普通用户仅限个人数据
- **安全防护**: 登录限制、CSRF保护、XSS防护、SQL注入防护

### 🛡️ 企业级安全
- **登录保护**: 5次失败后IP锁定30分钟
- **会话管理**: 安全的会话控制和自动过期
- **审计日志**: 完整的登录记录和操作追踪
- **密码安全**: Django内置哈希加密存储

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd FaceMaskDetection

# 安装依赖
pip install -r requirements.txt
```

### 2. 设置用户认证系统
```bash
cd django_frontend

# 运行数据库迁移
python manage.py migrate

# 设置用户认证系统（创建管理员账户）
python manage.py setup_auth

# 启动服务器
python manage.py runserver
```

### 3. 访问系统
- **系统入口**: http://127.0.0.1:8000
- **默认管理员**: admin / admin123
- **管理后台**: http://127.0.0.1:8000/admin/

## 📋 功能特性

### 🤖 AI检测功能
- **YOLO11模型**: 最新的目标检测算法
- **三类检测**: 正确戴口罩、未戴口罩、错误戴口罩
- **实时处理**: 快速图像上传和检测
- **结果美化**: 高质量的检测结果可视化

### 🧠 智能分析
- **大模型集成**: 支持GPT-4、Claude、Gemini等
- **专业分析**: AI生成的检测结果分析报告
- **多模型切换**: 灵活的模型管理系统

### 📊 数据管理
- **检测历史**: 完整的检测记录管理
- **统计分析**: 详细的检测数据统计
- **数据导出**: 支持检测结果导出
- **用户隔离**: 安全的多用户数据管理

### 🎨 现代化界面
- **响应式设计**: 支持桌面和移动设备
- **Bootstrap 5**: 现代化的UI组件
- **拖拽上传**: 便捷的图片上传体验
- **实时反馈**: 动态的处理状态显示

## 🏗️ 系统架构

```
FaceMaskDetection/
├── yoloserver/          # YOLO训练和推理服务
│   ├── scripts/         # 训练、验证、推理脚本
│   ├── utils/           # 工具函数和美化模块
│   └── models/          # 训练好的模型文件
├── django_frontend/     # Django Web前端
│   ├── detection/       # 主应用
│   ├── templates/       # 模板文件
│   ├── static/          # 静态资源
│   └── media/           # 上传文件
└── crawler_script/      # 数据爬虫模块
```

## 👥 用户权限

### 🔑 管理员权限
- 查看所有用户的检测记录和统计数据
- 用户管理和系统配置
- 模型管理和系统监控
- 访问Django管理后台

### 👤 普通用户权限
- 上传图片进行口罩检测
- 查看个人检测历史和统计
- 使用AI分析功能
- 管理个人账户信息

## 🔧 技术栈

### 后端技术
- **Django 4.2+**: Web框架
- **YOLO11**: 深度学习模型
- **SQLite/PostgreSQL**: 数据库
- **Pillow**: 图像处理

### 前端技术
- **Bootstrap 5**: UI框架
- **JavaScript**: 交互逻辑
- **Font Awesome**: 图标库
- **Chart.js**: 数据可视化

### AI技术
- **Ultralytics**: YOLO实现
- **OpenAI API**: GPT模型
- **Anthropic API**: Claude模型
- **Google API**: Gemini模型

## 📖 详细文档

- [用户认证设置指南](django_frontend/USER_AUTH_SETUP.md)
- [YOLO训练文档](yoloserver/README.md)
- [Django前端文档](django_frontend/README.md)
- [爬虫使用说明](crawler_script/爬虫使用说明.md)

## 🧪 测试

```bash
# 运行用户认证系统测试
cd django_frontend
python test_auth.py

# 运行Django测试
python manage.py test
```

## 🔄 版本历史

### v2.0.0 (2025-07-01)
- ✅ 新增完整的用户认证和权限管理系统
- ✅ 实现多用户数据隔离
- ✅ 添加企业级安全防护措施
- ✅ 优化用户界面和交互体验

### v1.0.0
- ✅ 基础的YOLO口罩检测功能
- ✅ Django Web界面
- ✅ 大模型分析集成
- ✅ 检测历史管理

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**🎯 项目状态**: ✅ 生产就绪
**🔧 技术支持**: 完整的文档和测试覆盖
**🛡️ 安全等级**: 企业级安全防护
**👥 用户支持**: 多用户权限管理