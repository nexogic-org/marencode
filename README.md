<div align="center">

<img src="logo.svg" width="150" alt="Maren Code Logo" />

# ᓚᘏᗢ Maren Code

**Maren Automatically Runs Executable Navigation Code**

*One instruction. Multiple AI agents. Zero manual work.*

<br>

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-Nexogic-blue.svg)](https://nexogic.org)
[![Version](https://img.shields.io/badge/Version-v2026.2.0.0-brightgreen.svg)](https://nexogic.org/version)
[![Python](https://img.shields.io/badge/Python-3.12+-yellow.svg)](https://www.python.org/downloads/release/python-3120/)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-181717?logo=github)](https://github.com/nexogic-org/marencode)

</div>

---

## What is Maren Code?

Maren Code is a lightweight, fully automated AI programming CLI agent. You give a single instruction — multiple specialized AI roles (Leader, Coder, Tester) collaborate **in parallel** to plan, code, and test a complete solution.

No GUI. No manual steps. Pure CLI efficiency.

```bash
>> code run "Build a REST API with user authentication"

  ═══════════════════════════════════════════════════════
  ᓚᘏᗢ Maren Code Multi-Agent Engine
  ═══════════════════════════════════════════════════════

  ✓ [👑 Leader]  Planning complete — 4 tasks
  ⟳ [⌨ Coder]   #1 Project scaffold        ██████████░░ 75%
  ⟳ [⌨ Coder]   #2 Auth module
  ⟳ [🔍 Tester]  #3 Unit tests
```

## Core Modes

### 1. Fast Parallel Mode (`code run`)
After the Leader plans the tasks, it builds a dependency graph and executes independent tasks **in parallel**, significantly speeding up generation. Ideal for clear requirements and efficiency.

```
User Input → 👑 Leader Plan → ⚡ Parallel Exec (Layer 1/2/3) → 📁 Output
                              ├─ ⌨ Coder (Task A)
                              ├─ ⌨ Coder (Task B)
                              └─ ⌨ Coder (Task C)
```

### 2. Full Quality Mode (`new`)
Introduces **Chatter** for requirement analysis and **Tester** for code review, including an **automatic fix loop**. Ideal for complex projects or when code quality is a priority.

```
Chatter (Reqs) → Leader (Plan) → Coder (Exec) → Tester (Review) ──┐
                                   ↑                          │
                                   └───────(Auto Fix)─────────┘
```

### 3. Interactive Project Mode (`run enter`)
Enter a continuous conversation environment with context memory, supporting multi-turn instructions and slash commands.

## Quick Start

### Install

```bash
pip install -r requirements.txt
python app.py
```

### Initialize

```bash
code init boot
```

The setup wizard will guide you through configuring the API Base URL, model names, and API Keys for each role.

### Common Commands

| Command | Description |
|---|---|
| `code run <desc>` | **Parallel Mode**: Fast code generation |
| `new <desc>` | **Quality Mode**: With analysis & fix loops |
| `run enter` | **Interactive Mode**: Project dialog environment |
| `chat <msg>` | Single-shot chat (Chatter) |
| `chat enter` | Enter pure chat mode |
| `config show` | View current config |
| `config mode` | Switch mode (`quality` / `saving`) |
| `skill list` | List loaded skills |
| `help` | Show all commands |
| `exit` | Exit CLI |

## Interactive Mode (`run enter`)

Once in interactive mode, you can use:

- `/new`: Create a new project session
- `/list`: List all sessions
- `/switch <id>`: Switch to a specific session
- `exit`: Exit interactive mode

## AI Roles

| Role | Temp | Purpose |
|---|---|---|
| **Leader** | 0.3 | Global planning, task breakdown, dependency analysis |
| **Coder** | 0.0 | Coding, refactoring, bug fixing |
| **Tester** | 0.1 | Code review, test case generation, QA |
| **Chatter** | 0.7 | Requirement analysis, chat assistant, retrieval |
| **Icon Designer** | 1.0 | Icon/UI element generation |

## Built-in Skills

AI roles can dynamically invoke skills (located in `core/skill/`):

| Skill | Description |
|---|---|
| `read_file` | Read local file content |
| `write_file` | Write file (auto-creates directories) |
| `edit_file` | Intelligent file editing |
| `file_ops` | File operations (move, delete, mkdir, etc.) |
| `terminal` | Execute terminal commands |
| `get_github` | Fetch GitHub repository info |
| `get_web_info` | Web search and extraction |
| `get_website` | Fetch webpage content |
| `get_time` | Get system time |

## Configuration

Customize system behavior with `config`:

```bash
code config mode quality      # Set to Quality Mode (more loops)
code config loops 5           # Set max fix loops
code config model set coder gpt-4-turbo  # Override model for Coder
code config danger list       # View dangerous command blacklist
```

## Thanks

- **Team:** [Nexogic](https://nexogic.org)
- **API Provider:** [性价比Api](https://xingjiabiapi.org/register?aff=EpB0)

## Support

If you like this project, support us on [Afdian](https://afdian.com/a/nexogic).

## License

[MIT](https://opensource.org/licenses/MIT)
