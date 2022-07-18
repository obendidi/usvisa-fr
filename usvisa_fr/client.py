import logging
import typing as tp

from bs4 import BeautifulSoup
from httpx import Client

from usvisa_fr.config import settings

logger = logging.getLogger(__name__)

T = tp.TypeVar("T", bound="UsVisaClient")


class UsVisaClient(Client):
    def __init__(self, **kwargs) -> None:
        kwargs.update(
            {"headers": {"User-Agent": "Mozilla/5.0"}, "base_url": settings.BASE_URI}
        )
        super().__init__(**kwargs)
        self.sign_in()

    def get_crsf(self, content: bytes) -> tp.Tuple[str, str]:
        soup = BeautifulSoup(content, "lxml")
        csrf_param = soup.find("meta", attrs={"name": "csrf-param"})
        csrf_token = soup.find("meta", attrs={"name": "csrf-token"})
        assert csrf_token is not None, "CSRF token not found"
        csrf_param = csrf_param or {"content": "authenticity_token"}
        param, token = csrf_param.get("content"), csrf_token.get("content")
        assert param and token, "Invalid CSRF param and/or token"
        return param, token

    def sign_in(self) -> None:
        logger.info(f"Signing in to: {self.base_url}")
        resp = self.get("/users/sign_in")
        resp.raise_for_status()
        csrf_param, csrf_token = self.get_crsf(resp.content)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            csrf_param: csrf_token,
            "user[email]": settings.USVISA_USERNAME,
            "user[password]": settings.USVISA_PASSWORD,
            "policy_confirmed": 1,
        }
        resp = self.post("/users/sign_in", headers=headers, data=data)
        if resp.status_code != 302:
            raise RuntimeError(f"Authentification Error: {resp}")
        logger.info("\t => Sign in successful.")

    def __enter__(self: T) -> T:
        self._transport.__enter__()
        for transport in self._mounts.values():
            if transport is not None:
                transport.__enter__()
        return self


if __name__ == "__main__":
    with UsVisaClient() as client:
        client.sign_in()
