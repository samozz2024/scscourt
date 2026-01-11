from colorama import Fore, Style


class ColorLogger:
    @staticmethod
    def success(msg: str):
        print(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def error(msg: str):
        print(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(msg: str):
        print(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def info(msg: str):
        print(f"{Fore.CYAN}ℹ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def processing(msg: str):
        print(f"{Fore.BLUE}⚙ {msg}{Style.RESET_ALL}")
    
    @staticmethod
    def skip(msg: str):
        print(f"{Fore.MAGENTA}⊘ {msg}{Style.RESET_ALL}")
