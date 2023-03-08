from sql_metadata import Parser


# HACK: Override the Parser class to suppress logging message from logger that exist inside the Parser class.
class QueryParser(Parser):
    def __init__(self, sql: str = '', enable_default_logger: bool = False) -> None:
        super().__init__(sql)
        self._logger.disabled = not enable_default_logger
