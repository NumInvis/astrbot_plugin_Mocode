# Mocode - AstrBot 在线运行代码插件

支持 Python 代码在 AstrBot 本地沙箱中安全执行

## 来源与致敬

本项目移植自 [nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code)，感谢原作者的出色工作！

## 安装

1. 在 AstrBot 插件管理面板中添加仓库地址：
   ```
   https://github.com/NumInvis/astrbot_plugin_Mocode
   ```

2. 点击安装即可

## 系统要求

**无特殊要求**，插件使用 AstrBot 自带的本地沙箱执行代码。

## 配置

在 AstrBot 插件配置面板中设置：
- `admin_only`: 是否仅管理员使用（默认：false）
- `timeout_seconds`: 代码执行超时时间（默认：30秒）

**注意**：本插件使用 **AstrBot 本地沙箱** 执行 Python 代码
- 仅支持 Python 语言
- 自动使用 AstrBot 的沙箱环境
- 执行超时时间可配置

**AstrBot 沙箱限制：**
- 使用子进程执行代码
- 超时控制
- 禁止危险命令（如 `rm -rf`, `mkfs`, `dd` 等）
- 文件系统访问限制在 AstrBot 目录内

> 适合运行简单代码，资源限制由 AstrBot 控制

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

**3. 执行计算：**
```
/code py
x = sum(range(100))
print(f"Sum: {x}")
```

### 支持的语言

| 别名 | 语言 |
|------|------|
| py / python | Python |

> 目前仅支持 Python

### 命令列表

- `/code` - 运行代码
- `/mocode` - 查看帮助信息

## 工作原理

插件使用 AstrBot 的本地沙箱执行代码：
1. 导入 AstrBot 的 `get_local_booter()` 获取沙箱
2. 通过 `booter.python.exec()` 执行代码
3. 返回执行结果（标准输出和标准错误）

**安全特性：**
- 使用 AstrBot 内置的沙箱环境
- 子进程隔离
- 超时控制
- 禁止危险命令
- 文件系统访问限制

## 致谢

- 原项目：[nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code)
- AstrBot 沙箱技术
