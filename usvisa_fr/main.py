import logging
import typing as tp
from datetime import datetime
import time

from bs4 import BeautifulSoup

from usvisa_fr.client import UsVisaClient
from usvisa_fr.logger import RichHandler

from dateutil.parser import parse as parse_date

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%x %X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)


def get_current_appointement_date(client: UsVisaClient) -> datetime:
    logger.info("Getting current appointment date ...")
    resp = client.get("/groups/18399708")
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "lxml")
    param = soup.find("p", attrs={"class": "consular-appt"})
    if param is None:
        raise ValueError("Couldn't find current appointment date!")
    date_obj = parse_date(param.text.strip(), fuzzy=True, ignoretz=True)
    logger.info(
        f"\t => Current appointement is at '{date_obj}' "
        f"(in {(date_obj - datetime.now()).days} days.)"
    )
    return date_obj


def get_closest_availlable_apointement(client: UsVisaClient) -> tp.Optional[datetime]:
    logger.info("Getting closest available appointement ...")
    params = {"appointments[expedite]": "false"}
    resp = client.get("/schedule/37982683/appointment/days/44.json", params=params)
    resp.raise_for_status()
    dates = resp.json()
    if not dates:
        logger.warning(
            "\t => Got an empty date response, please wait "
            "for a while before retrying ..."
        )
        return None

    str_date = min(dates, key=lambda d: d["date"])["date"]

    # get time
    params = {"appointments[expedite]": "false", "date": str_date}
    resp = client.get("/schedule/37982683/appointment/times/44.json", params=params)
    resp.raise_for_status()
    times = resp.json().get("available_times", [])
    if not times:
        raise RuntimeError(f"Couldn't find any available time, for date '{str_date}'")

    str_time = min(times)
    closest_date = datetime.strptime(f"{str_date} {str_time}", "%Y-%m-%d %H:%M")
    logger.info(f"\t => Closest available appointement found is at '{closest_date}'")
    return closest_date


def book_new_appointment(client: UsVisaClient, new_appointement: datetime) -> bool:
    logger.info(f"Booking new appointement at '{new_appointement}' ...")
    # get crsf data
    csrf_param, csrf_token = client.get_crsf(
        client.get("/schedule/37982683/appointment").content
    )

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    _date, _time = new_appointement.strftime("%Y-%m-%d %H:%M").split()

    data = {
        csrf_param: csrf_token,
        "confirmed_limit_message": 1,
        "use_consulate_appointment_capacity": True,
        "appointments[consulate_appointment][facility_id]": 44,  # 44 stands for PARIS embassy # noqa
        "appointments[consulate_appointment][date]": _date,
        "appointments[consulate_appointment][time]": _time,
    }
    resp = client.post("/schedule/37982683/appointment", headers=headers, data=data)
    if resp.status_code != 302:
        logger.error(
            f"\t => Failed to book new appointment at '{new_appointement}' ({resp})"
        )
        return False

    # shouldn't happend cause status code is 302 redirect
    if resp.next_request is None:
        raise RuntimeError()

    expected_redirect = f"{client.base_url}schedule/37982683/appointment/instructions"
    if resp.next_request.url != expected_redirect:
        logger.error(
            f"Couldn't book new appointement at '{new_appointement}'."
            f"\nExpected redirect to '{expected_redirect}' "
            f"but got '{resp.next_request.url}'"
        )
        return False
    logger.info(f"\t => Successfully booked new appointment at '{new_appointement}'")
    return True


def main(client: UsVisaClient):
    while True:
        # get current appointement date
        current_appointement = get_current_appointement_date(client)

        # try to find a new appointement date
        new_appointement = get_closest_availlable_apointement(client)

        # In case we get throtheled, wait for a while
        if new_appointement is None:
            logger.warning("Sleeping for 15 minutes before retrying ...")
            time.sleep(15 * 60)  # sleep for 15mins
            continue

        # if new appointement is not better than current one
        if new_appointement >= current_appointement:
            logger.info(
                f"New appointement is in a longer date than current one "
                f"(new='{new_appointement}' >= current='{current_appointement}'), "
                "\nSleeping for 5 minutes before retrying ..."
            )
            time.sleep(5 * 60)  # sleep for 5mins
            continue

        booked = book_new_appointment(client, new_appointement)
        if booked:
            logger.info("Logging new appointement date ...")
            with open("APPOINTEMENTS_CHANGELOG.md", "a") as f:
                f.write(f"## [{datetime.now()}]: New appointement {new_appointement}\n")
            logger.info("Sleeping for 10 minutes before retrying ...")
            time.sleep(10 * 60)  # sleep for 10mins
            continue


if __name__ == "__main__":
    try:
        while True:
            try:
                client = UsVisaClient()
                main(client)
            except Exception as error:
                logger.error(f"Error: {error}")
                time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Exiting ...")
