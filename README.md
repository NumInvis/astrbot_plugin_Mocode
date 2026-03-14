# Mocode - AstrBot 在线运行代码插件

支持 Python 代码本地安全执行

## 来源与致敬

本项目移植自 [nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code)，感谢原作者的出色工作！

## 安装

1. 在 AstrBot 插件管理面板中添加仓库地址：
   ```
   https://github.com/NumInvis/astrbot_plugin_Mocode
   ```

2. 点击安装即可

## 配置

在 AstrBot 插件配置面板中设置：
- `admin_only`: 是否仅管理员使用（默认：false）
- `timeout_seconds`: 代码执行超时时间（默认：30秒）

**注意**：本插件使用 Docker 沙箱执行 Python 代码
- 仅支持 Python 语言
- Docker 沙箱提供真正的隔离环境
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

### 基本用法
```
code [语言] [输入(可选)]
[代码]
```

### 示例

运行 Python Hello World：
```
/code py
print("Hello World!")
```

带输入的 Python 示例：
```
/code py 你好，世界！
print(input())
```

运行 JavaScript：
```
/code js
console.log("Hello from JavaScript!");
```

### 支持的语言

- **Python** (py/python) - 本地安全执行

> 其他语言（JavaScript、Java、C/C++ 等）的在线 API 已不可用，暂时只支持 Python

## 命令

- `/code` - 运行代码
- `/mocode` - 查看帮助信息

## 致谢

- 原项目：[nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code)

## License

MIT License
