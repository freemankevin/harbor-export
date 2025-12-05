# Harbor EXPORT

一个功能强大的 Harbor 镜像管理和下载工具后端服务。

## 📁 项目结构

```
harbor-export/
├── app.py                      # 主应用入口
├── config.py                   # 配置文件
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量（可选）
├── api/                        # API 路由层
│   ├── __init__.py
│   ├── harbor.py              # Harbor API 接口
│   ├── docker.py              # Docker 操作接口
│   └── system.py              # 系统管理接口
├── services/                   # 服务层
│   ├── __init__.py
│   ├── harbor_service.py      # Harbor 业务逻辑
│   └── docker_service.py      # Docker 业务逻辑
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── logger.py              # 日志工具
│   ├── auth.py                # 认证工具
│   └── response.py            # 响应格式化
├── logs/                       # 日志目录
├── temp/                       # 临时文件
└── downloads/                  # 下载文件
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Docker (需要启动 Docker 守护进程)
- 可访问的 Harbor 仓库

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
# GIT BASH
source venv/Scripts/activate


# 安装依赖
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5001` 启动

### 4. 查看 API 文档

访问 `http://localhost:5001/api/docs` 查看完整的 API 文档


## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件：

```env
# Flask 配置
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Docker 配置
DOCKER_TIMEOUT=600

# 日志配置
LOG_LEVEL=INFO
```

### config.py 配置项

- `MAX_CONTENT_LENGTH`: 最大上传文件大小（默认 16GB）
- `DOCKER_TIMEOUT`: Docker 操作超时时间（默认 600 秒）
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `HARBOR_REQUEST_TIMEOUT`: Harbor API 请求超时（默认 30 秒）


## 📝 开发说明

### 代码结构说明

1. **分层架构**
   - `api/`: 路由层，处理 HTTP 请求
   - `services/`: 服务层，实现业务逻辑
   - `utils/`: 工具层，提供通用功能

2. **错误处理**
   - 统一的响应格式
   - 详细的错误日志
   - 友好的错误提示

3. **日志系统**
   - 控制台 + 文件双重输出
   - 自动日志轮转
   - 详细的调试信息

### 扩展开发

#### 添加新的 API 接口

1. 在 `api/` 目录创建新的蓝图
2. 在 `services/` 实现业务逻辑
3. 在 `app.py` 注册蓝图

示例：
```python
# api/custom.py
from flask import Blueprint
from utils.response import success_response

custom_bp = Blueprint('custom', __name__, url_prefix='/api/custom')

@custom_bp.route('/hello', methods=['GET'])
def hello():
    return success_response(message='Hello World')

# app.py
from api.custom import custom_bp
app.register_blueprint(custom_bp)
```

## ⚠️ 注意事项

1. **Docker 依赖**: 服务器必须安装 Docker 并确保 Docker 守护进程运行
2. **磁盘空间**: 下载大镜像需要足够的磁盘空间（建议至少 50GB）
3. **网络访问**: 确保服务器可以访问 Harbor 仓库
4. **自签名证书**: 代码中已设置 `verify=False`，如需验证证书请修改配置
5. **权限问题**: 确保运行用户有权限访问 Docker socket

