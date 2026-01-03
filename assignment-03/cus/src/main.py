from utils.logger import setup_logging, get_logger
from api.http import create_app
from core.mock_controller import MockController
#from core.system_controller import SystemController

# Setup logging
setup_logging(log_level="INFO", log_file="logs/cus.log")
logger = get_logger(__name__)

# Create app instance for uvicorn to find
logger.info("Initializing CUS application")
controller = MockController()
# controller = SystemController()
app = create_app(controller)


def main():
    try:
        import uvicorn
    except Exception as exc:
        raise RuntimeError("uvicorn is required to run the server directly") from exc

    logger.info("Starting CUS server on localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()