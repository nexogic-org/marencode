"""
shell/cmd/new.py — new 命令
Leader 作为入口 → 优化提示词 → 拆分细小任务 → 逐个交给 Coder/Designer → Tester 测试 → Leader 总结修复 → 循环
"""
from colorama import Fore, Style, init
from shell.cmd import prefix
from shell.cmd.config import get_mode, get_max_loops
from pipeline import dashboard
from pipeline.leader import plan_tasks, plan_bugfixes, summarize_project
from pipeline.coder import execute_task, execute_designer_task
from pipeline.tester import review_code


def _dispatch_task(task: dict, context: str, mode: str):
    """根据任务角色分发给对应执行者"""
    role = task.get("role", "Coder").lower()
    if role == "designer":
        return execute_designer_task(task, context, mode)
    else:
        # Coder 是默认角色，Leader/Tester 类型的任务也由 Coder 执行
        return execute_task(task, context, mode)


def run(message: str):
    """执行 new 命令 - Leader 主导的全流程自动化"""
    init(autoreset=True)
    if not message or not message.strip():
        print(f"{prefix()}{Fore.RED}请输入需求描述{Style.RESET_ALL}")
        return

    mode = get_mode()
    max_loops = get_max_loops()

    dashboard.banner("Maren Code 全自动编程引擎")
    print(f"  {dashboard.CAT} 模式: {Fore.CYAN}{mode}{Style.RESET_ALL}"
          f" | 最大循环: {Fore.CYAN}{max_loops}{Style.RESET_ALL}")
    print()

    # ══════════════════════════════════════════════
    # Phase 1: Leader 接收需求，优化提示词，拆分细小任务
    # ══════════════════════════════════════════════
    dashboard.phase_start("leader", "正在分析需求、优化提示词并拆分任务...")
    try:
        plan = plan_tasks(message.strip(), mode)
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
    # Phase 2: Leader 逐个将任务交给 Coder / Designer
    # ══════════════════════════════════════════════
    context = plan.get("summary", "")
    all_outputs = {}

    for idx, t in enumerate(tasks):
        role = t.get("role", "Coder")
        # Tester 类型任务跳过（系统自动调用 Tester）
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
            # 累积上下文供后续任务使用
            context += f"\n[#{t['id']} {t['title']} 已完成]"
        except KeyboardInterrupt:
            print(f"\n{prefix()}{Fore.YELLOW}已中断{Style.RESET_ALL}")
            return

    if not all_outputs:
        print(f"{prefix()}{Fore.RED}没有任务产出{Style.RESET_ALL}")
        return

    # ══════════════════════════════════════════════
    # Phase 3: Tester 测试 → Leader 总结 → 拆分修复 → Coder 修复 → 循环
    # ══════════════════════════════════════════════
    for loop_i in range(1, max_loops + 1):
        dashboard.loop_info(loop_i, max_loops, mode)

        # 3a: Tester 审查代码，写测试报告
        report = review_code(all_outputs, mode)

        errors = [i for i in report.get("issues", [])
                  if i.get("severity") == "error"]
        if not errors:
            dashboard.phase_done("tester", "所有测试通过 ✓")
            break

        dashboard.phase_done("tester",
            f"发现 {len(errors)} 个错误，报告已提交给 Leader")

        # 3b: Leader 接收测试报告，总结并拆分修复任务
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

        # 3c: Leader 逐个将修复任务交给 Coder
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
    # Phase 4: Leader 总结项目
    # ══════════════════════════════════════════════
    try:
        summary = summarize_project(all_outputs, mode)
    except Exception:
        summary = ""

    dashboard.banner("项目完成", Fore.LIGHTGREEN_EX)
    print(f"  {prefix()}{Fore.GREEN}全部完成。{Style.RESET_ALL}")
    if summary:
        print(f"\n{summary}")
