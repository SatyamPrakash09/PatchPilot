import json
from typing import Any, AsyncGenerator, Generator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from patchpilot.agent_config.agent import agent
from patchpilot.config.setting import get_config
from patchpilot.tools.codebase_tool import get_runtime

router = APIRouter(prefix="/agent", tags=["Agent"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class AgentRunRequest(BaseModel):
    query: str = Field(..., description="Task or question for PatchPilot agent")
    chat_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation turns",
    )
    repo_path: str | None = Field(
        default=None,
        description="Optional repository path to target",
    )


@router.get("/info")
def get_agent_info():
    """Get metadata about the current PatchPilot agent and LLM configuration."""
    config = get_config()
    return {
        "status": "running",
        "model": config.MODEL,
        "provider": config.PROVIDER,
        "development_mode": config.DEVELOPMENT,
    }


@router.post("/run")
def run_agent_endpoint(body: AgentRunRequest):
    """Execute an agent turn synchronously and return all executed tool steps and final answer."""
    if body.repo_path:
        get_runtime(body.repo_path)

    # Convert chat history to dict format for LangGraph agent
    history = [{"role": msg.role, "content": msg.content} for msg in body.chat_history]
    history.append({"role": "user", "content": body.query})

    steps: list[dict[str, Any]] = []
    final_response = ""

    try:
        for chunk in agent.stream({"messages": history}):
            for node_name, node_output in chunk.items():
                messages = node_output.get("messages", [])
                step_record: dict[str, Any] = {"node": node_name, "tool_calls": [], "tool_results": []}

                for msg in messages:
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            step_record["tool_calls"].append({
                                "name": tc.get("name"),
                                "args": tc.get("args", {}),
                                "id": tc.get("id"),
                            })
                    elif msg.__class__.__name__ == "ToolMessage":
                        step_record["tool_results"].append({
                            "content": str(msg.content),
                            "name": getattr(msg, "name", None),
                        })
                    elif (
                        hasattr(msg, "content")
                        and msg.content
                        and (node_name == "agent" or not getattr(msg, "tool_calls", None))
                    ):
                        final_response = str(msg.content)

                if step_record["tool_calls"] or step_record["tool_results"]:
                    steps.append(step_record)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    if final_response:
        history.append({"role": "assistant", "content": final_response})

    return {
        "status": "success",
        "query": body.query,
        "response": final_response,
        "steps": steps,
        "chat_history": history,
    }


@router.post("/stream")
def stream_agent_endpoint(body: AgentRunRequest):
    """Stream agent execution via Server-Sent Events (SSE).
    
    Streams live events for tool calls, tool results, agent thought chunks, and final response.
    """
    if body.repo_path:
        get_runtime(body.repo_path)

    history = [{"role": msg.role, "content": msg.content} for msg in body.chat_history]
    history.append({"role": "user", "content": body.query})

    def event_stream() -> Generator[str, None, None]:
        final_response = ""
        try:
            yield f"event: start\ndata: {json.dumps({'query': body.query})}\n\n"

            for chunk in agent.stream({"messages": history}):
                for node_name, node_output in chunk.items():
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                payload = {
                                    "name": tc.get("name"),
                                    "args": tc.get("args", {}),
                                    "id": tc.get("id"),
                                }
                                yield f"event: tool_call\ndata: {json.dumps(payload)}\n\n"
                        elif msg.__class__.__name__ == "ToolMessage":
                            content = str(msg.content)
                            preview = (content[:250] + "...") if len(content) > 250 else content
                            payload = {
                                "name": getattr(msg, "name", None),
                                "content": content,
                                "preview": preview,
                            }
                            yield f"event: tool_result\ndata: {json.dumps(payload)}\n\n"
                        elif (
                            hasattr(msg, "content")
                            and msg.content
                            and (node_name == "agent" or not getattr(msg, "tool_calls", None))
                        ):
                            final_response = str(msg.content)
                            yield f"event: chunk\ndata: {json.dumps({'content': final_response})}\n\n"

            if final_response:
                history.append({"role": "assistant", "content": final_response})

            yield f"event: done\ndata: {json.dumps({'response': final_response, 'chat_history': history})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
