from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field

# Enum


class LiveDifficulty(IntEnum):
    """難易度"""

    normal = 1
    hard = 2


class JoinRoomResult(IntEnum):
    """部屋参加結果"""

    ok = 1  # 入室OK
    room_full = 2  # 満員
    disbanded = 3  # 解散済み
    other_error = 4  # その他エラー


class WaitRoomStatus(IntEnum):
    """部屋待機状態"""

    waiting = 1
    live_start = 2
    dissolution = 3


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

    model_config = ConfigDict(from_attributes=True)


# User APIs


class Empty(BaseModel):
    pass


class UserCreateRequest(BaseModel):
    user_name: str = Field(title="ユーザー名")
    leader_card_id: int = Field(title="リーダーカードのID")


class UserCreateResponse(BaseModel):
    user_token: str


# Room APIs


class RoomID(BaseModel):
    room_id: int


class CreateRoomRequest(BaseModel):
    live_id: int
    select_difficulty: LiveDifficulty


class ListRoomRequest(BaseModel):
    live_id: int


class RoomInfo(BaseModel):
    room_id: int
    live_id: int
    joined_user_count: int
    max_user_count: int


class ListRoomResponse(BaseModel):
    room_info_list: list[RoomInfo]


class WaitRoomRequest(BaseModel):
    room_id: int


class RoomUser(BaseModel):
    user_id: int
    name: str
    leader_card_id: int
    select_diffiulty: LiveDifficulty
    is_me: bool
    is_host: bool


class WaitRoomResponse(BaseModel):
    status: WaitRoomStatus
    room_user_list: list[RoomUser]
