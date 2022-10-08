from typing import Any, Dict
from starlite import Starlite, post, get, Request, BaseRouteHandler, NotAuthorizedException
from starlite.types import ASGIApp, Scope, Receive, Send
from starlite.datastructures import State
from dotenv import load_dotenv
import os
from tinydb import TinyDB
from pydantic import BaseModel
import time

def start(state: State) -> None:
    load_dotenv()
    state.db = TinyDB(os.environ["DATALOGGER_DB"])
    state.keys = os.environ["DATALOGGER_KEYS"].split(",")

def guard_key(request: Request, _: BaseRouteHandler) -> None:
    if not request.headers.get("Authorization", "") in request.app.state.keys:
        raise NotAuthorizedException(detail=f'"{request.headers.get("Authorization", "")}" is not a valid API key.')

def log(db: TinyDB, sensor: str, data: Any, log_time: float):
    db.insert({
        "logged_at": log_time,
        "received_at": time.time(),
        "data": data
    })


def middleware_factory(app: ASGIApp) -> ASGIApp:
    async def my_middleware(scope: Scope, receive: Receive, send: Send) -> None:
        print(scope.items())
        await app(scope, receive, send)

    return my_middleware

class DataModel(BaseModel):
    logged_at: float
    data: Any

@post("/data/{sensor:str}", guards=[guard_key])
def post_data(sensor: str, data: DataModel, state: State) -> None:
    log(state.db, sensor, data.data, log_time=data.logged_at)



app = Starlite(route_handlers=[post_data], on_startup=[start], middleware=[middleware_factory])