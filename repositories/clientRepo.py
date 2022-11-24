from typing import List, Optional
from datetime import datetime
import sqlalchemy as sa
from .baseRepo import BaseRepo
from sqlalchemy.engine import Row
from db.model_client import Client
from enums import CWorkes, CStatuses



class ClientRepo(BaseRepo):
    """ `Row` filds: `id`, `work_id`, `status_id`, `api_id`, `api_hash`, `phone`, `created_at`"""

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: int) -> Optional[Row]:
        query = sa.select(Client).where(Client.id==id)
        return await self.database.fetch_one(query)

    async def get_by_phone(self, phone: str) -> Optional[Row]:
        query = sa.select(Client).where(Client.phone==phone)
        return await self.database.fetch_one(query)

    async def get_by_work_id(self, work_id: int, 
                                   limit: int = 100, 
                                   skip: int = 0
                                   ) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip).where(Client.work_id==work_id)
        return await self.database.fetch_all(query)
    
    async def get_by_status_id(self, status_id: int, 
                                     limit: int = 100, 
                                     skip: int = 0
                                     ) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip).where(Client.status_id==status_id)
        return await self.database.fetch_all(query)

    async def create(self, work_id: int, 
                           status_id: int, 
                           api_id: int, 
                           api_hash: str,
                           phone: str,
                           ) -> int:
        """`return`  id: `int`"""
        client_acc = {
            'work_id': work_id,
            'status_id': status_id,
            'api_id': api_id,
            'api_hash': api_hash,
            'phone': phone,
            'created_at': datetime.now(),
        }

        query = sa.insert(Client).values(**client_acc)
        return await self.database.execute(query)

    async def update(self, id: int, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(Client).where(Client.id==id).values(**kwargs)
        return await self.database.execute(query)

    async def delete(self, id: int):
        query = sa.delete(Client).where(Client.id==id)
        return await self.database.execute(query)

# class Client(Base):
#     __tablename__ = 'client_accounts'
#     __table_args__ = {"comment": "Аккаунты парсеры"}

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     work_id = Column(Integer, ForeignKey('client_workes.id'),nullable=False, default=CWorkes.UNWORKING.value['id'])
#     status_id = Column(Integer, ForeignKey('client_statuses.id'),nullable=False, default=CStatuses.WAITING_AUTHORIZATION.value['id'])
#     api_id = Column(Integer, nullable=False)
#     api_hash = Column(String(50), nullable=False)
#     phone = Column(String(16), nullable=False)
#     created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)