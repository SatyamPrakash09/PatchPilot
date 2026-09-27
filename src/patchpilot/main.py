from uvicorn import run
from patchpilot.config.setting import get_config


def main() -> None:
    config = get_config()
    run(
        "patchpilot.app.app:app",
        reload=config.DEVELOPMENT,
        port=config.PORT,
    )


if __name__ == "__main__":
    main()
