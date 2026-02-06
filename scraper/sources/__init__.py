"""News source scrapers"""
from .base import BaseScraper
from .nrl_official import NRLOfficialScraper
from .theroar import TheRoarScraper
from .thewest import TheWestScraper
from .perthnow import PerthNowScraper
from .foxsports import FoxSportsScraper
from .smh import SMHScraper
from .theage import TheAgeScraper
from .codesports import CodeSportsScraper
from .newsnow import NewsNowScraper
from .nine import NineScraper

__all__ = [
    "BaseScraper",
    "NRLOfficialScraper",
    "TheRoarScraper",
    "TheWestScraper",
    "PerthNowScraper",
    "FoxSportsScraper",
    "SMHScraper",
    "TheAgeScraper",
    "CodeSportsScraper",
    "NewsNowScraper",
    "NineScraper",
]
