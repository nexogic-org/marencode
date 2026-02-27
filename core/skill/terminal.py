"""
core/skill/terminal.py — 终端命令执行技能
在子进程中安全执行 shell 命令，带超时和输出截断
"""
import subprocess
import os
from core.runtime_dir import resolve_path, get_runtime_dir


# 禁止执行的危险命令关键词
_BLOCKED_PATTERNS = [
    "rm -rf /", "rm -rf ~", "del /f /s /q C:\\",
    "format c:", "mkfs", "dd if=", "> /dev/sda",
    ":(){ :|:& };:", "shutdown", "reboot",
]


def run_command(command: str, cwd: str = None, timeout: int = 30) -> str:
    """
    执行终端命令并返回输出
    :param command: 要执行的命令
    :param cwd: 工作目录（可选，默认当前目录）
    :param timeout: 超时秒数，默认 30 秒
    :return: 命令输出或错误信息
    """
    if not command:
        return "[ERROR] 未指定命令。"

    # 安全检查：拦截危险命令
    cmd_lower = command.lower().strip()
    for pattern in _BLOCKED_PATTERNS:
        if pattern.lower() in cmd_lower:
            return f"[BLOCKED] 危险命令被拦截: {command}"

    work_dir = resolve_path(cwd) if cwd else get_runtime_dir()
    if not os.path.isdir(work_dir):
        return f"[ERROR] 工作目录不存在: {work_dir}"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[STDERR]\n{result.stderr}")

        output = "\n".join(output_parts) if output_parts else "(无输出)"

        # 截断过长输出
        if len(output) > 8000:
            output = output[:8000] + "\n...(已截断)"

        status = "成功" if result.returncode == 0 else f"退出码 {result.returncode}"
        return f"[{status}] 命令: {command}\n目录: {work_dir}\n\n{output}"

    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] 命令超时 ({timeout}s): {command}\n工作目录: {work_dir}"
    except FileNotFoundError as e:
        return f"[ERROR] 命令或程序未找到: {command}\n详情: {e}\n工作目录: {work_dir}"
    except PermissionError as e:
        return f"[ERROR] 权限不足: {command}\n详情: {e}\n工作目录: {work_dir}"
    except Exception as e:
        return f"[ERROR] 执行失败: {type(e).__name__}: {e}\n命令: {command}\n工作目录: {work_dir}"
