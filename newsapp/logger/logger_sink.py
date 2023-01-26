from enum import Enum


class LoggerSink(Enum):
    # you can create your own sinks, but keep the attribute name equal to its value (both uppercase)
    DEFAULT = "DEFAULT"
    VIEWS = "VIEWS"
    DEBUG = "DEBUG"
    SCRAPER = "SCRAPER"
    AUTH = "AUTH"
    NEWS = "NEWS"
    SLOVAK_NEWS_SOURCES = "SLOVAK_NEWS_SOURCES"
    CYBERSEC_SOURCES = "CYBERSEC_SOURCES"
