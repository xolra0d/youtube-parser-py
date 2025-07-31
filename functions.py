import logging

def create_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - {name} - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(),]
    )
    return logger
