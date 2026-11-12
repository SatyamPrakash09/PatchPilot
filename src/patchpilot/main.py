"""PatchPilot CLI main module - Fixed agent loop handling."""

import argparse
import asyncio
import traceback
from typing import Any

from patchpilot.config.setting import get_config


def extract_text(content: Any) -> str:
    """Pull plain text out of str or content-block-list message content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") in (None, "text", "output_text"):
                parts.append(block.get("text", "") or "")
        return "".join(parts)
    if isinstance(content, dict):
        return extract_text(content.get("content", ""))
    return str(content) if content is not None else ""


class AgentLoopController:
    """Controls agent execution to prevent infinite loops."""

    def __init__(self, max_tool_calls: int = 30, max_turns: int = 20):
        self.max_tool_calls = max_tool_calls
        self.max_turns = max_turns
        self.tool_call_counts: dict[str, int] = {}
        self.total_tool_calls = 0
        self.latest_turns = 0

    def should_stop(self) -> bool:
        """Check if execution should stop."""
        return self.total_tool_calls >= self.max_tool_calls or self.latest_turns >= self.max_turns

    def record_tool_call(self, tool_name: str) -> bool:
        """Record a tool call and return True if it should be allowed."""
        self.tool_call_counts[tool_name] = self.tool_call_counts.get(tool_name, 0) + 1
        self.total_tool_calls += 1
        # Allow up to 2 calls per tool (handles the "already indexed" case)
        return self.tool_call_counts[tool_name] <= 2


def create_tool_executor():
    """Create a tool executor that calls tools directly."""
    from patchpilot.agent_config.agent_tools import tools

    tool_map = {t.name: t for t in tools}

    def execute_tool(name: str, args: dict) -> Any:
        if name not in tool_map:
            return f"Error: Tool '{name}' not found"
        tool = tool_map[name]
        return tool.invoke(args)

    return execute_tool, tool_map


async def run_agent_turn(query: str, chat_history: list, debug: bool = False) -> str:
    """Execute one agent turn with explicit loop detection and tool deduplication.

    This function implements a direct tool-calling loop that gives us full control
    over the interaction, preventing the infinite loops observed with deepagents'
    default behavior.
    """
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    # Initialize controller and tool executor
    controller = AgentLoopController(max_tool_calls=30, max_turns=15)
    execute_tool, tool_map = create_tool_executor()

    # Add user message to history
    chat_history.append(HumanMessage(content=query))

    final_response = ""
    buffer = ""

    try:
        # Import model function
        from patchpilot.agent_config.agent import agent
        from patchpilot.llm.model import llm_model

        turn_count = 0

        while not controller.should_stop() and turn_count < controller.max_turns:
            turn_count += 1
            controller.latest_turns = turn_count

            # Call the model
            try:
                result = agent.invoke(
                    {"messages": chat_history},
                    config={"recursion_limit": 200},
                )
                messages = result.get("messages", []) if isinstance(result, dict) else []
            except Exception as e:
                print(f"\n⚠️ Model error (attempt {turn_count}): {e}", flush=True)
                break

            # Find the last AI message
            ai_msg = None
            last_tool_calls = []
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    if getattr(msg, 'tool_calls', None):
                        ai_msg = msg
                        last_tool_calls = msg.tool_calls
                        break
                    else:
                        # This is the final AI response
                        content = extract_text(msg.content)
                        if content:
                            print(f"\n\033[1;34m🤖 [PatchPilot]\033[0m\n{content}\n", flush=True)
                            buffer = content
                        break

            if ai_msg is None and not buffer:
                # No AI message found
                break

            # Execute tool calls if any
            if last_tool_calls:
                print(f"\033[2m🔧 Executing {len(last_tool_calls)} tool call(s)...\033[0m", flush=True)

                for tc in last_tool_calls:
                    tool_name = tc.get("name")
                    args = tc.get("args", {})
                    tool_call_id = tc.get("id", "unknown")

                    # Check if we should allow this tool call (loop prevention)
                    if not controller.record_tool_call(tool_name):
                        print(f"   ⚠️ Skipped {tool_name} - loop detected (called {controller.tool_call_counts.get(tool_name, 0)} times)", flush=True)
                        continue

                    # Execute the tool
                    try:
                        result = execute_tool(tool_name, args)
                        result_str = str(result) if not isinstance(result, str) else result

                        # Print result preview
                        preview = result_str.replace("\n", " ")[:150]
                        print(f"   ↳ {tool_name}: {preview}...", flush=True)

                        # Add to history
                        chat_history.append(ToolMessage(
                            content=result_str,
                            tool_call_id=tool_call_id,
                            name=tool_name,
                        ))

                        # Check for stop signals
                        if "STOP" in result_str.upper() or "ALREADY" in result_str.upper():
                            print(f"   ℹ️ Tool suggests stopping - result indicates task complete", flush=True)

                    except Exception as e:
                        error_result = f"Error executing {tool_name}: {e}"
                        print(f"   ❌ {error_result}", flush=True)
                        chat_history.append(ToolMessage(
                            content=error_result,
                            tool_call_id=tool_call_id,
                            name=tool_name,
                        ))
            else:
                # No more tool calls, we have a response
                break

        # Warn if we hit limits
        if controller.total_tool_calls >= controller.max_tool_calls:
            print(f"\n⚠️ Hit tool call limit ({controller.max_tool_calls}).", flush=True)

        # Add final AI message to history
        if buffer:
            chat_history.append(AIMessage(content=buffer))

        return buffer

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}", flush=True)
        if debug:
            traceback.print_exc()
        if chat_history:
            chat_history.pop()
        return ""


async def chat_loop(debug: bool = False) -> None:
    """Interactive REPL on a single event loop (keeps async clients valid)."""
    print("\033[1;32m==========================================\033[0m")
    print("\033[1;32m      🛰️  PatchPilot Terminal Agent        \033[0m")
    print("\033[1;32m==========================================\033[0m")
    print("Commands: 'exit' or 'quit' to quit, 'clear' to reset chat history.\n")

    history: list = []
    while True:
        try:
            user_input = (
                await asyncio.to_thread(input, "\033[1;33mPatchPilot > \033[0m")
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting PatchPilot.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        if user_input.lower() == "clear":
            history.clear()
            print("Conversation history reset.\n")
            continue

        await run_agent_turn(user_input, history, debug=debug)


def start_interactive_session(debug: bool = False) -> None:
    try:
        asyncio.run(chat_loop(debug))
    except KeyboardInterrupt:
        print("\nExiting PatchPilot.")


def serve(port: int | None) -> None:
    from uvicorn import run

    config = get_config()
    port = port or config.PORT
    print(f"Starting PatchPilot FastAPI server on port {port}...", flush=True)
    run("patchpilot.app.app:app", reload=config.DEVELOPMENT, port=port)


def ui() -> None:
    from patchpilot.agent_config.agent_test_ui import launch_ui

    launch_ui()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PatchPilot - AI codebase investigation and debugging agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  patchpilot "Find error in ./src"   # Run a single query
  patchpilot chat                    # Interactive terminal session
  patchpilot serve                   # Start FastAPI web server
  patchpilot ui                      # Launch Gradio test UI
  patchpilot --debug "query"         # Print raw stream chunks
        """,
    )
    parser.add_argument("query", nargs="*", help="Query, or 'chat' / 'serve' / 'ui'.")
    parser.add_argument("--serve", action="store_true", help="Run the FastAPI web server.")
    parser.add_argument("--ui", action="store_true", help="Launch the Gradio test UI.")
    parser.add_argument("--port", type=int, default=None, help="Server port.")
    parser.add_argument("--debug", action="store_true", help="Print raw stream output and tracebacks.")

    args = parser.parse_args()

    if args.serve:
        return serve(args.port)
    if args.ui:
        return ui()

    query_str = " ".join(args.query).strip()
    command = query_str.lower()

    if not query_str or command == "chat":
        start_interactive_session(args.debug)
    elif command == "serve":
        serve(args.port)
    elif command == "ui":
        ui()
    else:
        asyncio.run(run_agent_turn(query_str, [], debug=args.debug))


if __name__ == "__main__":
    main()