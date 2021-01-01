import logging

class Log:

    @staticmethod
    def get_logger():
        logging.basicConfig(level=logging.DEBUG)
        return logging