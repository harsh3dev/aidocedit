from sqlalchemy import Column, String, Integer, Text
from database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String, nullable=False)
    template_type = Column(String, nullable=False)
    content = Column(Text, default="")
