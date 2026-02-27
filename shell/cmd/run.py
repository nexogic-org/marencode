"""
shell/cmd/run.py — code run 命令
支持一键全自动编程和 run enter 交互式项目对话模式
- run <描述>: 一键全自动编程
- run enter: 进入交互式项目对话模式
"""
import os
import sys
import json
import uuid
from datetime import datetime
try:
    import msvcrt
except ImportError:
    msvcrt = None
from colorama import Fore, Style, init
from shell.cmd import prefix
from core.agent.orchestrator import run_pipeline
from core.agent import request
from core.context_tracker import ContextTracker
from core.skill_manager import execute_skill, build_skill_prompt
from core.runtime_dir import resolve_path, get_runtime_dir
from display.panel import divider, role_tag
from display import StreamRenderer
import constants
import utils.inited as inited


# ── 全局会话管理 ──
_sessions = {}
_active_session_id = None


def _flush_input():
    """清空输入缓冲区，防止生成过程中的误触"""
    if msvcrt:
        while msvcrt.kbhit():
            msvcrt.getch()


def _ensure_utf8():
    """强制输出流为 UTF-8"""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _readline_prompt(prompt_str: str) -> str:
    """兼容不同编码的输入读取"""
    print(prompt_str, end="", flush=True)
    try:
        raw = sys.stdin.buffer.readline()
        if not raw:
            return ""
        enc = getattr(sys.stdin, 'encoding', None) or 'utf-8'
        return raw.decode(enc, errors='replace').rstrip('\r\n')
    except Exception:
        return ""


def _load_coder_config():
    """读取 Coder 角色的 API 配置"""
    if not inited.is_inited():
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} 未初始化，请先执行 code init boot")
        return None
    try:
        with open(inited.maren_json_path(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} maren.json 不存在: {inited.maren_json_path()}")
        return None
    except json.JSONDecodeError as e:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} maren.json 格式错误: {e}")
        return None
    except Exception as e:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} 读取 maren.json 失败: {type(e).__name__}: {e}")
        return None
    lang = config.get("lang", "zh-CN")
    mc = config.get("model", {})
    base_url = mc.get("base_url")
    api_key = mc.get("api_key", {}).get("coder")
    model_name = mc.get("coder", {}).get("model_name")
    max_tokens = mc.get("coder", {}).get("max_tokens", 8192)
    if not base_url or not api_key or not model_name:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Coder 模型配置缺失")
        return None
    return base_url, api_key, model_name, lang, max_tokens


def _load_project_name() -> str:
    """从 .maren/project.json 读取项目名称，回退为当前目录名"""
    try:
        with open(inited.project_json_path(), "r", encoding="utf-8") as f:
            proj = json.load(f)
            name = proj.get("name", "").strip()
            if name:
                return name
    except Exception:
        pass
    return os.path.basename(os.getcwd()) or "未命名项目"


