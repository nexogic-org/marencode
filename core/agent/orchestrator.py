"""
core/agent/orchestrator.py — 多智能体并行协作引擎
Leader 规划 → Coder/Tester 并行执行 → 结果汇总
"""
import json
import threading
import time
from typing import Dict, List, Optional
from colorama import Fore, Style

from core.agent import request
from display.panel import (
    divider, role_tag, progress_bar,
    status_line, task_panel
)
import constants


def _load_config():
    """加载 maren.json 配置"""
    import utils.inited as inited
    config_path = inited.maren_json_path()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  {Fore.RED}[ERROR] 配置文件不存在: {config_path}{Style.RESET_ALL}")
        return None
    except json.JSONDecodeError as e:
        print(f"  {Fore.RED}[ERROR] maren.json 格式错误: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"  {Fore.RED}[ERROR] 读取 maren.json 失败: {e}{Style.RESET_ALL}")
        return None


def _get_role_config(config: dict, role: str):
    """获取指定角色的 API 配置，支持角色独立 base_url"""
    model_cfg = config.get("model", {})
    # 优先使用角色独立 base_url，回退到全局
    role_urls = model_cfg.get("role_base_urls", {})
    base_url = role_urls.get(role) or model_cfg.get("base_url")
    api_key = model_cfg.get("api_key", {}).get(role)
    role_cfg = model_cfg.get(role, {})
    model_name = role_cfg.get("model_name")
    temperature = role_cfg.get("temperature")
    max_tokens = role_cfg.get("max_tokens")
    if not base_url or not api_key or not model_name:
        return None
    return {
        "base_url": base_url,
        "api_key": api_key,
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _call_role(role: str, system_prompt: str, user_msg: str,
               config: dict, lang: str) -> str:
    """同步调用单个角色，返回完整回复文本"""
    rc = _get_role_config(config, role)
    if not rc:
        return f"[ERROR] {role} 配置缺失"
    lang_hint = f"\n使用 {lang} 输出。" if lang else ""
    full_system = f"{constants.BASE_SYSTEM}\n{system_prompt}{lang_hint}"
    parts = []
    try:
        for chunk in request.chat_complete(
            rc["base_url"], rc["api_key"], rc["model_name"],
            full_system, [], user_msg,
            temperature=rc.get("temperature"),
            max_tokens=rc.get("max_tokens"),
        ):
            parts.append(chunk)
    except RuntimeError as e:
        return f"[ERROR] {role} API 错误: {e}"
    except KeyboardInterrupt:
        partial = "".join(parts)
        return partial if partial else f"[ERROR] {role} 被用户中断"
    except Exception as e:
        return f"[ERROR] {role} 未知异常 ({type(e).__name__}): {e}"
    return "".join(parts)


def _parse_leader_plan(text: str) -> Optional[dict]:
    """从 Leader 回复中提取 JSON 任务计划"""
    # 尝试从代码块中提取
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    # 尝试直接解析
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return None


class TaskResult:
    """单个任务的执行结果"""
    def __init__(self, task_id: int, role: str, title: str):
        self.task_id = task_id
        self.role = role
        self.title = title
        self.status = "pending"
        self.output = ""
        self.error = ""


def _execute_task(task: dict, config: dict, lang: str,
                  result: TaskResult, context: str = ""):
    """在线程中执行单个任务"""
    role = task.get("role", "Coder").lower()
    desc = task.get("description", task.get("title", ""))

    role_prompts = {
        "coder": constants.CODER_SYSTEM,
        "designer": constants.DESIGNER_SYSTEM,
        "tester": constants.TESTER_SYSTEM,
        "leader": constants.LEADER_SYSTEM,
    }
    sys_prompt = role_prompts.get(role, constants.CODER_SYSTEM)

    user_msg = f"任务: {desc}"
    if context:
        user_msg = f"项目上下文:\n{context}\n\n{user_msg}"

    result.status = "running"
    try:
        output = _call_role(role, sys_prompt, user_msg, config, lang)
        result.output = output
        if output.startswith("[ERROR]"):
            result.status = "error"
            result.error = output
        else:
            result.status = "done"
    except Exception as e:
        import traceback
        result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        result.status = "error"
        print(f"  {Fore.RED}[ERROR] 任务 #{result.task_id} ({role}) 执行异常: {e}{Style.RESET_ALL}")


def _run_parallel_tasks(tasks: list, config: dict, lang: str,
                        context: str = "") -> List[TaskResult]:
    """并行执行一批无依赖的任务"""
    results = []
    threads = []
    for t in tasks:
        r = TaskResult(t["id"], t.get("role", "Coder"), t.get("title", ""))
        results.append(r)
        th = threading.Thread(
            target=_execute_task,
            args=(t, config, lang, r, context),
            daemon=True
        )
        threads.append(th)

    # 启动所有线程
    for th in threads:
        th.start()

    # 等待完成，实时打印状态
    while any(th.is_alive() for th in threads):
        time.sleep(0.5)
        _print_live_status(results)

    # 最终状态
    _print_live_status(results, final=True)
    return results


def _print_live_status(results: List[TaskResult], final=False):
    """打印任务实时状态"""
    done = sum(1 for r in results if r.status == "done")
    total = len(results)
    bar = progress_bar(done, total, width=30, label="进度")
    if not final:
        print(f"\r  {bar} ({done}/{total})", end="", flush=True)
    else:
        print(f"\r  {bar} ({done}/{total})")
        print()


def _topological_layers(tasks: list) -> List[List[dict]]:
    """将任务按依赖关系分成可并行执行的层"""
    task_map = {t["id"]: t for t in tasks}
    done_ids = set()
    layers = []
    remaining = list(tasks)

    while remaining:
        # 找出所有依赖已满足的任务
        layer = []
        for t in remaining:
            deps = t.get("depends_on", [])
            if all(d in done_ids for d in deps):
                layer.append(t)
        if not layer:
            # 有循环依赖，强制执行剩余任务
            layer = remaining[:]
        for t in layer:
            remaining.remove(t)
            done_ids.add(t["id"])
        layers.append(layer)

    return layers


def run_pipeline(user_request: str) -> dict:
    """
    完整的多智能体协作流水线
    1. Leader 规划任务
    2. 按依赖关系分层并行执行
    3. Tester 审查
    4. 汇总输出
    """
    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    config = _load_config()
    if not config:
        print(f"  {cat} {Fore.RED}[ERROR] 配置未初始化{Style.RESET_ALL}")
        return {"status": "error", "message": "配置未初始化"}

    lang = config.get("lang", "zh-CN")

    # ── Phase 1: Leader 规划 ──
    print()
    divider("═", 56, Fore.LIGHTYELLOW_EX)
    print(f"  {cat} {Style.BRIGHT}Maren Code 多智能体协作引擎{Style.RESET_ALL}")
    divider("═", 56, Fore.LIGHTYELLOW_EX)
    print()
    status_line("Leader", "正在分析需求并规划任务...", "running")

    leader_reply = _call_role(
        "leader", constants.LEADER_SYSTEM,
        user_request, config, lang
    )
    plan = _parse_leader_plan(leader_reply)

    if not plan or "tasks" not in plan:
        status_line("Leader", "规划失败，回退为单任务模式", "error")
        # 回退：直接让 Coder 处理
        plan = {
            "project_name": "直接执行",
            "summary": user_request,
            "tasks": [{
                "id": 1, "title": user_request,
                "description": user_request,
                "role": "Coder", "priority": "high",
                "depends_on": []
            }]
        }

    status_line("Leader", f"规划完成 — {len(plan['tasks'])} 个任务", "done")

    # 展示任务面板
    task_panel(
        plan.get("project_name", "项目"),
        [{"id": t["id"], "title": t["title"],
          "role": t.get("role", "Coder"), "status": "pending"}
         for t in plan["tasks"]]
    )

    # ── Phase 2: 按依赖分层并行执行 ──
    tasks = plan["tasks"]
    all_results: Dict[int, TaskResult] = {}
    context = plan.get("summary", user_request)

    # 拓扑分层：将任务按依赖关系分成多个批次
    layers = _topological_layers(tasks)

    for layer_idx, layer in enumerate(layers):
        print(f"  {Style.BRIGHT}{Fore.CYAN}── 第 {layer_idx+1}/{len(layers)} 批 ({len(layer)} 个任务并行) ──{Style.RESET_ALL}")
        # 构建上下文：包含前序任务的输出
        prev_context = context
        for tid, r in all_results.items():
            if r.status == "done":
                prev_context += f"\n\n[任务#{tid} {r.title} 输出]:\n{r.output[:2000]}"

        results = _run_parallel_tasks(layer, config, lang, prev_context)
        for r in results:
            all_results[r.task_id] = r
            st = "done" if r.status == "done" else "error"
            status_line(r.role, f"#{r.task_id} {r.title}", st)

    # ── Phase 3: 汇总结果 ──
    print()
    divider("═", 56, Fore.LIGHTGREEN_EX)
    print(f"  {cat} {Style.BRIGHT}{Fore.LIGHTGREEN_EX}执行完成{Style.RESET_ALL}")
    divider("═", 56, Fore.LIGHTGREEN_EX)

    outputs = {}
    for tid, r in sorted(all_results.items()):
        outputs[tid] = {
            "title": r.title,
            "role": r.role,
            "status": r.status,
            "output": r.output,
        }

    return {
        "status": "done",
        "plan": plan,
        "results": outputs,
    }
