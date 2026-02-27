"""
pipeline/chatter.py — Chatter 需求收集模块
与用户交互式对话，收集项目需求细节
"""
import sys
import json
from colorama import Fore, Style
from core.agent import request
from pipeline import dashboard
import constants
import utils.inited as inited


try:
    import msvcrt
except ImportError:
    msvcrt = None


def _flush_input():
    if msvcrt:
        while msvcrt.kbhit():
            msvcrt.getch()


def _load_chatter_cfg():
    """加载 Chatter 角色配置"""
    try:
        with open(inited.maren_json_path(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return None
    mc = config.get("model", {})
    base_url = mc.get("base_url")
    api_key = mc.get("api_key", {}).get("chatter")
    model_name = mc.get("chatter", {}).get("model_name")
    lang = config.get("lang", "zh-CN")
    if not base_url or not api_key or not model_name:
        return None
    return base_url, api_key, model_name, lang


def _readline_prompt(prompt: str) -> str:
    print(prompt, end="", flush=True)
    try:
        raw = sys.stdin.buffer.readline()
        if not raw:
            return ""
        enc = getattr(sys.stdin, 'encoding', None) or 'utf-8'
        return raw.decode(enc, errors='replace').rstrip('\r\n')
    except Exception:
        return ""


CHATTER_GATHER_PROMPT = """你现在是需求收集助手。你的任务是与用户深入交流，收集完整的项目需求。

## 你必须做到：
1. 主动询问项目的目标、功能、技术栈、UI需求
2. 确认边界条件、异常处理、性能要求
3. 如果用户描述模糊，追问细节
4. 每轮对话结束时总结已收集的需求

## 当你认为需求已经足够清晰时：
输出 `[REQUIREMENTS_DONE]` 标记，后面跟完整的需求文档。

## 输出格式（仅在需求收集完成时）：
[REQUIREMENTS_DONE]
```json
{
  "project_name": "项目名",
  "summary": "一句话概述",
  "requirements": ["需求1", "需求2"],
  "tech_stack": ["技术1"],
  "ui_needs": true/false,
  "details": "详细需求描述"
}
```
"""


def _call_chatter(base_url, api_key, model_name, system, history, msg):
    """调用 Chatter AI 并收集完整回复"""
    parts = []
    try:
        for chunk in request.chat_complete(
            base_url, api_key, model_name, system, history, msg
        ):
            parts.append(chunk)
            print(chunk, end="", flush=True)
    except RuntimeError as e:
        print(f"\n  {Fore.RED}[API ERROR] {e}{Style.RESET_ALL}")
        return "".join(parts)  # 返回已收到的部分内容
    except KeyboardInterrupt:
        print(f"\n  {Fore.YELLOW}[中断] 用户取消请求{Style.RESET_ALL}")
        return "".join(parts)
    except Exception as e:
        print(f"\n  {Fore.RED}[ERROR] {type(e).__name__}: {e}{Style.RESET_ALL}")
        return "".join(parts)
    print()
    return "".join(parts)


def gather_requirements(initial_msg: str):
    """与用户交互收集需求，返回需求文档 dict"""
    cfg = _load_chatter_cfg()
    if not cfg:
        print(f"  {Fore.RED}[ERROR] Chatter 配置缺失{Style.RESET_ALL}")
        return None
    base_url, api_key, model_name, lang = cfg
    lang_hint = f"\n使用 {lang} 与用户交流。"
    system = constants.BASE_SYSTEM + constants.load_memory_prompt() + CHATTER_GATHER_PROMPT + lang_hint
    dashboard.phase_start("chatter", "正在与您交流需求细节...")
    history = []
    prompt = f"  {Fore.LIGHTMAGENTA_EX}you>{Style.RESET_ALL} "

    # 第一轮：AI 先分析用户的初始需求
    chatter_tag = (
        f"  {dashboard.CAT}"
        f" {Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}[ Chatter ]{Style.RESET_ALL} "
    )
    print(chatter_tag, end="")
    reply = _call_chatter(base_url, api_key, model_name, system, history, initial_msg)
    _flush_input()
    history.append({"role": "user", "content": initial_msg})
    history.append({"role": "assistant", "content": reply})

    # 多轮对话循环
    max_rounds = 10
    for _ in range(max_rounds):
        # 检查是否已完成需求收集
        if "[REQUIREMENTS_DONE]" in reply:
            return _parse_requirements(reply)

        # 用户继续输入
        user_input = _readline_prompt(prompt).strip()
        if not user_input:
            continue
        if user_input.lower() in ("done", "完成", "ok", "确认"):
            # 用户主动结束，让 AI 总结
            user_input = "需求已经足够了，请输出完整需求文档。"

        print(chatter_tag, end="")
        reply = _call_chatter(base_url, api_key, model_name, system, history, user_input)
        _flush_input()
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": reply})

        if "[REQUIREMENTS_DONE]" in reply:
            return _parse_requirements(reply)

    # 超过最大轮次，强制总结
    print(chatter_tag, end="")
    force_msg = "请立即输出完整需求文档，使用 [REQUIREMENTS_DONE] 标记。"
    reply = _call_chatter(base_url, api_key, model_name, system, history, force_msg)
    dashboard.phase_done("chatter", "需求收集完成")
    return _parse_requirements(reply)


def _parse_requirements(text: str) -> dict:
    """从 AI 回复中提取需求 JSON"""
    # 尝试提取 JSON 块
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    # 尝试直接解析
    if "{" in text:
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end])
            except json.JSONDecodeError:
                pass
    # 回退：用原始文本构造
    return {
        "project_name": "用户项目",
        "summary": text[:200],
        "requirements": [text],
        "tech_stack": [],
        "ui_needs": False,
        "details": text
    }
