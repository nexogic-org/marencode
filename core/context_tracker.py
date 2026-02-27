"""
core/context_tracker.py — 上下文使用量追踪器
根据 API 返回的上下文限度，实时计算已用百分比
支持 chat enter 和 run enter 模式
"""
from colorama import Fore, Style


class ContextTracker:
    """追踪对话上下文的 token 使用量"""

    def __init__(self, max_tokens: int = 128000):
        """
        :param max_tokens: 模型上下文窗口大小（默认 128k）
        """
        self.max_tokens = max_tokens
        self.used_chars = 0  # 已用字符数（粗略估算 token）

    def update(self, history: list, system_prompt: str = ""):
        """根据历史消息更新已用量"""
        total = len(system_prompt)
        for msg in history:
            total += len(msg.get("content") or "")
        self.used_chars = total

    def add_chars(self, count: int):
        """增加字符计数"""
        self.used_chars += count

    @property
    def used_tokens_estimate(self) -> int:
        """粗略估算已用 token 数（中文约 1.5 字符/token，英文约 4 字符/token）"""
        # 取一个折中值：约 2.5 字符/token
        return int(self.used_chars / 2.5)

    @property
    def usage_percent(self) -> float:
        """已用百分比"""
        if self.max_tokens <= 0:
            return 0.0
        return min(self.used_tokens_estimate / self.max_tokens * 100, 100.0)

    def render_bar(self, width: int = 20) -> str:
        """渲染上下文使用进度条"""
        pct = self.usage_percent
        filled = int(width * pct / 100)
        filled = min(filled, width)

        # 根据使用量选择颜色
        if pct < 50:
            color = Fore.GREEN
        elif pct < 80:
            color = Fore.YELLOW
        else:
            color = Fore.RED

        bar = "█" * filled + "░" * (width - filled)
        return f"{color}{bar}{Style.RESET_ALL} {pct:.1f}%"

    def render_inline(self) -> str:
        """渲染行内上下文提示（用于提示符旁边）"""
        pct = self.usage_percent
        if pct < 50:
            color = Fore.GREEN
        elif pct < 80:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        return f"{Fore.LIGHTBLACK_EX}[{color}{pct:.0f}%{Fore.LIGHTBLACK_EX}]{Style.RESET_ALL}"
