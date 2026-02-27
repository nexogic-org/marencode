"""
pipeline/leader.py — Leader 任务规划与 Bug 修复拆分
"""
import json
from colorama import Fore, Style
from core.agent import request
from pipeline import dashboard
import constants
import utils.inited as inited
from shell.cmd.config import get_config, get_role_model_override


def _load_role_cfg(role: str):
    """加载指定角色的 API 配置，支持角色独立 base_url"""
    try:
        with open(inited.maren_json_path(), "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return None
    mc = config.get("model", {})
    # 优先使用角色独立 base_url，回退到全局
    role_urls = mc.get("role_base_urls", {})
    base_url = role_urls.get(role) or mc.get("base_url")
    api_key = mc.get("api_key", {}).get(role)
    model_name = mc.get(role, {}).get("model_name")
    # 检查是否有模型覆盖
    override = get_role_model_override(role)
    if override:
        model_name = override
    lang = config.get("lang", "zh-CN")
    temp = mc.get(role, {}).get("temperature")
    max_tok = mc.get(role, {}).get("max_tokens")
    if not base_url or not api_key or not model_name:
        return None
    return {
        "base_url": base_url, "api_key": api_key,
        "model_name": model_name, "lang": lang,
        "temperature": temp, "max_tokens": max_tok
    }


def _call_role(role, system, msg, mode="quality"):
    """调用指定角色 AI，返回完整回复"""
    rc = _load_role_cfg(role)
    if not rc:
        return f"[ERROR] {role} 配置缺失"
    lang_hint = f"\n使用 {rc['lang']} 输出。"
    full_sys = constants.BASE_SYSTEM + constants.load_memory_prompt() + "\n" + system + lang_hint
    kwargs = {}
    if rc.get("temperature") is not None:
        kwargs["temperature"] = rc["temperature"]
    if rc.get("max_tokens") is not None:
        mt = rc["max_tokens"]
        if mode == "saving":
            mt = min(mt, 2048)
        kwargs["max_tokens"] = mt
    parts = []
    try:
        for chunk in request.chat_complete(
            rc["base_url"], rc["api_key"], rc["model_name"],
            full_sys, [], msg, **kwargs
        ):
            parts.append(chunk)
    except RuntimeError as e:
        # API 层面的明确错误（连接失败、超时、HTTP 错误等）
        return f"[ERROR] {role} 调用失败: {e}"
    except KeyboardInterrupt:
        # 用户中断，返回已收集的部分内容
        partial = "".join(parts)
        return partial if partial else f"[ERROR] {role} 被用户中断"
    except Exception as e:
        return f"[ERROR] {role} 未知异常 ({type(e).__name__}): {e}"
    return "".join(parts)


def _parse_plan(text: str):
    """从 Leader 回复中提取 JSON 任务计划"""
    if "```json" in text:
        s = text.find("```json") + 7
        e = text.find("```", s)
        if e != -1:
            try:
                return json.loads(text[s:e].strip())
            except json.JSONDecodeError:
                pass
    if text.strip().startswith("{"):
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
    return None


def plan_tasks(requirements, mode="quality"):
    """Leader 分析需求并输出任务计划，支持 str 或 dict 输入"""
    dashboard.phase_start("leader", "正在分析需求并规划任务...")
    if isinstance(requirements, str):
        req_str = requirements
    else:
        req_str = json.dumps(requirements, ensure_ascii=False, indent=2)
    prompt = (
        "请先总结优化以下用户需求，然后拆分为尽可能细小的可执行子任务。\n"
        "每个任务只做一件事，涉及 UI/页面的任务 role 设为 Designer，"
        "涉及逻辑/后端的任务 role 设为 Coder。\n\n"
        f"用户需求：\n{req_str}"
    )
    reply = _call_role("leader", constants.LEADER_SYSTEM, prompt, mode)
    plan = _parse_plan(reply)
    if not plan or "tasks" not in plan:
        dashboard.phase_error("leader", "规划失败，回退单任务")
        plan = _fallback_plan(requirements)
    dashboard.phase_done("leader", f"共 {len(plan.get('tasks',[]))} 个任务")
    return plan


def _fallback_plan(req):
    """回退计划，支持 str 或 dict"""
    if isinstance(req, str):
        return {
            "project_name": "项目",
            "summary": req,
            "tasks": [{
                "id": 1, "title": "执行任务",
                "description": req,
                "role": "Coder", "priority": "high",
                "depends_on": []
            }]
        }
    return {
        "project_name": req.get("project_name", "项目"),
        "summary": req.get("summary", ""),
        "tasks": [{
            "id": 1, "title": req.get("summary", "执行任务"),
            "description": req.get("details", ""),
            "role": "Coder", "priority": "high",
            "depends_on": []
        }]
    }


def plan_bugfixes(test_report: dict, mode="quality"):
    """Leader 根据测试报告拆分 Bug 修复任务"""
    dashboard.phase_start("leader", "正在分析测试报告...")
    issues = test_report.get("issues", [])
    if not issues:
        return {"tasks": []}
    report_str = json.dumps(issues, ensure_ascii=False, indent=2)
    prompt = f"""测试发现以下问题，请拆分为修复任务：
{report_str}
每个任务只修复一个问题，输出 JSON 格式。"""
    reply = _call_role("leader", constants.LEADER_SYSTEM, prompt, mode)
    plan = _parse_plan(reply)
    if not plan or "tasks" not in plan:
        return {"tasks": []}
    dashboard.phase_done("leader", f"拆分为 {len(plan['tasks'])} 个修复任务")
    return plan


def summarize_project(all_outputs: dict, mode="quality"):
    """Leader 总结项目并生成文档"""
    dashboard.phase_start("leader", "正在总结项目...")
    summary_parts = []
    for tid, out in all_outputs.items():
        summary_parts.append(f"任务#{tid}: {out.get('title','')}\n{out.get('output','')[:1500]}")
    context = "\n\n".join(summary_parts)
    prompt = f"请总结以下项目成果，生成项目文档：\n{context}"
    reply = _call_role("leader", constants.LEADER_SYSTEM, prompt, mode)
    dashboard.phase_done("leader", "项目总结完成")
    return reply
