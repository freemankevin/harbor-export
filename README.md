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

服务将在 `http://localhost:5000` 启动

### 4. 查看 API 文档

访问 `http://localhost:5000/api/docs` 查看完整的 API 文档

## 📚 API 接口说明

### Harbor 相关接口

#### 1. 测试连接
```http
POST /api/harbor/test-connection
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "连接成功，找到 3 个项目",
  "data": {
    "projects": [
      {
        "project_id": 1,
        "name": "bj-tgy",
        "public": false,
        "repo_count": 4,
        "created": "2025-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### 2. 获取项目列表
```http
POST /api/harbor/projects
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345",
  "page": 1,
  "pageSize": 100
}
```

#### 3. 获取项目详情
```http
POST /api/harbor/projects/{project_name}
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345"
}
```

#### 4. 获取仓库列表
```http
POST /api/harbor/repositories
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345",
  "project": "bj-tgy",
  "page": 1,
  "pageSize": 100
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "repositories": [
      {
        "id": 1,
        "name": "bj-tgy/dev/outer-net-mq-service-arm64",
        "project_name": "bj-tgy",
        "artifact_count": 2,
        "pull_count": 10,
        "tags": ["latest", "v1.0.0"],
        "artifacts": [
          {
            "digest": "sha256:abc123...",
            "tags": ["latest"],
            "size": 257698304,
            "push_time": "2025-02-14T16:58:00Z"
          }
        ]
      }
    ]
  }
}
```

#### 5. 搜索仓库
```http
POST /api/harbor/search
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345",
  "query": "nginx"
}
```

#### 6. 获取系统信息
```http
POST /api/harbor/system-info
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345"
}
```

#### 7. 获取统计信息
```http
POST /api/harbor/statistics
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345"
}
```

### Docker 相关接口

#### 1. 检查 Docker 连接
```http
GET /api/docker/ping
```

#### 2. 下载镜像
```http
POST /api/docker/download
Content-Type: application/json

{
  "harborUrl": "https://10.3.2.40",
  "username": "admin",
  "password": "Harbor12345",
  "image": "bj-tgy/dev/outer-net-mq-service-arm64",
  "tag": "latest"
}
```

**响应：** 直接返回 `.tar.gz` 文件流

#### 3. 获取本地镜像
```http
GET /api/docker/local-images
```

#### 4. 删除本地镜像
```http
POST /api/docker/remove-image
Content-Type: application/json

{
  "imageId": "sha256:abc123..."
}
```

### 系统管理接口

#### 1. 健康检查
```http
GET /api/system/health
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "docker": "connected"
  }
}
```

#### 2. 系统信息
```http
GET /api/system/info
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "cpu": {
      "percent": 25.5,
      "count": 8
    },
    "memory": {
      "total": 17179869184,
      "available": 8589934592,
      "percent": 50.0,
      "used": 8589934592
    },
    "disk": {
      "total": 500000000000,
      "used": 250000000000,
      "free": 250000000000,
      "percent": 50.0
    },
    "download_folder": {
      "path": "/path/to/downloads",
      "size": 1073741824
    }
  }
}
```

#### 3. 清理临时文件
```http
POST /api/system/cleanup
```

#### 4. 获取日志
```http
GET /api/system/logs
```

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

## 🎯 功能特性

### Harbor 功能
- ✅ 连接测试和认证
- ✅ 获取项目列表和详情
- ✅ 获取仓库列表和标签
- ✅ 搜索仓库
- ✅ 获取系统信息和统计
- ✅ 支持分页查询
- ✅ 完整的错误处理

### Docker 功能
- ✅ 自动登录 Harbor
- ✅ 拉取镜像
- ✅ 保存镜像为 tar
- ✅ 自动压缩为 tar.gz
- ✅ 保留完整镜像名称和标签
- ✅ 管理本地镜像
- ✅ 自动清理临时文件

### 系统功能
- ✅ 健康检查
- ✅ 系统资源监控
- ✅ 日志管理
- ✅ 临时文件清理
- ✅ 完整的日志记录

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

