from sqlalchemy import Integer , JSON , DateTime , Boolean
from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column  
from typing import List
from datetime import datetime , timezone

class Base(DeclarativeBase):
    pass

      
class ModMailBlacklist(Base):
    __tablename__ = "modmailblacklist"
    guild_id : Mapped[int] = mapped_column(Integer , primary_key=True)
    user_id : Mapped[int] = mapped_column(Integer , primary_key=True)
    time : Mapped[datetime] = mapped_column(DateTime , default=lambda : datetime.now(timezone.utc))

class Ticket(Base):
    __tablename__ = "ticket"
    id : Mapped[int] = mapped_column(Integer , autoincrement=True)
    guild_id : Mapped[int] = mapped_column(Integer , primary_key=True)
    user_id : Mapped[int] = mapped_column(Integer , primary_key=True)
    thread_id : Mapped[int] = mapped_column(Integer , nullable=False)
    active : Mapped[bool] = mapped_column(Boolean , default=True)
    created_at : Mapped[datetime] = mapped_column(DateTime , default= lambda : datetime.now(timezone.utc))
    