# ── 会话类 ──
class RunSession:
    """run enter 的单个会话"""

    def __init__(self, project_name: str, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.project_name = project_name
        self.history = []
        self.created = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.tracker = ContextTracker(max_tokens=128000)

    def to_dict(self):
        return {
            "id": self.session_id,
            "project": self.project_name,
            "history_len": len(self.history),
            "created": self.created,
        }


def _compress_history(history, base_url, api_key, model_name, lang):
    """超出阈值时压缩旧消息，保留最近轮次"""
    max_chars = 6000
    keep_recent = 4
    total = sum(len(m.get("content") or "") for m in history)
    if total <= max_chars:
        return history
    keep_count = keep_recent * 2
    recent = history[-keep_count:] if len(history) > keep_count else history
    older = history[:-keep_count]
    if not older:
        return recent
    # 压缩旧消息为摘要
    lines = []
    for m in older:
        role = "用户" if m.get("role") == "user" else "助手"
        lines.append(f"{role}: {(m.get('content') or '')[:200]}")
    summary_prompt = f"请将以下对话压缩成简洁摘要，保留关键事实与待办，使用 {lang} 输出。"
    content_text = "\n".join(lines)
    parts = []
    try:
        for chunk in request.chat_complete(base_url, api_key, model_name, summary_prompt, [], content_text):
            parts.append(chunk)
    except Exception as e:
        print(f"{prefix()}{Fore.LIGHTBLACK_EX}[WARN] 历史压缩失败: {type(e).__name__}: {e}{Style.RESET_ALL}")
        return recent
    summary = "".join(parts).strip()
    if not summary:
        return recent
    return [{"role": "system", "content": f"对话摘要：{summary}"}] + recent


def _stream_reply(message, base_url, api_key, model_name, lang, history, tracker, project_name):
    """流式调用 AI 并渲染输出，返回完整回复文本"""
    skill_prompt = build_skill_prompt("Coder")
    lang_hint = f"对话默认使用 {lang}，除非用户明确指定其他语言。"
    system_prompt = (
        f"{constants.BASE_SYSTEM}\n{constants.CODER_SYSTEM}\n"
        f"{skill_prompt}\n{lang_hint}\n"
        f"当前项目: {project_name}"
    )

    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    role_label = f" {Style.BRIGHT}{Fore.LIGHTGREEN_EX}[ Coder ]{Style.RESET_ALL} "
    print(f"{cat}{role_label}", end="")

    parts = []
    renderer = StreamRenderer()

    # 如果最后一条是 system 消息（工具结果），引导 AI 继续
    actual_message = message
    if history and history[-1].get("role") == "system":
        actual_message = "请根据上述系统信息继续。"

    try:
        for chunk in request.chat_complete(
            base_url, api_key, model_name, system_prompt, history, actual_message
        ):
            parts.append(chunk)
            rendered = renderer.feed(chunk)
            if rendered:
                print(rendered, end="", flush=True)
    except Exception as exc:
        print()
        import traceback
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR] API 调用失败{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}类型: {type(exc).__name__}{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}详情: {exc}{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}模型: {model_name} | URL: {base_url}{Style.RESET_ALL}")
        return ""

    tail = renderer.finalize()
    if tail:
        print(tail, end="", flush=True)
    print()

    reply = "".join(parts)
    # 更新上下文追踪
    tracker.update(history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply}
    ], system_prompt)
    return reply


def _extract_tool_json(reply):
    """从回复中提取工具调用 JSON 字符串"""
    if "```tool_call" in reply:
        start = reply.find("```tool_call") + 12
        end = reply.find("```", start)
        if end != -1:
            return reply[start:end].strip()
    elif "```json" in reply:
        start = reply.find("```json") + 7
        end = reply.find("```", start)
        if end != -1:
            candidate = reply[start:end].strip()
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict) and obj.get("action"):
                    return candidate
            except Exception:
                pass
    return None


def _try_execute_tool(reply, history, base_url, api_key, model_name, lang, tracker, project_name):
    """
    多轮工具调用循环（最多 5 轮）
    每轮：提取工具调用 -> 执行 -> 注入结果 -> AI 继续回复
    如果执行了工具，返回 (True, 最终回复)；否则返回 (False, None)
    """
    max_rounds = 5
    ever_executed = False
    current_reply = reply

    for round_idx in range(max_rounds):
        raw_json = _extract_tool_json(current_reply)
        if not raw_json:
            break

        try:
            tool_call = json.loads(raw_json)
            action = tool_call.get("action")
            if not action:
                break
        except json.JSONDecodeError:
            break

        # 执行技能
        try:
            params = {k: v for k, v in tool_call.items() if k not in ("action", "msg")}
            result = execute_skill(action, **params)
            result_str = str(result)
            if len(result_str) > 8000:
                result_str = result_str[:8000] + "...(truncated)"
        except Exception as e:
            print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR] Tool '{action}' failed: {e}{Style.RESET_ALL}")
            break

        ever_executed = True

        # 将本轮 AI 回复和工具结果追加到历史
        history.append({"role": "assistant", "content": current_reply})
        sys_msg = (
            f"工具 ({action}) 执行结果：\n\n{result_str}\n\n"
            f"请根据以上结果继续完成用户的需求。如果还需要调用其他工具请继续，否则直接输出最终结果。"
        )
        history.append({"role": "system", "content": sys_msg})

        # AI 继续回复
        next_reply = _stream_reply(
            "请继续", base_url, api_key, model_name, lang,
            history, tracker, project_name
        )
        _flush_input()

        if not next_reply:
            break

        current_reply = next_reply

    # 将最终回复记录到历史
    if ever_executed and current_reply:
        history.append({"role": "assistant", "content": current_reply})

    return ever_executed, current_reply if ever_executed else None


