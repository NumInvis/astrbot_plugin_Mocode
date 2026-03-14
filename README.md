# Mocode - AstrBot 在线运行代码插件

支持 Python 代码在 Docker 沙箱中安全执行

## 来源与致敬

本项目移植自 [nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code)，感谢原作者的出色工作！

## 安装

1. 在 AstrBot 插件管理面板中添加仓库地址：
   ```
   https://github.com/NumInvis/astrbot_plugin_Mocode
   ```

2. 点击安装即可

## 系统要求

**必须在宿主机上安装 Docker**

### 方案 1：挂载 Docker Socket（推荐）

如果 AstrBot 运行在 Docker 容器中，启动时需要挂载 Docker socket：

```bash
docker run -d \
  --name astrbot \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/astrbot/data:/AstrBot/data \
  -p 6185:6185 \
  soulter/astrbot:latest
```

### 方案 2：直接运行 AstrBot

如果直接在宿主机上运行 AstrBot（不使用 Docker），只需确保宿主机已安装 Docker：

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io

# CentOS/RHEL
sudo yum install -y docker
sudo systemctl start docker

# 或使用官方安装脚本
curl -fsSL https://get.docker.com | sh
```

## 配置

在 AstrBot 插件配置面板中设置：
- `admin_only`: 是否仅管理员使用（默认：false）
- `timeout_seconds`: 代码执行超时时间（默认：30秒）

**注意**：本插件使用 **Docker 沙箱** 执行 Python 代码
- 仅支持 Python 语言
- 自动拉取 Python 镜像
- 执行超时时间可配置

**Docker 沙箱限制：**
- 只读文件系统（--read-only）
- 禁止网络访问（--network none）
- 内存限制 8MB（--memory 8m）
- CPU 限制 10%（--cpus 0.1）
- 进程数限制 10（--pids-limit 10）
- 运行后自动删除容器（--rm）

> 资源限制非常严格，仅适合运行简单代码

## 使用

### 基本命令格式
```
/code [语言] [输入(可选)]
[代码]
```

### 使用示例

**1. 运行 Python Hello World：**
```
/code py
print("Hello World!")
```

**2. 带输入的 Python 示例：**
```
/code py 你好，世界！
print(input())
```

### 支持的语言

| 别名 | 语言 |
|------|------|
| py / python | Python |

> 目前仅支持 Python，其他语言的在线 API 已不可用

### 命令列表

- `/code` - 运行代码
- `/mocode` - 查看帮助信息

## 工作原理

插件使用 Docker 容器来运行代码：
1. 检查 Docker 是否可用
2. 自动拉取 python:3.12-slim 镜像（如果不存在）
3. 在临时目录中写入代码文件
4. 启动 Docker 容器运行代码
5. 捕获标准输出和标准错误
6. 返回执行结果

**安全特性：**
- 代码在隔离的 Docker 容器中运行
- 只读文件系统防止修改宿主机文件
- 网络隔离防止访问外部网络
- 严格的资源限制（内存、CPU、进程数）
- 超时控制防止无限循环

## 致谢

- 原项目：[nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code)
- Docker 沙箱技术
