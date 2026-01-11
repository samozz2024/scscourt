import sys
from colorama import init

from configuration import ScraperConfig
from orchestrator import ScraperOrchestrator
from utils.logger import ColorLogger

init(autoreset=True)


def main():
    try:
        config = ScraperConfig.from_env()
        
        if not config.capsolver_api_key:
            ColorLogger.error("CAPSOLVER_API_KEY not set in .env file")
            sys.exit(1)
        
        orchestrator = ScraperOrchestrator(config)
        orchestrator.run("case_ids.csv")
        
    except Exception as e:
        ColorLogger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
