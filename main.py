"""
Mocode - AstrBot 在线运行代码插件
支持多种编程语言，运行于 glot.io
版本: 1.0.0
"""

import asyncio
import json
import os
import re
import sys
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
        """运行代码 - 本地执行（仅支持 Python）"""
        if language not in ["python", "py"]:
            return {"stdout": "", "stderr": "", "error": "当前仅支持 Python 语言（其他语言的在线 API 已不可用）"}
        
        return await self._run_python_local(code, input_text)
    
    async def _run_python_local(self, code: str, input_text: str = "") -> Dict:
        """执行 Python 代码 - 优先使用 Docker 沙箱，不可用时回退到本地执行"""
        # 首先尝试 Docker 沙箱
        docker_result = await self._run_docker_sandbox(code, input_text)
        if docker_result.get("error") != "Docker 未安装或不可用":
            return docker_result
        
        # Docker 不可用，回退到本地执行
        return await self._run_local_sandbox(code, input_text)
    
    async def _run_docker_sandbox(self, code: str, input_text: str = "") -> Dict:
        """使用 Docker 沙箱执行 Python 代码"""
        import tempfile
        import os
        import subprocess
        
        # 检查 Docker 是否可用
        try:
            subprocess.run(["docker", "version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return {"stdout": "", "stderr": "", "error": "Docker 未安装或不可用"}
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="mocode_")
        
        try:
            # 写入代码文件
            code_file = os.path.join(temp_dir, "main.py")
            with open(code_file, 'w') as f:
                f.write(code)
            
            # 写入输入文件
            input_file = os.path.join(temp_dir, "input.txt")
            with open(input_file, 'w') as f:
                f.write(input_text or "")
            
            # 构建 Docker 命令
            docker_cmd = [
                "docker", "run", "--rm",
                "--read-only",
                "--network", "none",
                "--memory", "8m",
                "--memory-swap", "8m",
                "--cpus", "0.1",
                "--pids-limit", "10",
                "-v", f"{temp_dir}:/code:ro",
                "-w", "/code",
                "python:3.12-slim",
                "python", "-c",
                f"import sys; sys.stdin = open('/code/input.txt'); exec(open('/code/main.py').read())"
            ]
            
            try:
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds
                )
                
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": None
                }
            except subprocess.TimeoutExpired:
                return {
                    "stdout": "",
                    "stderr": f"执行超时（超过 {self.timeout_seconds} 秒）",
                    "error": None
                }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": "",
                    "error": f"Docker 执行错误: {str(e)}"
                }
        finally:
            # 清理临时目录
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    async def _run_local_sandbox(self, code: str, input_text: str = "") -> Dict:
        """本地沙箱执行（Docker 不可用时回退）"""
        import io
        import threading
        
        # 定义允许的内置函数
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii,
            'bin': bin, 'bool': bool, 'bytearray': bytearray, 'bytes': bytes,
            'callable': callable, 'chr': chr, 'classmethod': classmethod,
            'complex': complex, 'delattr': delattr, 'dict': dict, 'dir': dir,
            'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
            'float': float, 'format': format, 'frozenset': frozenset,
            'getattr': getattr, 'globals': globals, 'hasattr': hasattr,
            'hash': hash, 'hex': hex, 'id': id, 'int': int,
            'isinstance': isinstance, 'issubclass': issubclass, 'iter': iter,
            'len': len, 'list': list, 'locals': locals, 'map': map,
            'max': max, 'memoryview': memoryview, 'min': min, 'next': next,
            'object': object, 'oct': oct, 'ord': ord, 'pow': pow,
            'print': print, 'property': property, 'range': range,
            'repr': repr, 'reversed': reversed, 'round': round, 'set': set,
            'setattr': setattr, 'slice': slice, 'sorted': sorted,
            'staticmethod': staticmethod, 'str': str, 'sum': sum,
            'super': super, 'tuple': tuple, 'type': type, 'vars': vars,
            'zip': zip, '__import__': lambda x: None
        }
        
        safe_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            '__doc__': None,
            '__package__': None
        }
        
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        if input_text:
            stdin_buffer = io.StringIO(input_text)
        else:
            stdin_buffer = io.StringIO()
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin
        
        result_container = {}
        
        def execute_code():
            try:
                sys.stdout = stdout_buffer
                sys.stderr = stderr_buffer
                sys.stdin = stdin_buffer
                exec(code, safe_globals, {})
                result_container['success'] = True
            except Exception as e:
                result_container['error'] = str(e)
        
        try:
            thread = threading.Thread(target=execute_code)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.timeout_seconds)
            
            if thread.is_alive():
                return {
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": "执行超时（超过 {} 秒）".format(self.timeout_seconds),
                    "error": None
                }
            
            if 'error' in result_container:
                return {
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": result_container['error'],
                    "error": None
                }
            
            return {
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue(),
                "error": None
            }
            
        except Exception as e:
            return {
                "stdout": stdout_buffer.getvalue(),
                "stderr": stderr_buffer.getvalue() + "\n" + str(e),
                "error": None
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin

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
