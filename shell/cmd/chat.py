import json
import sys
try:
    import msvcrt
except ImportError:
    msvcrt = None
from colorama import Fore, Style, init
from core.agent import request
import constants
from shell.cmd import prefix
from display import StreamRenderer
from core.skill_manager import execute_skill
from core.context_tracker import ContextTracker
import utils.inited as inited

def _flush_input():
    # 在 Windows 下清空输入缓冲区，防止生成过程中的误触或多余回车被读取
    if msvcrt:
        while msvcrt.kbhit():
            msvcrt.getch()

def _print_tool_result(action: str, result_str: str):
    """打印工具执行结果给用户看"""
    DIM = Fore.LIGHTBLACK_EX
    R = Style.RESET_ALL
    if result_str.startswith("[OK]"):
        icon = f"{Fore.GREEN}✓{R}"
    elif result_str.startswith("[ERROR]"):
        icon = f"{Fore.RED}✗{R}"
    else:
        icon = f"{Fore.CYAN}→{R}"
    first_line = result_str.split("\n")[0][:120]
    print(f"  {icon} {DIM}[{action}]{R} {first_line}")


def _load_chatter_config():
    # 读取本地配置并校验必填字段，支持角色独立 base_url
    if not inited.is_inited():
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Maren code uninitialized. Use \"code init boot\".")
        return None
    try:
        with open(inited.maren_json_path(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} maren.json not found: {inited.maren_json_path()}")
        return None
    except json.JSONDecodeError as e:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} maren.json format error: {e}")
        return None
    except Exception as e:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to read maren.json: {type(e).__name__}: {e}")
        return None
    lang = config.get("lang")
    model_config = config.get("model", {})
    # 优先使用角色独立 base_url，回退到全局
    role_urls = model_config.get("role_base_urls", {})
    base_url = role_urls.get("chatter") or model_config.get("base_url")
    api_key = model_config.get("api_key", {}).get("chatter")
    model_name = model_config.get("chatter", {}).get("model_name")
    if not base_url or not api_key or not model_name:
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Chatter model config is missing.")
        return None
    return base_url, api_key, model_name, lang

def _ensure_utf8():
    # 强制输出流为 UTF-8，避免中文显示异常
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def _readline_prompt(prompt: str) -> str:
    # 兼容不同编码的输入读取，避免 UnicodeDecodeError
    print(prompt, end="", flush=True)
    try:
        raw = sys.stdin.buffer.readline()
        if not raw:
            return ""
        if raw.startswith(b'\xff\xfe'):
            return raw.decode('utf-16-le', errors='replace').rstrip('\r\n')
        if raw.startswith(b'\xfe\xff'):
            return raw.decode('utf-16-be', errors='replace').rstrip('\r\n')
        enc = getattr(sys.stdin, 'encoding', None) or 'utf-8'
        try:
            text = raw.decode(enc, errors='replace').rstrip('\r\n')
        except Exception:
            text = raw.decode('utf-8', errors='replace').rstrip('\r\n')
        return text
    except Exception:
        return ""

def _history_char_count(history):
    # 统计上下文长度用于压缩判断
    total = 0
    for item in history:
        total += len(item.get("content") or "")
    return total

def _summarize_history(history, base_url: str, api_key: str, model_name: str, lang: str):
    # 将历史对话压缩成摘要，只保留关键事实，节省 token
    if not history:
        return None
    lines = []
    for item in history:
        role = item.get("role", "")
        label = "用户" if role == "user" else "助手"
        content = (item.get("content") or "")[:300]  # 每条截断300字符
        lines.append(f"{label}: {content}")
    summary_prompt = (
        f"将以下对话压缩为极简摘要（不超过200字），"
        f"只保留关键事实、结论和待办，删除寒暄和重复内容。"
        f"使用 {lang} 输出。"
    )
    content_text = "\n".join(lines)
    parts = []
    try:
        for chunk in request.chat_complete(
            base_url, api_key, model_name, summary_prompt, [],
            content_text, max_tokens=512
        ):
            parts.append(chunk)
    except Exception as e:
        print(f"{prefix()}{Fore.LIGHTBLACK_EX}[WARN] 历史压缩失败: {type(e).__name__}: {e}{Style.RESET_ALL}")
        return None
    summary = "".join(parts).strip()
    return summary or None

