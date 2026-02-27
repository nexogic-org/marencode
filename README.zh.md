<div align="center">

<img src="logo.svg" width="150" alt="Maren Code Logo" />

# ᓚᘏᗢ Maren Code

**Maren Automatically Runs Executable Navigation Code**

*一条指令，多智能体并行协作，零人工干预。*

<br>

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-Nexogic-blue.svg)](https://nexogic.org)
[![Version](https://img.shields.io/badge/Version-v2026.2.0.0-brightgreen.svg)](https://nexogic.org/version)
[![Python](https://img.shields.io/badge/Python-3.12+-yellow.svg)](https://www.python.org/downloads/release/python-3120/)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717?logo=github)](https://github.com/nexogic-org/marencode)

</div>

---

## 什么是 Maren Code？

Maren Code 是一款极致轻量化的全自动 AI 编程 CLI Agent。你只需输入一条指令，多个专业 AI 角色（Leader、Coder、Tester）**并行协作**，自动完成规划、编码、测试的全流程。

无 GUI，无手动操作，纯命令行效率。

```bash

  ███╗   ███╗ █████╗ ██████╗ ███████╗███╗   ██╗   ██████╗ ██████╗ ██████╗ ███████╗
  ████╗ ████║██╔══██╗██╔══██╗██╔════╝████╗  ██║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝
  ██╔████╔██║███████║██████╔╝█████╗  ██╔██╗ ██║  ██║     ██║   ██║██║  ██║█████╗
  ██║╚██╔╝██║██╔══██║██╔══██╗██╔══╝  ██║╚██╗██║  ██║     ██║   ██║██║  ██║██╔══╝
  ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗██║ ╚████║  ╚██████╗╚██████╔╝██████╔╝███████╗
  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
  ──────────────────────────────────────────────────────────────────────────────────

             ᓚᘏᗢ Maren Automatically Runs Executable Navigation Code

  Version  2026.2.0.0    Author  Nexogic AI Team    Status  ✓ Ready    License  MIT
  ──────────────────────────────────────────────────────────────────────────────────

>> run enter

  ══════════════════════════════════════════════════════════
  ᓚᘏᗢ Maren Code · Project Dialog
  Project: maren    Session: 738c1c72
  ══════════════════════════════════════════════════════════
  /new  New session  |  /list  List  |  /switch <id>  Switch  |  exit  Quit

```

## 核心模式

### 交互式项目模式 (`run enter`)
**推荐模式**。进入持续对话环境，支持上下文记忆、多轮指令和斜杠命令管理。

```bash
run enter
```

进入后会询问项目名称，支持 `/new` 新建会话、`/list` 列出会话、`/switch <id>` 切换会话，输入 `exit` 退出。

### 其他模式
虽然系统支持单次指令模式，但为了更好的上下文理解和项目管理，强烈建议使用 `run enter` 进入交互模式。

## 快速开始

### 安装

```bash
pip install -r requirements.txt
python app.py
```

### 初始化

```bash
code init boot
```

初始化向导会引导你配置 API Base URL、各角色模型名和 API Key。

### 常用命令

| 命令 | 说明 |
|---|---|
| `run enter` | **交互模式**：进入项目对话环境（核心） |
| `chat <消息>` | 单次对话 (Chatter) |
| `chat enter` | 进入纯聊天模式 |
| `config show` | 查看当前配置 |
| `config mode` | 切换模式 (`quality` / `saving`) |
| `skill list` | 查看已加载技能 |
| `help` | 查看所有命令 |
| `exit` | 退出 |

## 交互模式 (`run enter`)

进入交互模式后，你可以使用以下指令：

- `/new`：创建新项目会话
- `/list`：列出所有会话
- `/switch <id>`：切换到指定会话
- `exit`：退出交互模式

## AI 角色

| 角色 | 温度 | 职责 |
|---|---|---|
| **Leader** | 0.3 | 全局规划、任务拆解、依赖分析 |
| **Coder** | 0.0 | 代码编写、重构、Bug 修复 |
| **Tester** | 0.1 | 代码审查、测试用例生成、质量把关 |
| **Chatter** | 0.7 | 需求分析、聊天助手、信息检索 |
| **Icon Designer** | 1.0 | 图标/UI 元素生成 |

## 内置技能

AI 角色可动态调用的技能模块（位于 `core/skill/`）：

| 技能 | 说明 |
|---|---|
| `read_file` | 读取本地文件内容 |
| `write_file` | 写入文件（自动创建目录） |
| `edit_file` | 智能文件编辑 |
| `file_ops` | 文件操作（移动、删除、创建目录等） |
| `terminal` | 执行终端命令 |
| `get_github` | 获取 GitHub 仓库信息 |
| `get_web_info` | 网页搜索与提取 |
| `get_website` | 获取网页内容 |
| `get_time` | 获取系统时间 |

## 配置管理

通过 `config` 命令可以灵活调整系统行为：

```bash
code config mode quality      # 设置为质量优先模式（更多循环）
code config loops 5           # 设置最大修复循环次数
code config model set coder gpt-4-turbo  # 为 Coder 指定特定模型
code config danger list       # 查看危险命令黑名单
```

## 致谢

- **团队:** [Nexogic](https://nexogic.org)
- **API 提供:** [性价比Api](https://xingjiabiapi.org/register?aff=EpB0)

## 支持

如果你喜欢这个项目，可以通过 [爱发电](https://afdian.com/a/nexogic) 支持我们。

## 许可证

[MIT](https://opensource.org/licenses/MIT)
