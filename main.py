"""
Mocode 代码运行插件
AstrBot 在线运行代码插件

版本: 1.0
"""

import asyncio
import base64
import json
import os
import tempfile
from typing import Dict, Optional

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.core.config.astrbot_config import AstrBotConfig

from ._version import __version__, __plugin_name__, __author__, __plugin_desc__


# 支持的语言映射
LANGUAGE_ALIASES = {
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "node": "javascript",
    "sh": "bash",
    "bash": "bash",
    "shell": "bash"
}


@register(__plugin_name__, __author__, __plugin_desc__, __version__)
class MocodePlugin(Star):
    """Mocode 代码运行插件主类"""

    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config

        # 加载配置
        self.admin_only = False
        self.timeout_seconds = 30
        if config:
            self.admin_only = config.get("mocode_admin_only", False)
            self.timeout_seconds = config.get("mocode_timeout_seconds", 30)

        logger.info("Mocode 代码运行插件已加载")

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
        if len(parts) >= 3:
            input_text = ' '.join(parts[2:])

        # 解析代码
        code_lines = lines[1:]
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
        """运行代码 - 使用 AstrBot 本地沙箱"""
        from astrbot.core.computer.computer_client import get_local_booter
        
        booter = get_local_booter()
        
        if language == "python":
            return await self._run_python(booter, code, input_text)
        elif language == "javascript":
            return await self._run_javascript(booter, code, input_text)
        elif language == "bash":
            return await self._run_bash(booter, code, input_text)
        else:
            return {"stdout": "", "stderr": "", "error": f"不支持的语言: {language}"}

    async def _run_python(self, booter, code: str, input_text: str = "") -> Dict:
        """使用 AstrBot 本地沙箱执行 Python 代码"""
        try:
            if input_text:
                input_b64 = base64.b64encode(input_text.encode('utf-8')).decode('utf-8')
                code = f'import sys\nimport base64\nfrom io import StringIO\ninput_text = base64.b64decode("{input_b64}").decode("utf-8")\nsys.stdin = StringIO(input_text)\n' + code
            
            result = await booter.python.exec(code, timeout=self.timeout_seconds)
            
            data = result.get("data", {})
            output = data.get("output", {})
            return {
                "stdout": output.get("text", ""),
                "stderr": data.get("error", ""),
                "error": None
            }
        except Exception as e:
            logger.error(f"执行 Python 代码时出错: {e}")
            return {"stdout": "", "stderr": "", "error": f"执行错误: {str(e)}"}

    async def _run_javascript(self, booter, code: str, input_text: str = "") -> Dict:
        """使用 AstrBot 本地沙箱执行 JavaScript 代码"""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                if input_text:
                    input_b64 = base64.b64encode(input_text.encode('utf-8')).decode('utf-8')
                    f.write(f'const input = Buffer.from("{input_b64}", "base64").toString("utf-8");\n')
                f.write(code)
                temp_file = f.name
            
            result = await booter.shell.exec(f"node {temp_file}", timeout=self.timeout_seconds)
            
            return {
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "error": None
            }
        except Exception as e:
            logger.error(f"执行 JavaScript 代码时出错: {e}")
            return {"stdout": "", "stderr": "", "error": f"执行错误: {str(e)}"}
        finally:
            if temp_file:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

    async def _run_bash(self, booter, code: str, input_text: str = "") -> Dict:
        """使用 AstrBot 本地沙箱执行 Bash 代码"""
        try:
            if input_text:
                input_b64 = base64.b64encode(input_text.encode('utf-8')).decode('utf-8')
                command = f'echo "{input_b64}" | base64 -d | {code}'
            else:
                command = code
            
            result = await booter.shell.exec(command, timeout=self.timeout_seconds)
            
            return {
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "error": None
            }
        except Exception as e:
            logger.error(f"执行 Bash 代码时出错: {e}")
            return {"stdout": "", "stderr": "", "error": f"执行错误: {str(e)}"}

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
                lines.append("⚠️ 标准错误:")
                lines.append("```")
                lines.append(stderr)
                lines.append("```")
            
            if not stdout and not stderr:
                lines.append("✅ 执行成功（无输出）")

        return "\n".join(lines)

    @filter.command("code")
    async def cmd_code(self, event: AstrMessageEvent):
        """code 命令 - 运行代码"""
        message_text = event.message_str

        # 检查权限
        if self.admin_only and not self._is_admin(event):
            yield event.make_result().message("❌ 只有管理员可以使用此命令")
            return

        # 解析命令
        parsed = self._parse_command(message_text)
        if not parsed:
            yield event.make_result().message("❌ 命令格式错误\n\n正确格式:\ncode [语言] [输入(可选)]\n[代码]\n\n例如:\ncode py\nprint('Hello World!')")
            return

        language = parsed["language"]
        input_text = parsed["input"]
        code = parsed["code"]

        # 发送处理中消息
        yield event.make_result().message(f"🚀 正在运行 {language} 代码...")

        # 运行代码
        result = await self._run_code(language, code, input_text)

        # 构建结果消息
        result_message = self._build_result_message(result)

        # 发送结果
        yield event.make_result().message(result_message)

    @filter.command("mocode")
    async def cmd_mocode(self, event: AstrMessageEvent):
        """Mocode 帮助"""
        help_msg = """📢 Mocode 代码运行器使用说明 (v1.0)

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
Python(py), JavaScript(js/node), Bash(sh/bash/shell)

【配置项】
- admin_only: 是否仅管理员可用
- timeout_seconds: 执行超时时间（秒）
"""
        yield event.make_result().message(help_msg)
