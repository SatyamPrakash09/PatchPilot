from langchain.agents import create_agent
from patchpilot.agent_config.agent_tools import tools
from patchpilot.config.setting import get_config
from patchpilot.llm.model import llm_model
config = get_config()


system_prompt = ''

with open ("/home/onix/Code/PatchPilot/src/patchpilot/agent_config/system_prompt.md", "r", encoding="utf-8") as file:
    system_prompt = file.read()

agent = create_agent(
    system_prompt="",
    tools= tools,
    model = llm_model
    
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