def _print_enter_banner(project_name: str, session_id: str):
    """打印 run enter 模式的欢迎横幅"""
    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    DIM = Fore.LIGHTBLACK_EX
    ACCENT = '\033[38;5;222m'
    R = Style.RESET_ALL
    w = 58
    print()
    print(f"  {ACCENT}{'═' * w}{R}")
    print(f"  {cat} {Style.BRIGHT}{ACCENT}Maren Code · Project Dialog{R}")
    print(f"  {DIM}Project:{R} {Fore.CYAN}{project_name}{R}"
          f"    {DIM}Session:{R} {ACCENT}{session_id}{R}")
    print(f"  {ACCENT}{'═' * w}{R}")
    print(f"  {DIM}/new  New session  |  /list  List  |  "
          f"/switch <id>  Switch  |  exit  Quit{R}")
    print()


def _handle_slash_command(text, session):
    """
    处理 run enter 模式中的斜杠命令
    返回 True 表示已处理，False 表示不是命令
    """
    global _sessions, _active_session_id
    parts = text.strip().split()
    cmd = parts[0].lower()

    if cmd == "/new":
        # 创建新会话，复用当前项目名称，只清空历史
        current_name = session.project_name if session else "未命名项目"
        new_s = RunSession(current_name)
        _sessions[new_s.session_id] = new_s
        _active_session_id = new_s.session_id
        _print_enter_banner(current_name, new_s.session_id)
        return True

    if cmd == "/list":
        if not _sessions:
            print(f"{prefix()}暂无会话")
            return True
        print(f"\n{prefix()}{Style.BRIGHT}会话列表:{Style.RESET_ALL}")
        for sid, s in _sessions.items():
            marker = f"{Fore.GREEN}●{Style.RESET_ALL}" if sid == _active_session_id else " "
            print(f"  {marker} {Fore.YELLOW}{sid}{Style.RESET_ALL}"
                  f" {Fore.CYAN}{s.project_name}{Style.RESET_ALL}"
                  f" ({len(s.history)} 条消息, {s.created})")
        print()
        return True

    if cmd == "/switch" and len(parts) > 1:
        target = parts[1]
        if target in _sessions:
            _active_session_id = target
            s = _sessions[target]
            _print_enter_banner(s.project_name, s.session_id)
        else:
            print(f"{prefix()}{Fore.RED}会话 {target} 不存在{Style.RESET_ALL}")
        return True

    return False


def enter():
    """进入 run enter 交互式项目对话模式"""
    global _sessions, _active_session_id
    init(autoreset=True)
    _ensure_utf8()

    config = _load_coder_config()
    if not config:
        return
    base_url, api_key, model_name, lang, max_tokens = config

    # 首次进入：从 .maren/project.json 读取项目名称，无需手动输入
    if not _sessions:
        project_name = _load_project_name()
        session = RunSession(project_name)
        session.tracker = ContextTracker(max_tokens=128000)
        _sessions[session.session_id] = session
        _active_session_id = session.session_id
    else:
        session = _sessions[_active_session_id]

    _print_enter_banner(session.project_name, session.session_id)

    # 主循环
    while True:
        session = _sessions.get(_active_session_id)
        if not session:
            break

        # 构建提示符：项目名 + 上下文百分比
        ctx_info = session.tracker.render_inline()
        ACCENT = '\033[38;5;222m'
        R = Style.RESET_ALL
        prompt = (
            f"{Style.BRIGHT}{ACCENT}"
            f"[{session.project_name}]{R} "
            f"{ctx_info} "
            f"{ACCENT}run>{R} "
        )

        text = _readline_prompt(prompt).strip()
        if not text:
            continue

        # 退出
        if text.lower() == "exit":
            print(f"{prefix()}{Fore.YELLOW}已退出项目对话模式{Style.RESET_ALL}")
            break

        # 斜杠命令
        if text.startswith("/"):
            if _handle_slash_command(text, session):
                continue

        # 压缩历史
        session.history = _compress_history(
            session.history, base_url, api_key, model_name, lang
        )

        # 发送请求
        reply = _stream_reply(
            text, base_url, api_key, model_name, lang,
            session.history, session.tracker, session.project_name
        )
        _flush_input()

        if not reply:
            continue

        session.history.append({"role": "user", "content": text})

        # 尝试执行工具调用（最多 5 轮）
        tool_executed, final_reply = _try_execute_tool(
            reply, session.history, base_url, api_key,
            model_name, lang, session.tracker, session.project_name
        )
        if not tool_executed:
            session.history.append({"role": "assistant", "content": reply})


