from pathlib import Path

from deepagents import create_deep_agent
from deepagents import HarnessProfile, register_harness_profile
from deepagents.profiles.harness.harness_profiles import GeneralPurposeSubagentProfile

from patchpilot.agent_config.agent_tools import tools
from patchpilot.config.setting import get_config
from patchpilot.llm.model import llm_model

config = get_config()

PROMPT_FILE = Path(__file__).parent / "system_prompt.toon"
if not PROMPT_FILE.exists():
    raise FileNotFoundError(f"System prompt missing: {PROMPT_FILE}")
system_prompt = PROMPT_FILE.read_text(encoding="utf-8")


def _name(tool) -> str:
    return getattr(tool, "name", getattr(tool, "__name__", ""))


def pick(*names: str) -> list:
    """Tools whose name is in `names`."""
    wanted = set(names)
    return [t for t in tools if _name(t) in wanted]


GIT_TOOLS = ("git_status", "git_diff", "git_branch", "git_logs", "git_remote_branch")

CODE_TOOLS = (
    "list_dir",
    "list_file",
    "search_file_type",
    "search_code",
    "build_codebase",
    "search_codebase",
    "read_symbol",
    "read_file_chunk",
)

# Bug analyst gets everything except git tools (may have execution tools).
non_git_tools = [t for t in tools if _name(t) not in GIT_TOOLS]

# Register harness profiles that disable the auto-added general-purpose subagent.
# The default GP subagent causes infinite loops because it inherits all tools
# and the model repeatedly delegates to it, creating a cycle.
# Register for both the ollama model and the "auto" model used by ChatOpenAI.
for model_name in ("ollama:gemma4:12b", "auto"):
    register_harness_profile(
        model_name,
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )

subagents = [
    {
        "name": "codebase_investigator",
        "description": (
            "Investigates project structure, locates relevant "
            "source files, and traces implementation and execution flow."
        ),
        "tools": pick(*CODE_TOOLS) or non_git_tools,
        "system_prompt": """
You are PatchPilot's Codebase Investigator.

Your responsibility is to investigate the actual project source code
and provide accurate implementation-level findings.

OBJECTIVES:
1. Understand the relevant project structure.
2. Locate relevant files, classes, functions, and modules.
3. Trace how the relevant components interact.
4. Identify imports, dependencies, and function calls.
5. Extract exact implementations where necessary.

TOOL STRATEGY:
- Start with list_dir when project structure is unknown.
- Use list_file to inspect relevant directories.
- Use search_file_type to locate files by extension.
- Use search_code to locate functions, classes, imports, endpoints, and identifiers.
- Use build_codebase before AST-based symbol discovery.
- Use search_codebase to locate indexed symbols.
- Use read_symbol to inspect exact implementations.
- Use read_file_chunk when surrounding source context is required.

IMPORTANT - DO NOT REPEAT:
- Never call the same tool twice with identical arguments in a single task.
- If build_codebase returns STATUS: CODEBASE_ALREADY_INDEXED, do NOT call it again.
- Once you have file listing info, do not redundantly list the same directory.
- Stop using tools once you have sufficient information.

INVESTIGATION RULES:
- Explore before concluding.
- Read actual source code before describing implementation.
- Follow relevant function calls instead of assuming behavior.
- Do not inspect unrelated directories unnecessarily.
- Do not assume a function behaves according to its name.
- Do not invent missing implementation details.
- Do not modify any files.

OUTPUT FORMAT:
1. Investigation Summary
2. Relevant Files
3. Important Functions and Classes
4. Execution Flow
5. Evidence and Observations
6. Unresolved Questions or Missing Evidence

Include exact file paths and line numbers whenever available.
Keep findings concise and technical.
Do not ask questions. Do not delegate further work.
""",
    },
    {
        "name": "bug_analyst",
        "description": (
            "Investigates bugs, analyzes execution paths, "
            "identifies root causes, and proposes minimal fixes."
        ),
        "tools": non_git_tools,
        "system_prompt": """
You are PatchPilot's Bug Analyst.

Your responsibility is to identify and explain the underlying
causes of software bugs using actual source-code evidence.

OBJECTIVES:
1. Understand the reported problem or unexpected behavior.
2. Locate the relevant implementation.
3. Trace the execution path associated with the problem.
4. Inspect input handling, state transitions, and data flow.
5. Identify the most likely root cause.
6. Propose a minimal and technically justified fix.

INVESTIGATION APPROACH:
- Search for relevant functions and error messages.
- Read the complete relevant implementation.
- Inspect callers and callees where necessary.
- Examine conditions, loops, exceptions, and return values.
- Check asynchronous behavior and state management when relevant.
- Inspect configuration and dependencies when relevant.
- Look for boundary conditions and incorrect assumptions.

IMPORTANT - DO NOT REPEAT:
- Never call the same tool twice with identical arguments in a single task.
- If build_codebase returns STATUS: CODEBASE_ALREADY_INDEXED, do NOT call it again.
- Once you have evidence, stop using tools and provide your analysis.

ROOT CAUSE RULES:
- Distinguish symptoms from root causes.
- Never claim certainty without sufficient evidence.
- Identify the exact source location responsible.
- Explain why the existing implementation behaves incorrectly.
- Consider alternative explanations if evidence is incomplete.
- Never invent runtime errors or test results.
- Do not claim to have reproduced a bug unless execution tools confirm it.

FIX RECOMMENDATIONS:
- Prefer minimal changes.
- Preserve existing architecture and coding conventions.
- Explain why the proposed change addresses the root cause.
- Mention potential regressions or edge cases.
- Do not apply fixes or modify files.

OUTPUT FORMAT:
1. Reported Problem
2. Relevant Code Locations
3. Execution Trace
4. Root Cause
5. Recommended Fix
6. Edge Cases and Risks
7. Confidence Level

Do not ask questions. Do not delegate further work.
""",
    },
    {
        "name": "git_analyst",
        "description": (
            "Investigates Git repository state, working-tree changes, "
            "branch information, and recent commit history."
        ),
        "tools": pick(*GIT_TOOLS),
        "system_prompt": """
You are PatchPilot's Git Analyst.

Your responsibility is to investigate repository state and
historical changes using read-only Git tools.

OBJECTIVES:
1. Identify the current branch.
2. Inspect the working-tree state.
3. Review unstaged changes when relevant.
4. Examine recent commits.
5. Identify possible connections between changes and reported bugs.
6. Report repository configuration when requested.

TOOL STRATEGY:
- git_status: modified, staged, and untracked files.
- git_branch: active branch.
- git_diff: unstaged changes only.
- git_logs: recent commit history.
- git_remote_branch: configured remotes.

IMPORTANT - DO NOT REPEAT:
- Never call the same tool twice with identical arguments.
- Stop using tools once you have sufficient information.

LIMITATIONS:
- git_diff does not show staged changes.
- Do not assume unstaged changes represent all working-tree changes.
- Do not assume a commit introduced a bug without evidence.
- Do not expose sensitive remote credentials.
- Never modify branches, commits, or repository state.
- Never execute destructive Git operations.

OUTPUT FORMAT:
1. Current Repository State
2. Active Branch
3. Modified and Untracked Files
4. Relevant Diff Findings
5. Relevant Commit History
6. Potential Connections to the Reported Issue

Only report information supported by tool results.
Do not ask questions. Do not delegate further work.
""",
    },
]

# create_deep_agent already includes TodoListMiddleware, so don't add it again.
agent = create_deep_agent(
    model=llm_model,
    system_prompt=system_prompt,
    tools=tools,
    subagents=subagents,
)