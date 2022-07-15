import logging

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

logger = logging.getLogger(__name__)


def get_browser(headless: bool = False) -> Firefox:
    manager = GeckoDriverManager()
    options = FirefoxOptions()
    options.headless = headless
    service = Service(executable_path=manager.install())
    return Firefox(service=service, options=options)
