"""
core/runtime_dir.py — 运行时项目目录管理

唯一的用户工作目录真相来源。
程序启动时立即锁定 os.getcwd()，之后所有模块统一通过本模块获取，
不再各自调用 os.getcwd()（后者可能在运行过程中改变）。
"""
import os

# 程序启动时立即锁定用户的工作目录
# 例如用户在 E:\maren> 执行 python E:\MarenCode\app.py
# 此时 _RUNTIME_DIR = "E:\maren"
_RUNTIME_DIR = os.path.abspath(os.getcwd())


def get_runtime_dir() -> str:
    """获取程序启动时锁定的用户工作目录"""
    return _RUNTIME_DIR


def set_runtime_dir(path: str):
    """手动设置运行时目录（用于测试或特殊场景）"""
    global _RUNTIME_DIR
    _RUNTIME_DIR = os.path.abspath(path)


def resolve_path(path: str) -> str:
    """
    将相对路径解析为基于运行时目录的绝对路径。
    如果已经是绝对路径则直接返回。
    """
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(_RUNTIME_DIR, path))


def maren_dir() -> str:
    """获取 .maren 配置目录的绝对路径"""
    return os.path.join(_RUNTIME_DIR, ".maren")
