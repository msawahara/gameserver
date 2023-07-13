from typing import Annotated

from fastapi import Depends
from sqlalchemy import Connection, create_engine

from . import config

engine = create_engine(config.DATABASE_URI, future=True, echo=True, pool_recycle=300)


def get_conn() -> Connection:
    print("get_conn")
    with engine.begin() as conn:
        yield conn
    print("close transaction")


Conn = Annotated[Connection, Depends(get_conn)]
