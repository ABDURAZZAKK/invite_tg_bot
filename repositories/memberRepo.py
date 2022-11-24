from .baseRepo import BaseRepo
from typing import List, Optional
from db.model_member import Member
import sqlalchemy as sa
from sqlalchemy.engine import Row 
from datetime import datetime



class MemberRepo(BaseRepo):
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `chat_id`, `created_at` """

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        query = sa.select(Member).limit(limit).offset(skip)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: int) -> Optional[Row]:
        query = sa.select(Member).where(Member.id==id)
        return await self.database.fetch_one(query)

    async def get_by_username(self, username: str) -> Optional[Row]:
        query = sa.select(Member).where(Member.username==username)
        return await self.database.fetch_one(query)

    async def create(self, id: int, 
                           first_name: Optional[str], 
                           last_name: Optional[str], 
                           username: Optional[str], 
                           chat_id:int) -> int:
        """`return`  id: `int`"""
        user = {
            'id': id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'chat_id': chat_id,
            'created_at': datetime.now(),
        }

        query = sa.insert(Member).values(**user)
        return await self.database.execute(query)

    
    async def update(self, id: int, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(Member).where(Member.id==id).values(**kwargs)
        return await self.database.execute(query)




# class Member(Base):
#     __tablename__ = 'members'
#     __table_args__ = {"comment": "Спарсенные участники групп"}

#     id = Column(BigInteger, primary_key=True)
#     first_name = Column(String(50))
#     last_name = Column(String(50))
#     username = Column(String(50))
#     invite_restricted = Column(Boolean, comment='Заблокирован ли у юзера приём инвайтов (1 - да)') TODO я не чекаю запрещено инвайтить или нет
#     chat_id = Column(BigInteger)
#     created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)