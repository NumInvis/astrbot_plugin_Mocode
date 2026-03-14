"""
Mocode - AstrBot 在线运行代码插件
支持多种编程语言，运行于 glot.io
版本: 1.0.0
"""

import asyncio
import json
import os
import re
from typing import Dict, Optional

import aiohttp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.message_event_result import MessageChain
import astrbot.core.message.components as Comp

from ._version import __version__, __plugin_name__, __author__, __plugin_desc__


# 支持的语言映射
LANGUAGE_ALIASES = {
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "go": "go",
    "golang": "go",
    "rs": "rust",
    "rust": "rust",
    "rb": "ruby",
    "ruby": "ruby",
    "php": "php",
    "sh": "bash",
    "bash": "bash",
    "lua": "lua",
    "pl": "perl",
    "perl": "perl",
    "cs": "csharp",
    "c#": "csharp",
    "fs": "fsharp",
    "f#": "fsharp",
    "vb": "vb.net",
    "vb.net": "vb.net",
    "r": "r",
    "scala": "scala",
    "swift": "swift",
    "kt": "kotlin",
    "kotlin": "kotlin",
    "clj": "clojure",
    "clojure": "clojure",
    "hs": "haskell",
    "haskell": "haskell",
    "erl": "erlang",
    "erlang": "erlang",
    "ex": "elixir",
    "elixir": "elixir",
    "ml": "ocaml",
    "ocaml": "ocaml",
    "julia": "julia",
    "nim": "nim",
    "crystal": "crystal",
    "d": "d"
}

# 文件扩展名映射
FILE_EXTENSIONS = {
    "python": "py",
    "javascript": "js",
    "typescript": "ts",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "go": "go",
    "rust": "rs",
    "ruby": "rb",
    "php": "php",
    "bash": "sh",
    "lua": "lua",
    "perl": "pl",
    "csharp": "cs",
    "fsharp": "fs",
    "vb.net": "vb",
    "r": "r",
    "scala": "scala",
    "swift": "swift",
    "kotlin": "kt",
    "clojure": "clj",
    "haskell": "hs",
    "erlang": "erl",
    "elixir": "ex",
    "ocaml": "ml",
    "julia": "jl",
    "nim": "nim",
    "crystal": "cr",
    "d": "d"
}


