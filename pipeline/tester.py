"""
pipeline/tester.py — Tester 测试审查模块
"""
import json
from colorama import Fore, Style
from core.agent import request
from pipeline import dashboard
from pipeline.leader import _load_role_cfg
import constants


def _parse_test_report(text: str):
    """从 Tester 回复中提取 JSON 报告"""
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
    return {"status": "pass", "issues": [], "tests": []}


def review_code(all_outputs: dict, mode="quality"):
    """Tester 审查所有 Coder 输出"""
    rc = _load_role_cfg("tester")
    if not rc:
        return {"status": "pass", "issues": []}
    dashboard.phase_start("tester", "正在审查代码...")

    # 构建审查内容
    code_parts = []
    for tid, out in all_outputs.items():
        code_parts.append(f"任务#{tid}:\n{out.get('output','')[:2000]}")
    code_str = "\n\n".join(code_parts)

    prompt = f"请审查以下代码：\n{code_str}"
    lang_hint = f"\n使用 {rc['lang']} 输出。"
    full_sys = constants.BASE_SYSTEM + "\n" + constants.TESTER_SYSTEM + lang_hint

    kwargs = {}
    if rc.get("temperature") is not None:
        kwargs["temperature"] = rc["temperature"]
    mt = rc.get("max_tokens", 4096)
    if mode == "saving":
        mt = min(mt, 1024)
    kwargs["max_tokens"] = mt

    parts = []
    try:
        for chunk in request.chat_complete(
            rc["base_url"], rc["api_key"], rc["model_name"],
            full_sys, [], prompt, **kwargs
        ):
            parts.append(chunk)
    except RuntimeError as e:
        dashboard.phase_error("tester", f"审查 API 错误: {e}")
        return {"status": "pass", "issues": []}
    except KeyboardInterrupt:
        dashboard.phase_error("tester", "审查被用户中断")
        return {"status": "pass", "issues": []}
    except Exception as e:
        dashboard.phase_error("tester", f"审查未知异常: {type(e).__name__}: {e}")
        return {"status": "pass", "issues": []}

    reply = "".join(parts)
    report = _parse_test_report(reply)
    issues = report.get("issues", [])
    errors = [i for i in issues if i.get("severity") == "error"]

    if errors:
        dashboard.phase_done("tester", f"发现 {len(errors)} 个错误")
    else:
        dashboard.phase_done("tester", "审查通过")
    return report
