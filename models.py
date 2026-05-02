#reference from: https://docs.sqlalchemy.org/en/20/intro.html#installation
#

import uuid
from sqlalchemy import Column, String, Integer
from database import Base

#makes the items
class Item(Base):
    __tablename__ = "items"

#this is the phase 1 btw
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    short_name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)
    amount = Column(Integer)