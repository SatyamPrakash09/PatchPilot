from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from patchpilot.config.setting import get_config
config = get_config()

# llm_model = init_chat_model(
#     model=config.MODEL,
#     model_provider=config.PROVIDER,
#     temperature=0.0
# )

llm_model = ChatOpenAI(
    model="auto",
    base_url="http://127.0.0.1:31415/v1",
    api_key=config.FREELLMAPI_API_KEY,
    temperature=0.2,
    max_tokens=2048,
)

# print(llm_model.invoke("what is ai?").content)
