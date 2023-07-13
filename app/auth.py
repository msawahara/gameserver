"""
認証モジュール

引数に `token: UserToken` を指定することで認証を行い、そのユーザーの
tokenを取得できる。
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound

from .db import Conn
from .structure import SafeUser

__all__ = ["UserToken"]
bearer = HTTPBearer()


async def get_auth_token(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    assert cred is not None
    if not cred.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid credential")
    return cred.credentials


UserToken = Annotated[str, Depends(get_auth_token)]


def get_user_by_token(conn: Conn, token: str) -> SafeUser | None:
    result = conn.execute(
        text("SELECT * FROM user WHERE token = :token"), {"token": token}
    )
    try:
        row = result.one()
        return SafeUser.from_orm(row)
    except NoResultFound:
        return None


def get_safe_user(conn: Conn, token: UserToken) -> SafeUser:
    user = get_user_by_token(conn, token)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="user not found")
    raise Exception("TEST")
    return user


AuthorizedUser = Annotated[SafeUser, Depends(get_safe_user)]