def _compress_history(history, base_url: str, api_key: str, model_name: str, lang: str):
    # 智能压缩：分级策略，优先截断再摘要
    max_chars = 6000
    keep_recent_pairs = 3  # 保留最近3轮
    total = _history_char_count(history)
    if total <= max_chars:
        return history

    keep_count = keep_recent_pairs * 2
    recent = history[-keep_count:] if len(history) > keep_count else history
    older = history[:-keep_count]

    # 第一级：如果旧消息不多，直接截断每条内容
    if len(older) <= 6:
        truncated = []
        for m in older:
            content = (m.get("content") or "")[:200]
            truncated.append({"role": m["role"], "content": content})
        return truncated + recent

    # 第二级：旧消息较多，调用 AI 压缩为摘要
    summary = _summarize_history(older, base_url, api_key, model_name, lang)
    if not summary:
        return recent
    return [{"role": "system", "content": f"对话摘要：{summary}"}] + recent

def _stream_reply(message: str, base_url: str, api_key: str, model_name: str, lang: str, history, char_mode: bool, show_cat: bool = True):
    # 逐块渲染：加粗、列表符号与代码高亮都在渲染器里完成
    lang_prompt = f"对话默认使用 {lang}，除非用户明确指定其他语言。"
    system_prompt = f"{constants.BASE_SYSTEM}\n{constants.CHATTER_SYSTEM}\n{lang_prompt}"
    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    role_label = f" {Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}[ Chatter ]{Style.RESET_ALL} "
    
    if "\n" in message and show_cat:
        print()
    
    if show_cat:
        print(f"{cat}{role_label}", end="")
    
    parts = []
    renderer = StreamRenderer()
    
    # 处理工具调用后的 system 消息引导
    actual_message = message
    if history and history[-1].get("role") == "system":
        actual_message = "请根据上述系统信息回答我的问题。"
    
    try:
        for chunk in request.chat_complete(base_url, api_key, model_name, system_prompt, history, actual_message):
            parts.append(chunk)
            rendered = renderer.feed(chunk)
            if rendered:
                # 按块输出，减少逐字符打印带来的性能开销
                print(rendered, end="", flush=True)
    except Exception as exc:
        print()
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR] API 调用失败{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}类型: {type(exc).__name__}{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}详情: {exc}{Style.RESET_ALL}")
        print(f"  {Fore.LIGHTBLACK_EX}模型: {model_name} | URL: {base_url}{Style.RESET_ALL}")
        return ""
    tail = renderer.finalize()
    if tail:
        print(tail, end="", flush=True)
    print()
    return "".join(parts)

def run(message: str):
    # 单句模式：chat "..."
    init(autoreset=True)
    _ensure_utf8()
    if not message or not message.strip():
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Missing chat message.")
        return
    config = _load_chatter_config()
    if not config:
        return
    base_url, api_key, model_name, lang = config
    
    # 单句模式也需要支持工具调用循环
    # 初始请求
    reply = _stream_reply(message, base_url, api_key, model_name, lang, [], True)
    
    # 循环检测工具调用
    # 限制最大轮次以防死循环
    max_turns = 5
    current_turn = 0
    
    # 临时历史，用于多轮对话
    # 第一轮：User -> Assistant (Reply)
    temp_history = [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply}
    ]
    
    while current_turn < max_turns:
        current_turn += 1
        
        # 尝试从回复中提取工具调用 JSON
        real_json_content = None
        if "```tool_call" in reply:
            start = reply.find("```tool_call") + 12
            end = reply.find("```", start)
            if end != -1:
                real_json_content = reply[start:end].strip()
        elif "```json" in reply:
            start = reply.find("```json") + 7
            end = reply.find("```", start)
            if end != -1:
                real_json_content = reply[start:end].strip()
        elif reply.strip().startswith("{") and reply.strip().endswith("}"):
            real_json_content = reply.strip()
            
        if not real_json_content:
            break
            
        try:
            tool_call = json.loads(real_json_content)
            action = tool_call.get("action")
            if not action:
                break

            # 通用技能调度，不再硬编码 read_url
            try:
                params = {k: v for k, v in tool_call.items() if k not in ("action", "msg")}
                result = execute_skill(action, **params)
                
                result_str = str(result)
                if len(result_str) > 8000:
                    result_str = result_str[:8000] + "...(truncated)"
                
                _print_tool_result(action, result_str)
                
                sys_msg = f"工具 ({action}) 执行结果：\n\n{result_str}\n\n请根据以上结果回答用户刚才的问题。"
                temp_history.append({"role": "system", "content": sys_msg})
                
                reply = _stream_reply("请继续", base_url, api_key, model_name, lang, temp_history, True, show_cat=False)
                temp_history.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR] Tool '{action}' failed: {type(e).__name__}: {e}{Style.RESET_ALL}")
                break
        except json.JSONDecodeError:
            break
        except Exception as e:
            print(f"{prefix()}{Fore.LIGHTBLACK_EX}[WARN] Tool parsing error: {type(e).__name__}: {e}{Style.RESET_ALL}")
            break