def _parse_file_blocks(text: str) -> list:
    """从 Coder 输出中提取 ```file:path``` 代码块"""
    blocks = []
    marker = "```file:"
    pos = 0
    while True:
        start = text.find(marker, pos)
        if start == -1:
            break
        path_start = start + len(marker)
        newline = text.find("\n", path_start)
        if newline == -1:
            break
        file_path = text[path_start:newline].strip()
        end = text.find("```", newline + 1)
        if end == -1:
            break
        content = text[newline + 1:end]
        blocks.append({"path": file_path, "content": content})
        pos = end + 3
    return blocks


def _write_files(blocks: list):
    """将解析出的文件块写入磁盘，路径相对于运行时项目根目录"""
    if not blocks:
        return
    for b in blocks:
        fpath = b["path"]
        content = b["content"]
        # 基于运行时目录解析路径
        fpath = resolve_path(fpath)
        try:
            dirn = os.path.dirname(fpath)
            if dirn:
                os.makedirs(dirn, exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            rel = os.path.relpath(fpath, get_runtime_dir())
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} 写入 {Fore.CYAN}{rel}{Style.RESET_ALL}")
        except PermissionError as e:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} 权限不足 {fpath}: {e}")
        except OSError as e:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} 文件系统错误 {fpath}: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} 写入失败 {fpath}: {type(e).__name__}: {e}")


def run(message: str):
    """执行 code run <描述> 一键全自动编程"""
    init(autoreset=True)

    # 检查是否是 enter 命令
    if message and message.strip().lower() == "enter":
        enter()
        return

    if not message or not message.strip():
        print(f"{prefix()}{Fore.RED}[ERROR]{Style.RESET_ALL} 请输入需求描述。")
        print(f"{prefix()}用法: code run <需求描述> | code run enter")
        return

    try:
        result = run_pipeline(message.strip())
    except KeyboardInterrupt:
        print(f"\n{prefix()}{Fore.YELLOW}已中断{Style.RESET_ALL}")
        return
    except Exception as e:
        import traceback
        print(f"{prefix()}{Fore.RED}[ERROR] Pipeline 执行失败{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}类型: {type(e).__name__}{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}详情: {e}{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}堆栈: {traceback.format_exc()}{Style.RESET_ALL}")
        return

    if result.get("status") == "error":
        print(f"{prefix()}{Fore.RED}{result.get('message', '未知错误')}{Style.RESET_ALL}")
        return

    # 提取并写入文件
    all_files = []
    for tid, r in result.get("results", {}).items():
        output = r.get("output", "")
        files = _parse_file_blocks(output)
        all_files.extend(files)

    if all_files:
        print()
        print(f"{prefix()}{Style.BRIGHT}生成文件:{Style.RESET_ALL}")
        _write_files(all_files)
    else:
        # 没有文件块，直接渲染输出
        print()
        renderer = StreamRenderer()
        for tid, r in sorted(result.get("results", {}).items()):
            tag = role_tag(r.get("role", ""))
            print(f"\n  {tag} 任务 #{tid}: {r.get('title', '')}")
            divider("─", 50)
            output = r.get("output", "")
            renderer.feed(output + "\n")
        tail = renderer.finalize()
        if tail:
            print(tail)

    print(f"\n{prefix()}{Fore.GREEN}完成。{Style.RESET_ALL}")
