from loguru import logger
import sys
def setup():
   logger.remove()

   LOG_FORMAT = ("<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                 "<level>{level: <8}</level> | "
                 "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

   logger.add(sys.stdout, level="INFO", format=LOG_FORMAT, filter=lambda r: r["level"].no < 40, colorize=True)
   logger.add(sys.stderr, level="ERROR", format=LOG_FORMAT, colorize=True)