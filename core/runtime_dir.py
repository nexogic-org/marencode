"""
core/runtime_dir.py — 运行时项目目录管理
在程序启动时记录用户的工作目录，所有文件操作都基于此目录
而非 os.getcwd()（后者可能在运行过程中改变）
"""
import os

# 程序启动时记录的用户工作目录
_RUNTIME_DIR = os.getcwd()


def get_runtime_dir() -> str:
    """获取程序启动时的运行目录（用户项目根目录）"""
    return _RUNTIME_DIR


def set_runtime_dir(path: str):
    """手动设置运行时目录（用于测试或特殊场景）"""
    global _RUNTIME_DIR
    _RUNTIME_DIR = os.path.abspath(path)


def resolve_path(path: str) -> str:
    """
    将相对路径解析为基于运行时目录的绝对路径
    如果已经是绝对路径则直接返回
    """
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(_RUNTIME_DIR, path))
