"""
shell/cmd/run.py — code run enter 命令
交互式项目对话模式：Chatter 交流需求 → Leader 拆分任务 → Coder 逐个执行
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
from shell.cmd.config import get_mode, get_max_loops
from core.context_tracker import ContextTracker
from core.runtime_dir import get_runtime_dir
from pipeline.chatter import gather_requirements
from pipeline.leader import plan_tasks, plan_bugfixes
from pipeline.coder import execute_task, execute_designer_task
from pipeline.tester import review_code
from pipeline import dashboard
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
    return os.path.basename(get_runtime_dir()) or "未命名项目"


# ── 会话类 ──
class RunSession:
    """run enter 的单个会话"""

    def __init__(self, project_name: str, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.project_name = project_name
        self.history = []
        self.created = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.tracker = ContextTracker(max_tokens=128000)


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
    """处理 run enter 模式中的斜杠命令"""
    global _sessions, _active_session_id
    parts = text.strip().split()
    cmd = parts[0].lower()

    if cmd == "/new":
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


def _dispatch_task(task: dict, context: str, mode: str):
    """根据任务角色分发给对应执行者"""
    role = task.get("role", "Coder").lower()
    if role == "designer":
        return execute_designer_task(task, context, mode)
    else:
        return execute_task(task, context, mode)


def _run_pipeline(user_input: str):
    """
    完整多角色协作流程：
    1. Chatter 交流需求细节
    2. Leader 拆分子任务
    3. Coder/Designer 逐个执行
    4. Leader 整合 → Tester 测试
    5. Leader 审查报告 → 不过关则拆修复任务 → Coder 修复
    6. 循环直至 Tester 无 bug（质量模式最多5次，节约模式最多3次）
    """
    mode = get_mode()
    max_loops = get_max_loops()

    dashboard.banner("Maren Code 全自动编程引擎")
    print(f"  {dashboard.CAT} 模式: {Fore.CYAN}{mode}{Style.RESET_ALL}"
          f" | 最大循环: {Fore.CYAN}{max_loops}{Style.RESET_ALL}")
    print()

    # ══════════════════════════════════════════════
    # Phase 1: Chatter 收集需求
    # ══════════════════════════════════════════════
    try:
        requirements = gather_requirements(user_input)
    except KeyboardInterrupt:
        print(f"\n{prefix()}{Fore.YELLOW}已中断{Style.RESET_ALL}")
        return
    if not requirements:
        print(f"{prefix()}{Fore.RED}需求收集失败{Style.RESET_ALL}")
        return

    # ══════════════════════════════════════════════
    # Phase 2: Leader 拆分任务
    # ══════════════════════════════════════════════
    try:
        plan = plan_tasks(requirements, mode)
    except KeyboardInterrupt:
        print(f"\n{prefix()}{Fore.YELLOW}已中断{Style.RESET_ALL}")
        return
    except Exception as e:
        print(f"{prefix()}{Fore.RED}Leader 规划失败: {e}{Style.RESET_ALL}")
        return

    tasks = plan.get("tasks", [])
    if not tasks:
        print(f"{prefix()}{Fore.RED}Leader 未生成任何任务{Style.RESET_ALL}")
        return

    # 展示任务面板
    dashboard.task_list([
        {"id": t["id"], "title": t["title"],
         "role": t.get("role", "Coder"), "status": "pending"}
        for t in tasks
    ])

    # ══════════════════════════════════════════════
    # Phase 3: Coder/Designer 逐个执行子任务
    # ══════════════════════════════════════════════
    context = plan.get("summary", "")
    all_outputs = {}

    for idx, t in enumerate(tasks):
        role = t.get("role", "Coder")
        if role.lower() == "tester":
            continue

        dashboard.phase_start("leader",
            f"分配任务 #{t['id']} 给 {role} ({idx+1}/{len(tasks)})")

        try:
            output = _dispatch_task(t, context, mode)
            all_outputs[t["id"]] = {
                "title": t["title"],
                "output": output,
                "role": role
            }
            context += f"\n[#{t['id']} {t['title']} 已完成]"
        except KeyboardInterrupt:
            print(f"\n{prefix()}{Fore.YELLOW}已中断{Style.RESET_ALL}")
            return

    if not all_outputs:
        print(f"{prefix()}{Fore.RED}没有任务产出{Style.RESET_ALL}")
        return

    # ══════════════════════════════════════════════
    # Phase 4: Tester 测试 → Leader 审查 → Coder 修复 → 循环
    # ══════════════════════════════════════════════
    for loop_i in range(1, max_loops + 1):
        dashboard.loop_info(loop_i, max_loops, mode)

        # Tester 审查代码
        report = review_code(all_outputs, mode)

        errors = [i for i in report.get("issues", [])
                  if i.get("severity") == "error"]
        if not errors:
            dashboard.phase_done("tester", "所有测试通过 ✓")
            break

        dashboard.phase_done("tester",
            f"发现 {len(errors)} 个错误，报告已提交给 Leader")

        # Leader 分析测试报告，拆分修复任务
        dashboard.phase_start("leader", "正在分析测试报告并拆分修复任务...")
        fix_plan = plan_bugfixes(report, mode)
        fix_tasks = fix_plan.get("tasks", [])

        if not fix_tasks:
            dashboard.phase_done("leader", "无法生成修复任务，结束循环")
            break

        dashboard.task_list([
            {"id": ft["id"], "title": ft["title"],
             "role": ft.get("role", "Coder"), "status": "pending"}
            for ft in fix_tasks
        ])

        # Coder 逐个修复
        for ft in fix_tasks:
            role = ft.get("role", "Coder")
            dashboard.phase_start("leader",
                f"分配修复任务 #{ft['id']} 给 {role}")
            try:
                fix_out = _dispatch_task(ft, context, mode)
                all_outputs[ft["id"]] = {
                    "title": ft["title"],
                    "output": fix_out,
                    "role": role
                }
            except KeyboardInterrupt:
                print(f"\n{prefix()}{Fore.YELLOW}已中断{Style.RESET_ALL}")
                return

        # 循环回到 Tester 再次测试

    # ══════════════════════════════════════════════
    # Phase 5: 完成
    # ══════════════════════════════════════════════
    dashboard.banner("项目完成", Fore.LIGHTGREEN_EX)
    print(f"  {prefix()}{Fore.GREEN}全部完成。{Style.RESET_ALL}\n")


def enter():
    """进入 run enter 交互式项目对话模式"""
    global _sessions, _active_session_id
    init(autoreset=True)
    _ensure_utf8()

    if not inited.is_inited():
        print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} "
              f"未初始化，请先执行 code init boot")
        return

    # 首次进入：从 .maren/project.json 读取项目名称
    if not _sessions:
        project_name = _load_project_name()
        session = RunSession(project_name)
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

        ACCENT = '\033[38;5;222m'
        R = Style.RESET_ALL
        prompt = (
            f"{Style.BRIGHT}{ACCENT}"
            f"[{session.project_name}]{R} "
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

        # ── 核心流程：Chatter → Leader → Coder ──
        _run_pipeline(text)
        _flush_input()


def run(message: str):
    """执行 run 命令 — 必须使用 run enter"""
    init(autoreset=True)

    if message and message.strip().lower() == "enter":
        enter()
        return

    print(f"{prefix()}{Fore.YELLOW}run 命令必须搭配 enter 使用。{Style.RESET_ALL}")
    print(f"{prefix()}请使用 {Fore.GREEN}run enter{Style.RESET_ALL} 进入项目对话模式。")
    print(f"{prefix()}如需全自动编程，请使用 {Fore.GREEN}new <需求描述>{Style.RESET_ALL}。")
