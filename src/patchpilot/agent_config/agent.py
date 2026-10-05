from pathlib import Path
from langchain.agents import create_agent
from patchpilot.agent_config.agent_tools import tools
from patchpilot.config.setting import get_config
from patchpilot.llm.model import llm_model

config = get_config()

PROMPT_FILE = Path(__file__).parent / "system_prompt.toon"
system_prompt = PROMPT_FILE.read_text(encoding="utf-8") if PROMPT_FILE.exists() else ""

agent = create_agent(
    system_prompt=system_prompt,
    tools=tools,
    model=llm_model,
)

#Code below is just for tetsing the agent

# result = agent.invoke({
#     "messages": [
#         {
#             "role": "user",
#             "content": "find error in /home/onix/Code/Orbit"
#         }
#     ]
# })

# print(result["messages"][-1].content)