@register(__plugin_name__, __author__, __plugin_desc__, __version__)
class MocodePlugin(Star):
    """Mocode 代码运行插件主类"""

    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config
        self.context = context

        # 数据目录
        self.data_dir = str(StarTools.get_data_dir("astrbot_plugin_mocode"))
        os.makedirs(self.data_dir, exist_ok=True)

        # 配置文件路径
        self.config_file = os.path.join(self.data_dir, "config.json")

        # 加载配置
        self._load_config()

        # HTTP 会话
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info("Mocode 代码运行插件已加载")

    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "glot_api_url": "https://glot.io/api",
            "glot_access_token": "",
            "admin_only": False,
            "timeout_seconds": 30
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except json.JSONDecodeError as e:
                logger.error(f"配置文件JSON格式错误: {e}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")

        if self.config:
            default_config["glot_api_url"] = self.config.get(
                "mocode_glot_api_url", default_config["glot_api_url"]
            )
            default_config["glot_access_token"] = self.config.get(
                "mocode_glot_access_token", default_config["glot_access_token"]
            )
            default_config["admin_only"] = self.config.get(
                "mocode_admin_only", default_config["admin_only"]
            )
            default_config["timeout_seconds"] = self.config.get(
                "mocode_timeout_seconds", default_config["timeout_seconds"]
            )

        self.glot_api_url = default_config["glot_api_url"]
        self.glot_access_token = default_config["glot_access_token"]
        self.admin_only = default_config["admin_only"]
        self.timeout_seconds = default_config["timeout_seconds"]

    async def initialize(self):
        """插件初始化时执行"""
        self._session = aiohttp.ClientSession()

    async def terminate(self):
        """插件卸载时清理资源"""
        if self._session:
            await self._session.close()

    def _is_admin(self, event: AstrMessageEvent) -> bool:
        """检查用户是否为管理员"""
        return event.is_admin()

    def _parse_command(self, text: str) -> Optional[Dict]:
        """解析 code 命令

        格式:
        code [语言] [输入(可选)]
        [代码]
        """
        lines = text.strip().split('\n')
        if not lines:
            return None

        first_line = lines[0].strip()
        
        # 匹配命令格式
        if not first_line.startswith('code'):
            return None

        parts = first_line.split(maxsplit=3)
        
        if len(parts) < 2:
            return None

        language_alias = parts[1].lower()
        
        # 解析输入
        input_text = ""
        code_start_index = 1
        
        if len(parts) >= 3:
            # 检查第三个部分是否是输入
            # 如果第二行开始有代码，那么第三部分可能是输入
            if len(lines) > 1 and lines[1].strip():
                input_text = ' '.join(parts[2:])
                code_start_index = 1
            else:
                input_text = ' '.join(parts[2:])
                code_start_index = 1

        # 解析代码
        code_lines = lines[code_start_index:]
        code = '\n'.join(code_lines).strip()

        if not code:
            return None

        # 标准化语言名称
        language = LANGUAGE_ALIASES.get(language_alias)
        if not language:
            return None

        return {
            "language": language,
            "input": input_text,
            "code": code
        }

    async def _run_code(self, language: str, code: str, input_text: str = "") -> Dict:
        """运行代码 - 使用 Judge0 API"""
        if not self._session:
            return {"error": "HTTP 会话未初始化"}

        # Judge0 API 语言 ID 映射
        JUDGE0_LANGUAGES = {
            "python": 71,      # Python 3.8.1
            "javascript": 63,  # JavaScript (Node.js 12.14.0)
            "typescript": 74,  # TypeScript 3.7.4
            "java": 62,        # Java (OpenJDK 13.0.1)
            "c": 50,           # C (GCC 9.2.0)
            "cpp": 54,         # C++ (GCC 9.2.0)
            "go": 60,          # Go (1.13.5)
            "rust": 73,        # Rust (1.40.0)
            "ruby": 72,        # Ruby (2.7.0)
            "php": 68,         # PHP (7.4.1)
            "bash": 46,        # Bash (5.0.0)
            "lua": 64,         # Lua (5.3.5)
            "perl": 85,        # Perl (5.28.1)
            "csharp": 51,      # C# (Mono 6.6.0.161)
            "fsharp": 87,      # F# (Mono 10.2.3)
            "vb.net": 84,      # VB.NET (Mono 10.2.3)
            "r": 80,           # R (4.0.0)
            "scala": 81,       # Scala (2.13.2)
            "swift": 83,       # Swift (5.2.3)
            "kotlin": 78,      # Kotlin (1.3.70)
            "clojure": 86,     # Clojure (1.10.1)
            "haskell": 61,     # Haskell (GHC 8.8.1)
            "erlang": 52,      # Erlang (22.2)
            "elixir": 57,      # Elixir (1.9.4)
            "ocaml": 65,       # OCaml (4.09.0)
            "julia": 70,       # Julia (1.4.0)
            "nim": 66,         # Nim (1.0.4)
            "crystal": 67,     # Crystal (0.32.1)
            "d": 56            # D (DMD 2.089.1)
        }

        language_id = JUDGE0_LANGUAGES.get(language)
        if not language_id:
            return {"stdout": "", "stderr": "", "error": f"不支持的语言: {language}"}

        payload = {
            "language_id": language_id,
            "source_code": code,
            "stdin": input_text,
            "cpu_time_limit": self.timeout_seconds,
            "memory_limit": 128000  # 128MB
        }

        try:
            # 使用 Judge0 公共 API（无需 API Key，有速率限制）
            url = "https://judge0-ce.p.rapidapi.com/submissions?base64_encoded=false&wait=true"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # 尝试多个 Judge0 实例
            urls = [
                "https://judge0-ce.p.rapidapi.com/submissions?base64_encoded=false&wait=true",
                "http://165.227.115.19:2358/submissions?base64_encoded=false&wait=true"
            ]
            
            for url in urls:
                try:
                    async with self._session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout_seconds + 5)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            stdout = result.get("stdout", "") or ""
                            stderr = result.get("stderr", "") or ""
                            compile_output = result.get("compile_output", "") or ""
                            message = result.get("message", "")
                            
                            # 解码 base64
                            import base64
                            try:
                                if stdout:
                                    stdout = base64.b64decode(stdout).decode('utf-8', errors='replace')
                                if stderr:
                                    stderr = base64.b64decode(stderr).decode('utf-8', errors='replace')
                                if compile_output:
                                    compile_output = base64.b64decode(compile_output).decode('utf-8', errors='replace')
                            except:
                                pass
                            
                            # 合并编译错误和运行错误
                            if compile_output:
                                stderr = compile_output + "\n" + stderr
                            
                            # 检查状态
                            status_id = result.get("status", {}).get("id", 0)
                            if status_id != 3:  # 3 = Accepted
                                if message:
                                    stderr = message + "\n" + stderr
                            
                            return {
                                "stdout": stdout,
                                "stderr": stderr,
                                "error": None
                            }
                except Exception as e:
                    continue
            
            return {"stdout": "", "stderr": "", "error": "所有 Judge0 API 实例均不可用"}
            
        except asyncio.TimeoutError:
            return {"stdout": "", "stderr": "", "error": "执行超时"}
        except Exception as e:
            return {"stdout": "", "stderr": "", "error": f"请求错误: {str(e)}"}

    def _build_result_message(self, result: Dict) -> str:
        """构建结果消息"""
        lines = []
        
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        error = result.get("error")

        if error:
            lines.append(f"❌ 错误: {error}")
        else:
            if stdout:
                lines.append("📤 标准输出:")
                lines.append("```")
                lines.append(stdout)
                lines.append("```")
            
            if stderr:
                lines.append("📥 标准错误:")
                lines.append("```")
                lines.append(stderr)
                lines.append("```")
            
            if not stdout and not stderr:
                lines.append("✅ 执行完成，无输出")

        return '\n'.join(lines)

    @filter.command("code")
    async def cmd_code(self, event: AstrMessageEvent):
        """运行代码"""
        if self.admin_only and not self._is_admin(event):
            yield event.plain_result("⚠️ 只有管理员可以使用此命令")
            return

        message_text = event.message_str
        
        parsed = self._parse_command(message_text)
        if not parsed:
            yield event.plain_result(
                "❌ 命令格式错误\n\n"
                "使用格式:\n"
                "code [语言] [输入(可选)]\n"
                "[代码]\n\n"
                "示例:\n"
                "code py\n"
                "print(\"Hello World!\")\n\n"
                "带输入示例:\n"
                "code py 你好\n"
                "print(input())"
            )
            return

        language = parsed["language"]
        input_text = parsed["input"]
        code = parsed["code"]

        yield event.plain_result(f"⏳ 正在运行 {language} 代码...")

        result = await self._run_code(language, code, input_text)
        result_msg = self._build_result_message(result)

        yield event.plain_result(result_msg)

    @filter.command("mocode")
    async def cmd_mocode(self, event: AstrMessageEvent):
        """Mocode 帮助"""
        help_msg = """📢 Mocode 代码运行器使用说明 (v1.0.0)

【使用格式】
code [语言] [输入(可选)]
[代码]

【示例】
code py
print("Hello World!")

【带输入示例】
code py 你好
print(input())

【支持的语言】
Python(py), JavaScript(js), TypeScript(ts), Java, C, C++, Go(golang), Rust(rs),
Ruby(rb), PHP, Bash(sh), Lua, Perl(pl), C#(cs), F#(fs), VB.NET(vb), R,
Scala, Swift, Kotlin(kt), Clojure(clj), Haskell(hs), Erlang(erl),
Elixir(ex), OCaml(ml), Julia, Nim, Crystal, D"""
        
        yield event.plain_result(help_msg)
