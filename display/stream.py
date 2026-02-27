"""
display/stream.py — 流式渲染器
负责将 AI 流式输出逐行解析并美化显示
支持代码块、tool_call JSON、普通文本的实时渲染
"""
import json
from colorama import Fore, Style
from display.style import InlineStyler
from display.table import is_table_line, is_table_separator, render_table
from display.code import highlight_code


class StreamRenderer:
    """流式 Markdown 渲染器，逐块接收文本并实时输出"""

    def __init__(self):
        self.in_code = False          # 是否在代码块内
        self.code_lang = ""           # 当前代码块语言
        self.file_path = ""           # 当前 file: 块的文件路径
        self.file_line_count = 0      # file: 块已接收的行数
        self.styler = InlineStyler()  # 行内样式处理器
        self.table_lines = []         # 表格行缓冲区
        self.buffer = ""              # 未处理的文本缓冲
        self.json_buffer = []         # tool_call JSON 缓冲

    def feed(self, chunk: str) -> str:
        """
        接收一个文本块，解析并通过 print 实时输出
        返回空字符串（兼容旧调用方式）
        """
        try:
            self.buffer += chunk
            self._process_buffer()
        except Exception as e:
            # 渲染失败时降级为原始输出，不中断流式显示
            print(f"{Fore.LIGHTBLACK_EX}[RENDER WARN] feed: {type(e).__name__}: {e}{Style.RESET_ALL}")
            try:
                print(chunk, end="", flush=True)
            except Exception:
                pass
        return ""

    def finalize(self) -> str:
        """刷新剩余缓冲区，返回尾部内容"""
        try:
            self._process_buffer(flush=True)
            output = []
            if self.table_lines:
                output.append("\n")
                output.append(render_table(self.table_lines))
                self.table_lines = []
            output.append(self.styler.finalize())
            return "".join(output)
        except Exception as e:
            print(f"{Fore.LIGHTBLACK_EX}[RENDER WARN] finalize: {type(e).__name__}: {e}{Style.RESET_ALL}")
            # 降级：返回缓冲区原始内容
            remaining = self.buffer
            self.buffer = ""
            return remaining

    def _process_buffer(self, flush=False):
        """逐行处理缓冲区内容"""
        max_iterations = 5000  # 防止异常情况下的无限循环
        iterations = 0
        while True:
            iterations += 1
            if iterations > max_iterations:
                # 安全阀：强制输出剩余缓冲并退出
                if self.buffer:
                    print(self.buffer, end="", flush=True)
                    self.buffer = ""
                break

            if not self.buffer:
                break

            nl = self.buffer.find('\n')
            if nl == -1:
                if flush:
                    line = self.buffer
                    self.buffer = ""
                else:
                    break
            else:
                line = self.buffer[:nl]
                self.buffer = self.buffer[nl + 1:]

            stripped = line.strip()

            # ── 代码块边界检测 ──
            if stripped.startswith("```"):
                # 进入/退出代码块前，先刷新待渲染的表格
                if self.table_lines:
                    print()  # 表格前空一行
                    rendered = render_table(self.table_lines)
                    self.table_lines = []
                    print(rendered, end="")
                if not self.in_code:
                    self._enter_code_block(stripped)
                else:
                    self._exit_code_block()
                continue

            # ── 代码块内容 ──
            if self.in_code:
                self._handle_code_line(line)
                continue

            # ── 普通文本（非 flush 时追加换行，因为 \n 已被 split 消耗）──
            has_newline = (nl != -1)
            self._render_line(line, final_line=not has_newline)

    def _enter_code_block(self, stripped: str):
        """进入代码块"""
        self.in_code = True
        self.code_lang = stripped[3:].strip()
        self.json_buffer = []

        # ── file:path 块：显示创建状态，静默内容 ──
        if self.code_lang.startswith("file:"):
            self.file_path = self.code_lang[5:].strip()
            self.file_line_count = 0
            print(f"  {Fore.YELLOW}⟳{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}正在创建{Style.RESET_ALL} {Fore.CYAN}{self.file_path}{Style.RESET_ALL} ...", end="", flush=True)
            return

        if self.code_lang == "tool_call":
            return

        # ── 普通代码块：显示加粗语言名称 ──
        display_lang = self.code_lang.upper() if self.code_lang else "CODE"
        print(f"\n{Style.BRIGHT}{Fore.CYAN}  ── {display_lang} ──{Style.RESET_ALL}")

    def _exit_code_block(self):
        """退出代码块，处理 tool_call、file: 或普通代码块结束"""
        self.in_code = False

        # ── file:path 块结束：覆盖行显示完成状态 ──
        if self.code_lang.startswith("file:"):
            print(f"\r  {Fore.GREEN}✓{Style.RESET_ALL} {Style.BRIGHT}{Fore.GREEN}文件已就绪{Style.RESET_ALL} {Fore.CYAN}{self.file_path}{Style.RESET_ALL} ({self.file_line_count} 行)")
            self.file_path = ""
            self.file_line_count = 0
            return

        if self.code_lang == "tool_call":
            self._render_tool_call()
        else:
            print(f"{Fore.CYAN}```{Style.RESET_ALL}")

    def _handle_code_line(self, line: str):
        """处理代码块内的一行"""
        if self.code_lang == "tool_call":
            self.json_buffer.append(line)
        elif self.code_lang.startswith("file:"):
            self.file_line_count += 1
        else:
            # 使用 display/code.py 的语法高亮
            try:
                highlighted = highlight_code(self.code_lang, line)
                print(f"  {highlighted}{Style.RESET_ALL}")
            except Exception:
                print(f"  {Fore.GREEN}{line}{Style.RESET_ALL}")

    def _render_tool_call(self):
        """渲染 tool_call JSON 为美化提示"""
        try:
            content = "".join(self.json_buffer)
            tool_data = json.loads(content)
            action = tool_data.get("action")
            msg = tool_data.get("msg")
            if action and msg:
                print(f"\r{Style.BRIGHT}{Fore.CYAN} ⚡ {msg}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}{content}{Style.RESET_ALL}")
        except Exception:
            print(f"{Fore.RED}{''.join(self.json_buffer)}{Style.RESET_ALL}")
        finally:
            self.json_buffer = []

    def _render_line(self, line: str, final_line: bool) -> str:
        """渲染普通文本行，处理表格收集逻辑"""
        if is_table_line(line):
            if is_table_separator(line):
                self.table_lines.append(line)
                return ""
            self.table_lines.append(line)
            return ""

        # 如果之前有缓存的表格行，先渲染表格
        if self.table_lines:
            print()  # 表格前空一行，视觉分隔
            rendered = render_table(self.table_lines)
            self.table_lines = []
            print(rendered, end="")
            result = self.styler.feed(line + ("\n" if not final_line else ""))
            if result:
                print(result, end="", flush=True)
            return ""

        result = self.styler.feed(line + ("\n" if not final_line else ""))
        if result:
            print(result, end="", flush=True)
        return ""
