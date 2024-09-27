import enum
import abc
import typing
import uvicorn
from starlette.types import ExceptionHandler
from fastapi import status
from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from config.server import ServerConfig
from config.db import DBConfig
from config.jwt import JWTConfig
from api import routing


class HandlersProvidable(abc.ABC):
    def get_handlers(self):
        raise NotImplementedError("Child classes should implement this method.")

    def notify(self, sender: FastAPI):
        raise NotImplementedError("Child classes should implement this method.")


class ExceptionCodeEnum(enum.StrEnum):
    BAD_REQUEST: str = "BAD_REQUEST"
    INTERNAL_SERVER_ERROR: str = "INTERNAL_SERVER_ERROR"
    UNPROCCESSABLE_ENTITY: str = "UNPROCESSABLE_ENTITY"


class ExceptionsHandler(HandlersProvidable):
    @staticmethod
    def handler_422(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": ExceptionCodeEnum.UNPROCCESSABLE_ENTITY
            }
        )

    @staticmethod
    def handler_500(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": ExceptionCodeEnum.INTERNAL_SERVER_ERROR
            }
        )

    def get_handlers(self) -> list[tuple[ExceptionHandler, type[Exception]]]:
        return [
            (self.handler_500, Exception),
            (self.handler_422, RequestValidationError)
        ]

    def notify(self, sender: FastAPI) -> None:
        for handler, exc in self.get_handlers():
            sender.add_exception_handler(exc, handler=handler)


class StartupEventsHandler(HandlersProvidable):

    def connect_db_on_startup(self):
        pass

    def connect_redis_on_startup(self):
        pass

    def get_handlers(self) -> list[tuple[typing.Literal["startup", "shutdown"], typing.Callable]]:
        return [
            ("startup", self.connect_db_on_startup),
            ("startup", self.connect_redis_on_startup)
        ]

    def notify(self, sender: FastAPI):
        for event_type, event_func in self.get_handlers():
            sender.add_event_handler(event_type=event_type, func=event_func)


class RoutingHandler(HandlersProvidable):
    def get_handlers(self) -> list[APIRouter]:
        return [
            routing.v1
        ]

    def notify(self, sender: FastAPI):
        for api_router in self.get_handlers():
            sender.include_router(router=api_router)


class Server:
    app: typing.ClassVar[FastAPI] = FastAPI(
            title="Billing Service API",
    )
    observers: typing.ClassVar[list[HandlersProvidable]] = [
        RoutingHandler(),
        StartupEventsHandler(),
        ExceptionsHandler(),
    ]

    def __init__(self, server_config: ServerConfig):
        self.config = server_config

    @classmethod
    def _notify(cls) -> None:
        for observer in cls.observers:
            observer.notify(sender=cls.app)

    def __call__(self) -> FastAPI:
        return self.app

    def __new__(cls, *args, **kwargs):
        cls._notify()
        return super().__new__(cls)

    def run(self) -> None:
        uvicorn.run(
            app="main:server",
            factory=True,
            host=self.config.app_host,
            port=self.config.app_port,
            reload=self.config.debug,
            workers=self.config.workers,
        )


server_config = ServerConfig(
    db_config=DBConfig(),
    jwt_config=JWTConfig()
)
server = Server(server_config)


if __name__ == '__main__':
    server.run()
