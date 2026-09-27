from langchain.chat_models import init_chat_model
from patchpilot.config.setting import get_config
config = get_config()

llm_model = init_chat_model(
    model=config.MODEL,
    model_provider=config.PROVIDER,
    temperature=0.2
)

# print(llm_model.invoke("what is ai?").content)

