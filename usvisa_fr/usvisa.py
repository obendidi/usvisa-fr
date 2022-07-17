import logging
import time
import typing as tp
from datetime import datetime

from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
    wait_fixed,
)

from usvisa_fr.config import settings

DAYS = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]

logger = logging.getLogger(__name__)


retry_policy = retry(
    retry=retry_if_exception_type(WebDriverException),
    reraise=True,
    stop=(stop_after_delay(900) | stop_after_attempt(500)),
    wait=wait_fixed(10) + wait_random_exponential(multiplier=1, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


@retry_policy
def sign_in(browser: Firefox) -> None:
    browser.get(f"{settings.BASE_URI}/users/sign_in ")
    browser.find_element(By.ID, "user_email").send_keys(settings.USVISA_USERNAME)
    browser.find_element(By.ID, "user_password").send_keys(settings.USVISA_PASSWORD)
    browser.find_element(
        By.XPATH,
        "/html/body/div[5]/main/div[3]/div/div[1]/div/form/div[3]/label/div",
    ).click()
    time.sleep(0.5)
    browser.find_element(
        By.XPATH,
        "/html/body/div[5]/main/div[3]/div/div[1]/div/form/p[1]/input",
    ).click()


@retry_policy
def get_current_appointement_date(browser: Firefox) -> datetime:
    browser.get(f"{settings.BASE_URI}/groups/18399708")
    element = browser.find_element(
        By.XPATH,
        "/html/body/div[4]/main/div[2]/div[3]/div[1]/div/div/div[2]/p[1]",
    )
    parsed = element.text.lstrip("Consular Appointment: ").rstrip(
        " PARIS local time at Paris — get directions"
    )
    return datetime.strptime(parsed, "%d %B, %Y, %H:%M")


@retry_policy
def find_new_appointement(
    browser: Firefox, *, current_appointement: datetime
) -> tp.Optional[datetime]:
    browser.get(f"{settings.BASE_URI}/schedule/37982683/appointment")

    if _check_consulate_date_not_available(browser):
        logger.error("There are no available appointments at the selected location.")
        logger.error("Sleeping for 10 minutes.")
        time.sleep(600)
        return None

    # click on date input field to show calendar
    browser.find_element(By.ID, "appointments_consulate_appointment_date_input").click()
    logger.info("Parsing calendar ...")
    while True:
        # get moth and year
        mm_yyy = browser.find_element(
            By.XPATH, "/html/body/div[5]/div[1]/div/div"
        ).text.strip()
        mm_yyy_date = datetime.strptime(mm_yyy, "%B %Y")
        if mm_yyy_date > current_appointement:
            break

        logger.info(f"Looking in '{mm_yyy}' calendar ...")
        _day = _process_calendar(browser)
        if _day is not None:
            _time = _select_time(browser)
            new_appointement = datetime.strptime(
                f"{_day} {mm_yyy} {_time}", "%d %B %Y %H:%M"
            )
            if new_appointement < current_appointement:
                logger.info(f"\t => Found new appointement at '{new_appointement}'")
                # Submit
                browser.find_element(By.ID, "appointments_submit_action").click()
                # Confirm
                browser.find_element(By.XPATH, "/html/body/div[6]/div/div/a[2]").click()
                logger.info(f"\t => New appointement at '{new_appointement}' booked.")
                return new_appointement
            else:
                logger.warning(
                    f"\t => Found appointement at '{new_appointement}' "
                    f"but it is >= '{current_appointement}', ignoring."
                )
            break

        logger.warning(f"\t => No appointements found in '{mm_yyy}'.")

        # check next month and repeat
        browser.find_element(By.XPATH, "/html/body/div[5]/div[2]/div/a").click()
    return None


def _process_calendar(browser: Firefox) -> tp.Optional[int]:
    calendar = browser.find_elements(
        By.XPATH, "/html/body/div[5]/div[1]/table/tbody/tr/td"
    )
    for date in calendar:
        value = date.text.strip()
        if value == "":
            continue

        if date.get_attribute("class").strip() == "undefined":
            date.click()
            return int(value)
    return None


def _select_time(browser: Firefox) -> str:

    # click on date input field to show calendar
    browser.find_element(By.ID, "appointments_consulate_appointment_time_input").click()
    dropdown = browser.find_elements(
        By.XPATH,
        "/html/body/div[4]/main/div[4]/div/div/form/fieldset/ol/fieldset/div/div[1]/div[3]/li[2]/select/option",  # noqa
    )
    for item in dropdown:
        value = item.text.strip()
        if value == "":
            continue
        item.click()
        break

    return value


def _check_consulate_date_not_available(browser: Firefox) -> bool:
    try:
        element = browser.find_element(By.ID, "consulate_date_time_not_available")
        style = element.get_attribute("style")
        if style.strip() == "display: none;":
            return False
        return True
    except NoSuchElementException:
        return False
