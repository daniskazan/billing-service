import os

from config.db import DBConfig
from config.jwt import JWTConfig


class ServerConfig:
    def __init__(
        self,
        *,
        db_config: DBConfig,
        jwt_config: JWTConfig
    ):
        self.db_config = db_config
        self.jwt_config = jwt_config
        self.app_host: str = os.environ.get("APP_HOST", "0.0.0.0")
        self.app_port: int = os.environ.get("APP_PORT", 8000)
        self.workers: int = os.environ.get("WORKERS", 1)
        self.debug: bool = os.environ.get("DEBUG", True)
