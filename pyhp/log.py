import logging
from logging import handlers
import os


class Server_Log:

    def __init__(self, level=logging.DEBUG, 
            logPath="./logs", 
            when="d", 
            interval=1,
            backupCount=7
        ):

        logger = logging.getLogger()
        logger.setLevel(level)

        if not os.path.isdir(logPath):
            os.makedirs(logPath)

        sh = logging.StreamHandler()
        rh = handlers.TimedRotatingFileHandler(
            os.path.join(logPath, "pyhp.log"), 
            when,
            interval,
            backupCount
        )
        
        logger.addHandler(sh)
        logger.addHandler(rh)

        formatter = logging.Formatter(
            self.setFormat()
        )
        sh.setFormatter(formatter)
        rh.setFormatter(formatter)
        
    def setFormat(self):
        return "\033[0m[%(asctime)s][%(levelname)s] %(message)s\033[0m"