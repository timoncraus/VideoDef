import logging

class ColoredFormatter(logging.Formatter):
    """Кастомный форматтер с цветами для консоли"""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m', 
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[41m',
        'RESET': '\033[0m',
    }
    
    def format(self, record):
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)