from pydantic import BaseSettings


class Settings(BaseSettings):

    DEBUG: bool = False

    # Credentials
    USVISA_USERNAME: str
    USVISA_PASSWORD: str

    # USVISA URLs
    BASE_URI: str = "https://ais.usvisa-info.com/en-fr/niv"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
