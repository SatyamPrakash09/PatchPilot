import argparse
import sys
from patchpilot.config.setting import get_config


def run_agent_turn(query: str, chat_history: list) -> str:
    """Executes a single agent turn with live streaming of tool calls and results."""
    from patchpilot.agent_config.agent import agent

    chat_history.append({"role": "user", "content": query})
    final_response = ""

    print(f"\n\033[1;36m⚙️  Executing query:\033[0m {query}\n")

    try:
        for chunk in agent.stream({"messages": chat_history}):
            for node_name, node_output in chunk.items():
                messages = node_output.get("messages", [])
                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            args_repr = ", ".join(f"{k}={v!r}" for k, v in tc.get("args", {}).items())
                            print(f"\033[33m🔧 [Tool Call]\033[0m \033[1m{tc['name']}\033[0m({args_repr})")
                    elif msg.__class__.__name__ == "ToolMessage":
                        content = str(msg.content)
                        preview = (content[:250] + "...") if len(content) > 250 else content
                        print(f"   \033[32m↳ [Result]\033[0m {preview}")
                    elif hasattr(msg, "content") and msg.content and node_name == "agent" or (hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None)):
                        final_response = msg.content
    except Exception as e:
        print(f"\n\033[31m❌ [Error executing agent]:\033[0m {e}\n")
        return str(e)

    if final_response:
        chat_history.append({"role": "assistant", "content": final_response})
        print(f"\n\033[1;34m🤖 [PatchPilot]\033[0m\n{final_response}\n")
    return final_response


def start_interactive_session() -> None:
    """Runs an interactive conversational REPL session with PatchPilot in the terminal."""
    print("\033[1;32m==========================================\033[0m")
    print("\033[1;32m      🛰️  PatchPilot Terminal Agent        \033[0m")
    print("\033[1;32m==========================================\033[0m")
    print("Commands: 'exit' or 'quit' to quit, 'clear' to reset chat history.\n")

    history = []
    while True:
        try:
            user_input = input("\033[1;33mPatchPilot > \033[0m").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            if user_input.lower() == "clear":
                history.clear()
                print("Conversation history reset.\n")
                continue

            run_agent_turn(user_input, history)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting PatchPilot.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PatchPilot - AI codebase investigation and debugging agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  patchpilot "Find error in ./src"            # Run a single query directly
  patchpilot chat                             # Start interactive terminal session
  patchpilot serve                            # Start FastAPI web server
  patchpilot ui                               # Launch Gradio test UI
        """,
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Query to ask the agent. If omitted or 'chat', starts interactive terminal mode.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run the FastAPI web server.",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the Gradio test UI in browser.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for the FastAPI web server.",
    )

    args = parser.parse_args()

    if args.serve:
        from uvicorn import run
        config = get_config()
        port = args.port or config.PORT
        print(f"Starting PatchPilot FastAPI server on port {port}...")
        run("patchpilot.app.app:app", reload=config.DEVELOPMENT, port=port)
        return

    if args.ui:
        from patchpilot.agent_config.agent_test_ui import launch_ui
        launch_ui()
        return

    query_str = " ".join(args.query).strip() if args.query else ""

    if not query_str or query_str.lower() == "chat":
        start_interactive_session()
    elif query_str.lower() == "serve":
        from uvicorn import run
        config = get_config()
        port = args.port or config.PORT
        run("patchpilot.app.app:app", reload=config.DEVELOPMENT, port=port)
    elif query_str.lower() == "ui":
        from patchpilot.agent_config.agent_test_ui import launch_ui
        launch_ui()
    else:
        run_agent_turn(query_str, [])


if __name__ == "__main__":
    main()

