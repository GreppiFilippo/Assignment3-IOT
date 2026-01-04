from utils.logger import setup_logging, get_logger
import asyncio
from core.system_controller import SystemController
import config


# Setup logging
setup_logging(log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)
logger = get_logger(__name__)

async def main():
    logger.info("Initializing CUS application")
    
    controller = SystemController()
    
    try:
        await controller.run()
    except asyncio.CancelledError:
        logger.info("Application cancelled, shutting down...")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        # Ensure clean shutdown of all services
        await controller.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutdown requested")
