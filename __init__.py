"""
Mocode 代码运行插件
AstrBot 在线运行代码插件

版本: 1.0.0
"""

from ._version import __version__, __plugin_name__, __plugin_desc__, __author__
from .main import MocodePlugin

__all__ = ["MocodePlugin", "__version__", "__plugin_name__", "__plugin_desc__", "__author__"]
