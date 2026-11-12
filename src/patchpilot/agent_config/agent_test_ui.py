import gradio as gr

from patchpilot.agent_config.agent import agent
from patchpilot.main import get_token_logger


def agent_invoke(query: str) -> str:
    # Reset token logger for fresh session
    logger = get_token_logger()
    logger.reset_usage()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        },
        config={
            "callbacks": [logger],
        }
    )

    # Get final token counts
    usage = logger.get_total_usage()

    # Append token usage to response
    response = result["messages"][-1].content
    token_info = f"\n\n---\n🪙 Token counts: {usage.input_tokens:,} input | {usage.output_tokens:,} output | {usage.total_tokens:,} total"
    return response + token_info


demo = gr.Interface(
    fn=agent_invoke,
    inputs=gr.Textbox(
        label="Query",
        placeholder="Ask PatchPilot something...",
    ),
    outputs=gr.Textbox(
        label="Response",
    ),
    title="PatchPilot",
    description="AI-powered coding assistant",
)

def launch_ui(server_port: int = 7860, share: bool = False) -> None:
    demo.launch(server_port=server_port, share=share)


if __name__ == "__main__":
    launch_ui()