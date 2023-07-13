import uuid

from sqlalchemy import text
from sqlalchemy.exc import NoResultFound

from .db import Conn, engine
from .structure import (
    JoinRoomResult,
    LiveDifficulty,
    RoomInfo,
    RoomUser,
    SafeUser,
    WaitRoomStatus,
)


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げるエラー"""


def create_user(name: str, leader_card_id: int) -> str:
    """Create new user and returns their token"""
    # UUID4は天文学的な確率だけど衝突する確率があるので、気にするならリトライする必要がある。
    # サーバーでリトライしない場合は、クライアントかユーザー（手動）にリトライさせることになる。
    # ユーザーによるリトライは一般的には良くないけれども、確率が非常に低ければ許容できる場合もある。
    token = str(uuid.uuid4())
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `user` (name, token, leader_card_id)"
                " VALUES (:name, :token, :leader_card_id)"
            ),
            {"name": name, "token": token, "leader_card_id": leader_card_id},
        )
        print(f"create_user(): {result.lastrowid=}")  # DB側で生成されたPRIMARY KEYを参照できる
    return token


def update_user(conn: Conn, user: SafeUser, name: str, leader_card_id: int) -> None:
    conn.execute(
        text(
            "UPDATE user SET name = :name, leader_card_id = :leader_card_id WHERE id = :id"
        ),
        {"id": user.id, "name": name, "leader_card_id": leader_card_id},
    )


def _create_empty_room(conn: Conn, live_id: int) -> int:
    result = conn.execute(
        text(
            "INSERT INTO room (`live_id`, `user_count`, `room_status`) VALUES (:live_id, :user_count, :room_status)"
        ),
        {
            "live_id": live_id,
            "user_count": 0,
            "room_status": WaitRoomStatus.waiting.value,
        },
    )
    return result.lastrowid


def _enter_room(
    conn, room_id: int, user_id: int, difficulty: LiveDifficulty
) -> JoinRoomResult:
    result = conn.execute(
        text(
            "SELECT live_id, user_count, room_status FROM room WHERE id = :id FOR UPDATE"
        ),
        {"id": room_id},
    )
    try:
        room = result.one()
    except NoResultFound:
        return JoinRoomResult.other_error
    if room.user_count >= 4:
        return JoinRoomResult.room_full
    is_host = room.user_count == 0
    conn.execute(
        text(
            "INSERT INTO room_member (`room_id`, `user_id`, `is_host`, `live_difficulty`) "
            "VALUES(:room_id, :user_id, :is_host, :live_difficulty)"
        ),
        {
            "room_id": room_id,
            "user_id": user_id,
            "is_host": is_host,
            "live_difficulty": difficulty.value,
        },
    )
    conn.execute(
        text("UPDATE room SET user_count = user_count + 1 WHERE id = :room_id"),
        {"room_id": room_id},
    )
    return JoinRoomResult.ok


def create_room(
    conn: Conn, user: SafeUser, live_id: int, difficulty: LiveDifficulty
) -> int:
    """部屋を作ってroom_idを返します"""
    room_id = _create_empty_room(conn, live_id)
    _enter_room(conn, room_id, user.id, difficulty)
    return room_id


def list_room(conn: Conn, live_id: int) -> list[RoomInfo]:
    query_text = "SELECT * FROM room WHERE room_status = :room_status AND user_count < :max_user_count"
    query_dict = {"room_status": WaitRoomStatus.waiting.value, "max_user_count": 4}
    if live_id != 0:
        query_text += " AND live_id = :live_id"
        query_dict |= {"live_id": live_id}

    result = conn.execute(text(query_text), query_dict)
    rows = result.all()

    return [
        RoomInfo(
            room_id=row.id,
            live_id=row.live_id,
            joined_user_count=row.user_count,
            max_user_count=4,
        )
        for row in rows
    ]


def wait_room(room_id: int) -> tuple[WaitRoomStatus, list[RoomUser]]:
    pass
