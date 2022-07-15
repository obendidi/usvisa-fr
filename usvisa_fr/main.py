import logging
import time
from datetime import datetime

from selenium.webdriver import Firefox
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_fixed,
    wait_random,
)

from usvisa_fr.browser import get_browser
from usvisa_fr.config import settings
from usvisa_fr.logger import RichHandler
from usvisa_fr.usvisa import (
    find_new_appointement,
    get_current_appointement_date,
    sign_in,
)

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)


@retry(
    reraise=True,
    stop=stop_after_attempt(20),
    wait=wait_fixed(20) + wait_random(10, 20),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def main(browser: Firefox):
    logger.info(f"Signing in to: {settings.BASE_URI}")
    sign_in(browser)
    logger.info("\t => Successfully signed in.")

    logger.info("Getting current appointment date ...")
    current_appointement = get_current_appointement_date(browser)
    logger.info(
        f"\t => Current appointement is at '{current_appointement}' "
        f"(in {current_appointement - datetime.now()})"
    )
    while True:
        new_appointement = find_new_appointement(
            browser, current_appointement=current_appointement
        )
        if new_appointement is not None:
            current_appointement = new_appointement
            with open("APPOINTEMENTS_CHANGELOG.md", "a") as f:
                f.write(
                    f"## [{datetime.now()}] New appointement booked "
                    f"at {current_appointement}\n"
                )
            # TODO: Send notification telegram ?

        logger.info("Sleeping for 30 seconds ...")
        time.sleep(30)


if __name__ == "__main__":
    try:
        browser = get_browser(headless=not settings.DEBUG)
        main(browser)
    finally:
        logger.info("Closing browser.")
        browser.close()
