import fastapi.exception_handlers
from fastapi import FastAPI, HTTPException, status

from app.db import Conn

from . import model
from .auth import AuthorizedUser, UserToken, get_user_by_token
from .structure import (
    CreateRoomRequest,
    Empty,
    ListRoomRequest,
    ListRoomResponse,
    RoomID,
    SafeUser,
    UserCreateRequest,
    UserCreateResponse,
    WaitRoomRequest,
    WaitRoomResponse,
)
from fastapi.exceptions import RequestValidationError

from . import model
from .auth import UserToken

app = FastAPI()


# リクエストのvalidation errorをprintする
# このエラーが出たら、リクエストのModel定義が間違っている
@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(req, exc):
    print("Request validation error")
    print(f"{req.url=}\n{exc.body=}\n{exc=!s}")
    return await fastapi.exception_handlers.request_validation_exception_handler(
        req, exc
    )


# Sample API
@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}


# User APIs

@app.post("/user/create")
def user_create(req: UserCreateRequest) -> UserCreateResponse:
    """新規ユーザー作成"""
    token = model.create_user(req.user_name, req.leader_card_id)
    return UserCreateResponse(user_token=token)


# 認証動作確認用のサンプルAPI
# ゲームアプリは使わない
@app.get("/user/me")
def user_me(conn: Conn, token: UserToken) -> SafeUser:
    user = get_user_by_token(conn, token)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # print(f"user_me({token=}, {user=})")
    # 開発中以外は token をログに残してはいけない。
    return user

@app.post("/user/update")
def update(req: UserCreateRequest, conn: Conn, user: AuthorizedUser) -> Empty:
    """Update user attributes"""
    model.update_user(conn, user, req.user_name, req.leader_card_id)
    return Empty()


# Room APIs

@app.post("/room/create")
def create(conn: Conn, user: AuthorizedUser, req: CreateRoomRequest) -> RoomID:
    """ルーム作成リクエスト"""
    room_id = model.create_room(conn, user, req.live_id, req.select_difficulty)
    return RoomID(room_id=room_id)


@app.post("/room/list")
def room_list(conn: Conn, req: ListRoomRequest) -> ListRoomResponse:
    room_info_list = model.list_room(conn, req.live_id)
    return ListRoomResponse(room_info_list=room_info_list)


@app.post("/room/wait")
def room_wait(conn: Conn, req: WaitRoomRequest) -> WaitRoomResponse:
    status, users = model.wait_room(req.room_id)
    return WaitRoomResponse(status=status, room_user_list=users)
