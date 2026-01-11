import sys
from colorama import init

from configuration import ScraperConfig
from scraper import CourtScraper
from logger import ColorLogger

init(autoreset=True)


def main():
    try:
        config = ScraperConfig.from_env()
        
        if not config.capsolver_api_key:
            ColorLogger.error("CAPSOLVER_API_KEY not set in .env file")
            sys.exit(1)
        
        ColorLogger.info(f"CapSolver API Key: {config.capsolver_api_key[:10]}...{config.capsolver_api_key[-5:]}")
        
        scraper = CourtScraper(config)
        scraper.run("case_ids.csv")
        
    except Exception as e:
        ColorLogger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
