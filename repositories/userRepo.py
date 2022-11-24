from .baseRepo import BaseRepo
from typing import List, Optional
from db.model_users import User
import sqlalchemy as sa
from sqlalchemy.engine import Row 
from datetime import datetime

class UserRepo(BaseRepo):
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `role_id`, `created_at` """

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        query = sa.select(User).limit(limit).offset(skip)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: int) -> Optional[Row]:
        query = sa.select(User).where(User.id==id)
        return await self.database.fetch_one(query)

    async def get_by_username(self, username: str) -> Optional[Row]:
        query = sa.select(User).where(User.username==username)
        return await self.database.fetch_one(query)

    async def create(self, id: int, 
                           first_name: Optional[str], 
                           last_name: Optional[str], 
                           username: Optional[str], 
                           role_id:int) -> int:
        """`return`  id: `int`"""
        user = {
            'id': id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'role_id': role_id,
            'created_at': datetime.now(),
        }

        query = sa.insert(User).values(**user)
        return await self.database.execute(query)

    
    async def update(self, id: int, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(User).where(User.id==id).values(**kwargs)
        return await self.database.execute(query)
    





# # class User(Base):
#     __tablename__ = 'users'
#     __table_args__ = {"comment": "Юзеры"}

#     id = Column(BigInteger, primary_key=True)
#     first_name = Column(String(50))
#     last_name = Column(String(50))
#     username = Column(String(50), nullable=False)
#     role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
#     # status_id = Column(Integer, ForeignKey('user_status.id'))
#     created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)