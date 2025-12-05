
SWAGGER_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Harbor Image Downloader API",
        "version": "2.0.0",
        "description": "一个功能强大的 Harbor 镜像管理和下载工具"
    },
    "servers": [
        {"url": "/api", "description": "API Server"}
    ],
    "tags": [
        {"name": "Harbor", "description": "Harbor 仓库相关操作"},
        {"name": "Docker", "description": "Docker 镜像操作"},
        {"name": "System", "description": "系统管理"}
    ],
    "paths": {
        "/harbor/test-connection": {
            "post": {
                "tags": ["Harbor"],
                "summary": "测试 Harbor 连接",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "harborUrl": {"type": "string", "example": "https://harbor.example.com"},
                                    "username": {"type": "string", "example": "admin"},
                                    "password": {"type": "string", "example": "password123"}
                                },
                                "required": ["harborUrl", "username", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "连接成功"}
                }
            }
        },
        "/harbor/projects": {
            "post": {
                "tags": ["Harbor"],
                "summary": "获取项目列表",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "harborUrl": {"type": "string"},
                                    "username": {"type": "string"},
                                    "password": {"type": "string"},
                                    "page": {"type": "integer", "default": 1},
                                    "pageSize": {"type": "integer", "default": 100}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "获取成功"}
                }
            }
        },
        "/harbor/projects/{project_name}": {
            "post": {
                "tags": ["Harbor"],
                "summary": "获取项目详情",
                "parameters": [
                    {"name": "project_name", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "harborUrl": {"type": "string"},
                                    "username": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "获取成功"}
                }
            }
        },
        "/harbor/repositories": {
            "post": {
                "tags": ["Harbor"],
                "summary": "获取仓库列表",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "harborUrl": {"type": "string"},
                                    "username": {"type": "string"},
                                    "password": {"type": "string"},
                                    "project": {"type": "string"},
                                    "page": {"type": "integer"},
                                    "pageSize": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "获取成功"}
                }
            }
        },
        "/docker/download": {
            "post": {
                "tags": ["Docker"],
                "summary": "下载镜像",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "harborUrl": {"type": "string"},
                                    "username": {"type": "string"},
                                    "password": {"type": "string"},
                                    "image": {"type": "string"},
                                    "tag": {"type": "string", "default": "latest"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "文件流",
                        "content": {
                            "application/gzip": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/docker/local-images": {
            "get": {
                "tags": ["Docker"],
                "summary": "获取本地镜像列表",
                "responses": {
                    "200": {"description": "获取成功"}
                }
            }
        },
        "/docker/ping": {
            "get": {
                "tags": ["Docker"],
                "summary": "检查 Docker 连接",
                "responses": {
                    "200": {"description": "连接正常"}
                }
            }
        },
        "/docker/remove-image": {
            "post": {
                "tags": ["Docker"],
                "summary": "删除本地镜像",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "imageId": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "删除成功"}
                }
            }
        },
        "/system/health": {
            "get": {
                "tags": ["System"],
                "summary": "健康检查",
                "responses": {
                    "200": {"description": "服务正常"}
                }
            }
        },
        "/system/info": {
            "get": {
                "tags": ["System"],
                "summary": "获取系统信息",
                "responses": {
                    "200": {"description": "获取成功"}
                }
            }
        },
        "/system/cleanup": {
            "post": {
                "tags": ["System"],
                "summary": "清理临时文件",
                "responses": {
                    "200": {"description": "清理完成"}
                }
            }
        },
        "/system/logs": {
            "get": {
                "tags": ["System"],
                "summary": "获取系统日志",
                "responses": {
                    "200": {"description": "获取成功"}
                }
            }
        }
    }
}
