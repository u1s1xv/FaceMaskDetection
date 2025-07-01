# 🔐 用户认证系统设置指南

本文档详细说明了YOLO口罩检测系统的用户认证和权限管理功能的设置和使用方法。

## 📋 功能概述

### ✅ 已实现功能

#### 🔑 用户认证系统
- **欢迎页面**: 系统入口，展示功能特性
- **用户注册**: 支持用户名、密码、邮箱注册
- **用户登录**: 安全登录，支持"记住我"功能
- **用户退出**: 安全退出登录

#### 🛡️ 安全性措施
- **输入验证**: 严格的服务端验证和清理
- **密码安全**: Django内置哈希加密存储
- **登录限制**: 5次失败后锁定30分钟
- **CSRF保护**: 防止跨站请求伪造
- **XSS防护**: 防止跨站脚本攻击
- **SQL注入防护**: 使用Django ORM参数化查询

#### 👥 权限分级管理
- **Django超级管理员**:
  - 查看所有用户的检测记录和统计数据
  - 系统管理权限（用户管理、模型管理等）
  - 可在首页和历史页面切换查看全站数据
- **普通用户**:
  - 只能查看和管理自己的检测记录
  - 只能看到自己的统计数据
  - 数据完全隔离

#### 🔒 数据隔离实现
- **DetectionRecord模型**: 添加user外键关联
- **视图过滤**: 所有查询基于当前用户过滤
- **API保护**: 所有API接口都需要登录认证
- **URL保护**: 防止用户直接访问其他用户数据

## 🚀 快速设置

### 1. 运行数据库迁移
```bash
cd django_frontend
python manage.py migrate
```

### 2. 设置用户认证系统
```bash
# 使用默认设置（推荐）
python manage.py setup_auth

# 或自定义管理员信息
python manage.py setup_auth --username admin --password yourpassword --email admin@yourdomain.com
```

### 3. 启动服务器
```bash
python manage.py runserver
```

### 4. 访问系统
- **系统入口**: http://127.0.0.1:8000 （自动重定向到欢迎页面）
- **欢迎页面**: http://127.0.0.1:8000/app/welcome/
- **用户登录**: http://127.0.0.1:8000/app/login/
- **用户注册**: http://127.0.0.1:8000/app/register/
- **管理后台**: http://127.0.0.1:8000/admin/

## 🔧 详细配置

### 默认管理员账户
- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@example.com
- **权限**: 超级管理员

### 安全配置参数
```python
# 登录失败限制
MAX_LOGIN_ATTEMPTS = 5  # 最大登录尝试次数
LOCKOUT_DURATION = 30   # 锁定时间（分钟）

# 会话设置
SESSION_COOKIE_AGE = 1209600  # 2周
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    'UserAttributeSimilarityValidator',
    'MinimumLengthValidator',  # 最少6位
    'CommonPasswordValidator',
    'NumericPasswordValidator',
]
```

### URL路由结构
```
/                           -> 重定向到欢迎页面
/app/welcome/              -> 欢迎页面
/app/login/                -> 登录页面
/app/register/             -> 注册页面
/app/logout/               -> 退出登录
/app/profile/              -> 个人资料
/app/                      -> 首页（需要登录）
/app/detect/               -> 检测页面（需要登录）
/app/history/              -> 历史记录（需要登录）
/app/models/               -> 模型管理（需要登录）
/app/settings/             -> 系统设置（需要登录）
/api/                      -> API接口（需要登录）
/admin/                    -> 管理后台
```

## 👤 用户管理

### 注册新用户
1. 访问注册页面：http://127.0.0.1:8000/app/register/
2. 填写注册信息：
   - **用户名**: 只允许数字和英文字母，3-150个字符
   - **密码**: 至少6位，支持字母、数字、特殊符号
   - **确认密码**: 二次验证
   - **邮箱**: 可选，用于后续功能扩展

### 用户登录
1. 访问登录页面：http://127.0.0.1:8000/app/login/
2. 输入用户名和密码
3. 可选择"记住我"（2周免登录）
4. 登录成功后重定向到首页

### 管理员功能
1. **查看全站数据**:
   - 首页右上角切换"我的数据"/"全站数据"
   - 历史页面切换查看所有用户记录
2. **用户管理**: 访问 /admin/ 管理后台
3. **系统监控**: 查看登录记录、安全日志

## 🔍 安全特性

### 登录保护
- **失败限制**: 5次失败后IP锁定30分钟
- **记录日志**: 所有登录尝试都被记录
- **用户代理**: 记录设备和浏览器信息
- **IP追踪**: 记录登录IP地址

### 数据保护
- **用户隔离**: 每个用户只能访问自己的数据
- **权限验证**: 所有操作都验证用户权限
- **CSRF令牌**: 防止跨站请求伪造
- **输入清理**: 防止XSS和SQL注入

### 会话安全
- **安全Cookie**: HttpOnly、SameSite设置
- **会话过期**: 可配置的会话时长
- **自动登出**: 浏览器关闭时可选登出

## 🛠️ 故障排除

### 常见问题

#### 1. 登录失败
**问题**: 无法登录系统
**解决方案**:
- 检查用户名和密码是否正确
- 确认账户未被锁定
- 检查是否超过登录尝试限制
- 查看管理后台用户状态

#### 2. 权限错误
**问题**: 无法访问某些页面
**解决方案**:
- 确认已登录系统
- 检查用户权限级别
- 确认URL路径正确
- 清除浏览器缓存

#### 3. 数据迁移问题
**问题**: 现有数据无法访问
**解决方案**:
```bash
# 重新运行设置命令
python manage.py setup_auth --skip-migration=False
```

#### 4. 忘记管理员密码
**解决方案**:
```bash
# 重置管理员密码
python manage.py changepassword admin
```

### 日志查看
```bash
# Django开发服务器日志
python manage.py runserver --verbosity=2

# 查看登录记录
# 访问管理后台 -> 登录尝试
```

## 📊 数据库结构

### 新增模型

#### UserProfile（用户配置）
- user: 关联User模型
- created_time: 创建时间
- last_login_ip: 最后登录IP
- login_count: 登录次数
- is_locked: 是否锁定
- locked_until: 锁定到期时间

#### LoginAttempt（登录尝试）
- username: 用户名
- ip_address: IP地址
- success: 是否成功
- attempt_time: 尝试时间
- user_agent: 用户代理

#### DetectionRecord（检测记录）
- user: 新增用户关联字段
- 其他字段保持不变

## 🔄 升级说明

### 从无认证版本升级
1. 备份现有数据库
2. 运行数据库迁移
3. 执行认证系统设置
4. 验证数据完整性

### 注意事项
- 现有检测记录会自动关联到管理员用户
- 所有页面都需要登录后访问
- API接口需要认证才能使用
- 建议更改默认管理员密码

---

**版本**: v2.0.0  
**更新时间**: 2025-07-01  
**功能状态**: ✅ 生产就绪