def enter():
    # 连续聊天模式：chat enter，输入 exit 退出
    init(autoreset=True)
    _ensure_utf8()
    config = _load_chatter_config()
    if not config:
        return
    base_url, api_key, model_name, lang = config
    history = []
    tracker = ContextTracker(max_tokens=128000)

    while True:
        # 动态提示符：包含上下文使用百分比
        ctx_info = tracker.render_inline()
        ACCENT = '\033[38;5;222m'
        R = Style.RESET_ALL
        prompt = f"{ctx_info} {Style.BRIGHT}{ACCENT}chat>{R} "
        text = _readline_prompt(prompt)
        
        # 修复：防止粘贴多行文本包含 prompt 导致无限循环请求
        # 如果是粘贴的内容，可能会包含 chat> 或 >>，需要过滤掉
        # 同时也去除首尾空白
        clean_text = text.replace("chat>", "").replace(">>", "").strip()
        
        if not clean_text:
            continue
            
        if clean_text.lower() == "exit":
            break
            
        history = _compress_history(history, base_url, api_key, model_name, lang)
        # 使用过滤后的 clean_text 发送请求
        reply = _stream_reply(clean_text, base_url, api_key, model_name, lang, history, True)
        
        # AI 响应期间忽略用户误触
        _flush_input()
        
        if reply:
            history.append({"role": "user", "content": clean_text})
            tracker.update(history + [{"role": "assistant", "content": reply}])
            
            # 检测是否包含工具调用指令
            real_json_content = None
            if "```tool_call" in reply:
                start = reply.find("```tool_call") + 12
                end = reply.find("```", start)
                if end != -1:
                    real_json_content = reply[start:end].strip()
            elif "```json" in reply:
                start = reply.find("```json") + 7
                end = reply.find("```", start)
                if end != -1:
                    real_json_content = reply[start:end].strip()
            elif reply.strip().startswith("{") and reply.strip().endswith("}"):
                real_json_content = reply.strip()
            
            tool_executed = False
            if real_json_content:
                try:
                    tool_call = json.loads(real_json_content)
                    action = tool_call.get("action")
                    
                    if action:
                        try:
                            params = {k: v for k, v in tool_call.items() if k not in ("action", "msg")}
                            result = execute_skill(action, **params)
                            
                            result_str = str(result)
                            if len(result_str) > 8000:
                                result_str = result_str[:8000] + "...(truncated)"
                            
                            _print_tool_result(action, result_str)
                                
                            sys_msg = f"工具 ({action}) 执行结果：\n\n{result_str}\n\n请根据以上结果回答用户的问题。"
                            
                            # 记录原始回复（AI 的工具调用指令）
                            history.append({"role": "assistant", "content": reply})
                            
                            temp_history = history.copy()
                            temp_history.append({"role": "system", "content": sys_msg})
                            
                            final_reply = _stream_reply("请继续", base_url, api_key, model_name, lang, temp_history, True, show_cat=False)
                            _flush_input()
                            
                            if final_reply:
                                history.append({"role": "assistant", "content": final_reply})
                                tool_executed = True
                                
                        except Exception as e:
                            print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR] Tool '{action}' failed: {type(e).__name__}: {e}{Style.RESET_ALL}")
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR] Tool parsing failed: {type(e).__name__}: {e}{Style.RESET_ALL}")

            if not tool_executed:
                history.append({"role": "assistant", "content": reply})
