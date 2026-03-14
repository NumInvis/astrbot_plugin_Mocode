# 🚀 Mocode - AstrBot 在线代码执行插件

[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-blue)](https://github.com/AstrBotDevs/AstrBot)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> 💡 **核心亮点**：深度集成 AstrBot 本地沙箱，无需 Docker，即装即用！

Mocode 是一款专为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 设计的代码执行插件，让用户能够在聊天环境中安全、便捷地运行 Python 代码。

## ✨ 核心特性

### 🔒 原生 AstrBot 沙箱支持
- **深度集成**：直接调用 AstrBot 内置的 `LocalPythonTool` 和 `LocalShellComponent` 沙箱
- **零配置**：无需安装 Docker，无需额外依赖
- **即装即用**：安装后立即可用，无需复杂配置
- **多语言支持**：支持 Python、JavaScript、Bash 三种语言

### 🛡️ 企业级安全防护
- **子进程隔离**：代码在独立子进程中运行
- **超时控制**：防止无限循环和长时间运行
- **危险命令拦截**：自动拦截 `rm -rf`、`mkfs`、`dd` 等危险命令
- **文件系统限制**：代码只能访问 AstrBot 目录内的文件

### 🎯 简洁易用
- **自然语言交互**：通过聊天即可执行代码
- **输入支持**：支持通过参数传递输入数据
- **实时反馈**：即时返回执行结果

## 📦 安装

### 方式一：插件市场安装（推荐）

1. 打开 AstrBot 管理面板
2. 进入「插件」→「插件市场」
3. 点击「添加仓库」，输入：
   ```
   https://github.com/NumInvis/astrbot_plugin_Mocode
   ```
4. 找到 Mocode 插件，点击「安装」

### 方式二：手动安装

```bash
# 进入 AstrBot 插件目录
cd /path/to/astrbot/data/plugins

# 克隆仓库
git clone https://github.com/NumInvis/astrbot_plugin_Mocode.git

# 重启 AstrBot
```

## ⚙️ 配置

在 AstrBot 管理面板中配置：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `admin_only` | 布尔值 | `false` | 是否仅管理员可用 |
| `timeout_seconds` | 整数 | `30` | 代码执行超时时间（秒） |

## 🎮 使用方法

### 基本语法

```
/code [语言] [输入数据]
[代码]
```

### 使用示例

#### 1️⃣ Hello World
```
/code py
print("Hello, World!")
```

**输出：**
```
✅ 执行成功
Hello, World!
```

#### 2️⃣ 带输入的代码
```
/code py AstrBot 真棒！
message = input()
print(f"你说: {message}")
```

**输出：**
```
✅ 执行成功
你说: AstrBot 真棒！
```

#### 3️⃣ 数学计算
```
/code py
# 计算 1 到 100 的和
result = sum(range(101))
print(f"1+2+3+...+100 = {result}")

# 斐波那契数列
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

print(f"斐波那契数列第 10 项: {fib(10)}")
```

**输出：**
```
✅ 执行成功
1+2+3+...+100 = 5050
斐波那契数列第 10 项: 55
```

#### 4️⃣ 字符串处理
```
/code py
import json

data = {
    "name": "AstrBot",
    "version": "3.0",
    "features": ["AI", "插件系统", "多平台"]
}

print(json.dumps(data, ensure_ascii=False, indent=2))
```

**输出：**
```
✅ 执行成功
{
  "name": "AstrBot",
  "version": "3.0",
  "features": ["AI", "插件系统", "多平台"]
}
```

#### 5️⃣ JavaScript 示例
```
/code js
const greeting = "Hello from JavaScript!";
console.log(greeting);

// 计算数组和
const numbers = [1, 2, 3, 4, 5];
const sum = numbers.reduce((a, b) => a + b, 0);
console.log(`Sum: ${sum}`);
```

**输出：**
```
✅ 执行成功
Hello from JavaScript!
Sum: 15
```

#### 6️⃣ Bash 示例
```
/code bash
echo "Hello from Bash!"
echo "当前时间: $(date)"
echo "当前目录: $(pwd)"
```

**输出：**
```
✅ 执行成功
Hello from Bash!
当前时间: Mon Jan  1 12:00:00 UTC 2024
当前目录: /AstrBot
```

## 🔧 支持的语言

| 语言 | 别名 | 状态 | 执行方式 |
|------|------|------|----------|
| Python | `py`, `python` | ✅ 支持 | `LocalPythonTool` |
| JavaScript | `js`, `javascript`, `node` | ✅ 支持 | `node` 命令 |
| Bash | `sh`, `bash`, `shell` | ✅ 支持 | `bash` 命令 |

## 🛡️ 安全说明

### 沙箱机制

本插件使用 **AstrBot 原生沙箱** (`LocalPythonTool`) 执行代码：

```python
from astrbot.core.computer.computer_client import get_local_booter

booter = get_local_booter()
result = await booter.python.exec(code, timeout=30)
```

### 安全特性

- ✅ **进程隔离**：每个代码片段在独立子进程中运行
- ✅ **超时保护**：超过配置时间自动终止
- ✅ **命令过滤**：自动拦截危险系统命令
- ✅ **路径限制**：文件操作限制在 AstrBot 安全目录内
- ✅ **资源控制**：CPU 和内存使用受系统限制

### 禁止的操作

以下操作会被自动拦截：
- `rm -rf /` 等破坏性命令
- `mkfs` 等格式化命令
- `dd if=` 等磁盘操作
- `shutdown`, `reboot`, `poweroff` 等系统命令
- 访问 `/etc/passwd` 等敏感文件

## 🏗️ 技术架构

```
用户输入
    ↓
AstrBot 消息处理
    ↓
Mocode 插件解析
    ↓
AstrBot LocalPythonTool 沙箱
    ↓
子进程执行代码
    ↓
返回执行结果
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证开源。

## 🙏 致谢

- 原项目：[nonebot-plugin-code](https://github.com/yzyyz1387/nonebot_plugin_code) - 感谢原作者的出色工作！
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 优秀的聊天机器人框架
- AstrBot 沙箱技术团队

---

<p align="center">
  Made with ❤️ for AstrBot Community
</p>
