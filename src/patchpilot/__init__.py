from uvicorn import run
from config.setting import get_config
config = get_config()
def main() -> None:
    run(
        "main:app",
        reload=config.DEVELOPMENT,
        port=config.PORT,
    )
