import gradio as gr

from patchpilot.agent_config.agent import agent


def agent_invoke(query: str) -> str:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ]
        }
    )

    return result["messages"][-1].content


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

demo.launch(debug=True)