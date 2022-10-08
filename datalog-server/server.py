from datetime import datetime
from typing import Any, List, Optional
from starlite import Starlite, post, get, Request, BaseRouteHandler, NotAuthorizedException
from starlite.datastructures import State
from dotenv import load_dotenv
import os
from tinydb import TinyDB, where
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
        "sensor": sensor,
        "logged_at": log_time,
        "received_at": time.time(),
        "data": data
    })

def get_from_db(db: TinyDB, sensors: List[str], before: datetime, after: datetime):
    if (not sensors and not before and not after):
        return db.all()
    q = []
    if sensors:
        q.append('where("sensor").one_of(sensors)')
    if before:
        q.append('where("logged_at") <= before')
    if after:
        q.append('where("logged_at") >= after')
    
    return eval(
        f'db.search({" & ".join(q)})', 
        {
            "sensors": sensors if sensors else [], 
            "before": before.timestamp() if before else 0, 
            "after": after.timestamp() if after else 0, 
            "db": db,
            "where": where
        }
    )

class DataModel(BaseModel):
    logged_at: float
    data: Any

@post("/data/{sensor:str}", guards=[guard_key])
def post_data(sensor: str, data: DataModel, state: State) -> None:
    log(state.db, sensor, data.data, log_time=data.logged_at)

@get("/data")
def get_data(state: State, sensors: Optional[List[str]] = None, before: Optional[datetime] = None, after: Optional[datetime] = None) -> List[Any]:
    return get_from_db(state.db, sensors, before, after)



app = Starlite(route_handlers=[post_data, get_data], on_startup=[start])