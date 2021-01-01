import logging

class Log:

    @staticmethod
    def get_logger(self):
        logging.basicConfig(level=loggin.DEBUG)
        return logging