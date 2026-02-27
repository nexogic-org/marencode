"""
pipeline/coder.py — Coder/Designer 代码执行模块
逐个任务执行，支持多轮工具调用，实时报告文件写入进度
"""
import os
import json
from colorama import Fore, Style
from core.agent import request
from core.runtime_dir import resolve_path, get_runtime_dir
from core.skill_manager import execute_skill, build_skill_prompt
from pipeline import dashboard
from pipeline.leader import _load_role_cfg
import constants
from pipeline.danger import check_dangerous


def parse_file_blocks(text: str) -> list:
    """从 Coder 输出中提取 ```file:path``` 代码块"""
    blocks = []
    marker = "```file:"
    pos = 0
    while True:
        start = text.find(marker, pos)
        if start == -1:
            break
        path_start = start + len(marker)
        nl = text.find("\n", path_start)
        if nl == -1:
            break
        fpath = text[path_start:nl].strip()
        end = text.find("```", nl + 1)
        if end == -1:
            break
        content = text[nl + 1:end]
        blocks.append({"path": fpath, "content": content})
        pos = end + 3
    return blocks


def write_files(blocks: list):
    """将文件块写入磁盘，路径相对于运行时项目根目录"""
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
            dashboard.file_written(rel)
        except Exception as e:
            dashboard.file_error(fpath, str(e))


def _extract_tool_call(text: str):
    """从 AI 输出中提取 tool_call JSON"""
    if "```tool_call" in text:
        start = text.find("```tool_call") + 12
        end = text.find("```", start)
        if end != -1:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    elif "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            candidate = text[start:end].strip()
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict) and obj.get("action"):
                    return obj
            except json.JSONDecodeError:
                pass
    return None


def _call_ai(rc, full_sys, history, user_msg, **kwargs):
    """调用 AI 并收集完整回复"""
    parts = []
    for chunk in request.chat_complete(
        rc["base_url"], rc["api_key"], rc["model_name"],
        full_sys, history, user_msg, **kwargs
    ):
        parts.append(chunk)
    return "".join(parts)


def _execute_role_task(task: dict, context: str, role: str, mode="quality"):
    """执行单个角色任务，支持多轮工具调用（搜索结果直接注入AI）"""
    cfg_role = "coder" if role == "designer" else role
    rc = _load_role_cfg(cfg_role)
    if not rc:
        return f"[ERROR] {role.capitalize()} 配置缺失"

    tid = task.get("id", "?")
    title = task.get("title", "")
    desc = task.get("description", title)
    phase = role if role in ("coder", "designer") else "coder"
    dashboard.phase_start(phase, f"任务 #{tid}: {title}")

    user_msg = f"任务: {desc}"
    if context:
        user_msg = f"项目上下文:\n{context}\n\n{user_msg}"

    # 根据角色选择系统提示词，并注入技能提示
    role_prompts = {
        "coder": constants.CODER_SYSTEM,
        "designer": constants.DESIGNER_SYSTEM,
    }
    sys_prompt = role_prompts.get(role, constants.CODER_SYSTEM)
    skill_prompt = build_skill_prompt("Coder")
    lang_hint = f"\n使用 {rc['lang']} 输出。"
    full_sys = (
        constants.BASE_SYSTEM + "\n" + sys_prompt
        + "\n" + skill_prompt + lang_hint
    )

    kwargs = {}
    if rc.get("temperature") is not None:
        kwargs["temperature"] = rc["temperature"]
    mt = rc.get("max_tokens", 8192)
    if mode == "saving":
        mt = min(mt, 2048)
    kwargs["max_tokens"] = mt

    # 第一轮调用
    history = []
    try:
        output = _call_ai(rc, full_sys, history, user_msg, **kwargs)
    except RuntimeError as e:
        dashboard.phase_error(phase, f"#{tid} API 错误: {e}")
        return f"[ERROR] {e}"
    except KeyboardInterrupt:
        dashboard.phase_error(phase, f"#{tid} 被用户中断")
        return f"[ERROR] 任务 #{tid} 被用户中断"
    except Exception as e:
        dashboard.phase_error(phase, f"#{tid} 未知异常: {type(e).__name__}: {e}")
        return f"[ERROR] {type(e).__name__}: {e}"

    # 多轮工具调用循环（最多 5 轮）
    # 搜索结果等工具输出直接注入 AI，不输出给用户
    max_tool_rounds = 5
    for _ in range(max_tool_rounds):
        tool_call = _extract_tool_call(output)
        if not tool_call:
            break

        action = tool_call.get("action")
        if not action:
            break

        # 静默执行工具
        msg = tool_call.get("msg", "")
        if msg:
            dashboard.phase_start(phase, f"#{tid} ⚡ {msg}")

        try:
            params = {k: v for k, v in tool_call.items()
                      if k not in ("action", "msg")}
            result = execute_skill(action, **params)
            result_str = str(result)
            if len(result_str) > 8000:
                result_str = result_str[:8000] + "...(truncated)"
        except Exception as e:
            dashboard.phase_error(phase, f"#{tid} 工具 '{action}' 失败: {e}")
            break

        # 将工具结果注入历史，让 AI 继续
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": output})
        history.append({"role": "system", "content": (
            f"工具 ({action}) 执行结果：\n\n{result_str}\n\n"
            f"请根据以上结果继续完成任务。"
            f"如果还需要调用其他工具请继续，否则直接输出最终结果。"
        )})

        try:
            output = _call_ai(
                rc, full_sys, history, "请继续", **kwargs
            )
        except Exception as e:
            dashboard.phase_error(phase, f"#{tid} 工具后续调用失败: {e}")
            break

    # 危险命令检查
    dangers = check_dangerous(output)
    if dangers:
        dashboard.danger_warning(", ".join(dangers))

    # 解析并写入文件
    blocks = parse_file_blocks(output)
    if blocks:
        write_files(blocks)

    dashboard.phase_done(phase, f"#{tid} 完成")
    return output


def execute_task(task: dict, context: str, mode="quality"):
    """执行单个 Coder 任务，返回输出文本"""
    return _execute_role_task(task, context, "coder", mode)


def execute_designer_task(task: dict, context: str, mode="quality"):
    """执行单个 Designer 任务，返回输出文本"""
    return _execute_role_task(task, context, "designer", mode)
