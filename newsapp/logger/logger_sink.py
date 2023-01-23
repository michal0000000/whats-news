from enum import Enum


class LoggerSink(Enum):
    # you can create your own sinks, but keep the attribute name equal to its value (both uppercase)
    DEFAULT = "DEFAULT"
    VIEWS = "VIEWS"
    DEBUG = "DEBUG"
    SCRAPER = "SCRAPER"
    AUTH = "AUTH"
    NEWS = "NEWS"
    SOURCES = "SOURCES"
