from .userRepo import UserRepo
from .clientRepo import ClientRepo
from .memberRepo import MemberRepo
from db.base import database


def get_client_repo() -> ClientRepo:
    """ `Row` filds: `id`, `work_id`, `status_id`, `api_id`, `api_hash`, `phone`, `created_at`"""
    return ClientRepo(database)

def get_user_repo() -> UserRepo:
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `role_id`, `created_at` """
    return UserRepo(database)

def get_member_repo() -> MemberRepo:
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `chat_id`, `created_at` """
    return MemberRepo(database)
