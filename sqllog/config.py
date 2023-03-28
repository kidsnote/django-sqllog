import configparser


class Config(configparser.ConfigParser):
    def __init__(self):
        super().__init__(allow_no_value=True)

    def get_value(self, conv, section, option, *, default=None):
        value = default
        try:
            if conv is bool:
                conv = self._convert_to_boolean
            value = self._get_conv(section, option, conv)
        finally:
            return value
