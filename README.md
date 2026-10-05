# 🛰️ PatchPilot

**PatchPilot** is an agentic AI coding assistant designed to explore local codebases, investigate bugs, search code and AST symbols, inspect Git repositories, and reason about fixes directly from your terminal or web interface.

Built using **LangGraph**, **LangChain**, **Ollama**, and **Tree-sitter**, PatchPilot runs locally or cloud-connected via Ollama with zero cloud vendor lock-in.

---

## 📋 Table of Contents
- [Architecture & Workflow](#-architecture--workflow)
- [Project Structure](#-project-structure)
- [Features & Tooling](#-features--tooling)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Configuration](#-configuration)
- [Execution & Usage](#-execution--usage)
  - [1. Interactive Terminal Agent (REPL)](#1-interactive-terminal-agent-repl)
  - [2. Direct Query Execution](#2-direct-query-execution)
  - [3. Web API Server (FastAPI)](#3-web-api-server-fastapi)
  - [4. Web UI (Gradio)](#4-web-ui-gradio)
- [Tool Reference](#-tool-reference)

---

## 🏗️ Architecture & Workflow

PatchPilot implements a progressive investigation workflow. When presented with a task or bug report, the agent navigates the codebase step-by-step:

```
                            User Query
                                │
                                ▼
                       ┌─────────────────┐
                       │ PatchPilot LLM  │
                       │ (ReAct Agent)   │
                       └────────┬────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  📁 Filesystem           🔎 Code Search         🌳 Tree-sitter AST
  ├── list_dir            └── search_code        ├── build_codebase
  ├── list_file               (ripgrep)          ├── search_codebase
  └── search_file_type                           └── read_symbol
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                        📖 read_file_chunk
                                │
                                ▼
                        🔀 Git Inspection
                        ├── git_status
                        ├── git_diff
                        ├── git_branch
                        └── git_logs
                                │
                                ▼
                       Comprehensive Answer
                       & Actionable Diagnosis
```

---

## 📂 Project Structure

```
PatchPilot/
├── src/
│   └── patchpilot/
│       ├── __init__.py           # Package definition & version metadata
│       ├── __main__.py           # python -m patchpilot entrypoint
│       ├── main.py               # CLI runner, REPL chat, server & UI launchers
│       │
│       ├── agent_config/
│       │   ├── agent.py          # LangGraph ReAct agent compiler
│       │   ├── agent_tools.py    # Registered tool registry
│       │   ├── agent_test_ui.py  # Gradio web interface
│       │   └── system_prompt.toon # Agent persona & tool instructions (TOON format)
│       │
│       ├── codebase/             # Tree-sitter AST indexing
│       │   ├── index.py          # CodebaseIndex AST symbol extractor
│       │   ├── parser.py         # Tree-sitter Python parser
│       │   └── symbols.py        # Symbol dataclass (functions, classes)
│       │
│       ├── config/
│       │   └── setting.py        # Pydantic BaseSettings & cached config
│       │
│       ├── llm/
│       │   └── model.py          # Chat model initialization via LangChain
│       │
│       ├── tools/                # Agent tools
│       │   ├── filesystem.py     # list_dir, list_file, search_file_type, read_file_chunk
│       │   ├── search.py         # search_code (ripgrep)
│       │   ├── git.py            # git_status, git_diff, git_branch, git_logs, git_remote_branch
│       │   └── codebase_tool.py  # build_codebase, search_codebase, read_symbol
│       │
│       └── app/
│           └── app.py            # FastAPI service definition
│
├── pyproject.toml                # Project metadata, CLI script, and dependencies
├── .env                          # Local environment configuration
└── README.md                     # Documentation
```

---

## ✨ Features & Tooling

1. **Progressive Exploration**: Locates directories and files before jumping into large file reads.
2. **Deep Semantic Symbol Search**: Uses Tree-sitter to parse Python code into an Abstract Syntax Tree (AST), enabling precise class/function symbol discovery and source extraction.
3. **Fast Native Code Search**: High-performance regex and text searching via `ripgrep` (`rg`).
4. **Context-Aware Git Inspection**: Upward-traversing Git repository detection to inspect branches, uncommitted diffs, logs, and remotes from any subdirectory.
5. **Multiple Interfaces**:
   - **Terminal REPL**: Conversational interactive shell with colored tool traces and memory.
   - **Terminal Single-Shot**: Quick one-command answers directly to stdout.
   - **FastAPI**: REST server for programmatic integration.
   - **Gradio**: Interactive web browser UI.

---

## 📦 Prerequisites

- **Python**: `>= 3.13`
- **uv**: Recommended Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Ripgrep (`rg`)**: Required for code search (`sudo apt install ripgrep` or `brew install ripgrep`)
- **Ollama**: Local or cloud LLM runner (`curl -fsSL https://ollama.com/install.sh | sh`)

---

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SatyamPrakash09/PatchPilot.git
   cd PatchPilot
   ```

2. **Install dependencies**:
   Using `uv` (recommended):
   ```bash
   uv sync
   ```
   Or standard pip:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. **Install globally (Run from anywhere via `uv tool`)**:
   Install `patchpilot` as a persistent, globally accessible terminal command in editable mode:
   ```bash
   uv tool install --editable .
   ```
   - Places the `patchpilot` binary directly in `~/.local/bin/patchpilot`.
   - The `--editable` flag ensures any code changes in the repository immediately apply without reinstalling.

4. **Pull or configure an LLM model in Ollama**:
   ```bash
   ollama pull gemma4:31b-cloud
   # or a smaller local model:
   ollama pull gemma4:12b
   ```

---

## ⚙️ Configuration

Create or update `.env` in the project root:

```env
DEVELOPMENT=True
PORT=3000
MODEL=gemma4:31b-cloud
PROVIDER=ollama
IS_STREAM=False
```

| Key | Description | Default |
| :--- | :--- | :--- |
| `MODEL` | Ollama model tag or remote model | `gemma4:31b-cloud` |
| `PROVIDER` | Model provider for LangChain | `ollama` |
| `PORT` | Web server port | `3000` |
| `DEVELOPMENT` | Enable auto-reload on FastAPI | `False` |

---

## 💻 Execution & Usage

### 1. Interactive Terminal Agent (REPL)

Start an interactive session where you can converse with PatchPilot across multiple turns:

```bash
# Direct command (from any directory):
patchpilot
# or
patchpilot chat

# (Or inside the repo without global install):
uv run patchpilot
```

Inside the interactive session:
```text
==========================================
      🛰️  PatchPilot Terminal Agent        
==========================================
Commands: 'exit' or 'quit' to quit, 'clear' to reset chat history.

PatchPilot > Where is get_config defined and what does it do?

⚙️  Executing query: Where is get_config defined and what does it do?

🔧 [Tool Call] search_code(path='.', query='def get_config')
   ↳ [Result] {"status": "success", "message": "Found 1 match records"...}
🔧 [Tool Call] read_file(file_path='src/patchpilot/config/setting.py')
   ↳ [Result] {"file_path": ".../src/patchpilot/config/setting.py", ...}

🤖 [PatchPilot]
`get_config` is defined in `src/patchpilot/config/setting.py`. It returns a cached
singleton instance of `Settings` using `@lru_cache`...

PatchPilot > clear
Conversation history reset.

PatchPilot > exit
Goodbye!
```

---

### 2. Direct Query Execution

Execute a single prompt without entering the interactive shell:

```bash
# General codebase inspection
patchpilot "What files are in src/patchpilot?"

# Search symbols using Tree-sitter
patchpilot "Index this codebase and list classes in src/patchpilot/codebase/index.py"

# Inspect Git repository state
patchpilot "What are the latest commits and unstaged changes?"
```

---

### 3. Web API Server (FastAPI)

Launch the FastAPI backend server:

```bash
patchpilot serve
# or with a custom port:
patchpilot --serve --port 8000
```
API endpoints will be available at `http://localhost:3000`.

---

### 4. Web UI (Gradio)

Launch the interactive browser UI:

```bash
patchpilot ui
```
Open `http://localhost:7860` in your web browser.

---

## 🛠️ Tool Reference

PatchPilot comes equipped with 13 built-in tools:

### 📁 Filesystem
| Tool | Arguments | Description |
| :--- | :--- | :--- |
| `list_dir` | `dir_path="."` | Lists directory names inside a target folder. |
| `list_file` | `dir_path="."` | Lists regular files present directly inside a directory. |
| `search_file_type` | `dir_path="."`, `file_glob="*.py"` | Finds files matching a specific glob or extension pattern. |
| `read_file_chunk` | `filepath`, `start_line=1`, `end_line=500` | Reads a specific line range from a file (1-indexed, inclusive). |

### 🔎 Code Search
| Tool | Arguments | Description |
| :--- | :--- | :--- |
| `search_code` | `query`, `path="."` | Rapidly searches source files for strings/regex via `ripgrep` (`rg`). |

### 🌳 Tree-sitter AST Codebase Indexing
| Tool | Arguments | Description |
| :--- | :--- | :--- |
| `build_codebase` | `repo_path="."` | Parses and indexes Python function and class definitions using Tree-sitter. |
| `search_codebase` | `query`, `repo_path="."` | Locates symbol definitions across indexed project files. |
| `read_symbol` | `file_path`, `symbol_name`, `repo_path="."` | Extracts the exact source code slice for a specific function or class. |

### 🔀 Git Inspection (Read-Only)
| Tool | Arguments | Description |
| :--- | :--- | :--- |
| `git_status` | `workspace="."` | Displays working tree status and active branch. |
| `git_diff` | `workspace="."` | Returns current unstaged diff. |
| `git_branch` | `workspace="."` | Returns the current active branch name. |
| `git_logs` | `workspace="."` | Retrieves the latest 10 commits with decorations. |
| `git_remote_branch` | `workspace="."` | Lists configured remote repositories and URLs. |

---

## 📄 License

This project is licensed under the MIT License.
