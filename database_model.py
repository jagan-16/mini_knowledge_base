from sqlalchemy import Column, Integer, String, ForeignKey, Text , DateTime , BigInteger , Float
from sqlalchemy.dialects.postgresql import UUID , JSONB
import uuid
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from database import Base


class TimestampMixin:
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class Document(Base, TimestampMixin):

    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    title = Column(
        String(255),
        nullable=False
    )

    file_name = Column(
        String(255),
        nullable=False
    )

    content_type = Column(
        String(100),
        nullable=False
    )

    file_size = Column(
        BigInteger,
        nullable=False
    )
    
    
    file_path = Column(

    String(500),

    nullable=False
)

    doc_metadata = Column(
        JSONB,
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="uploaded"
    )

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
class Chunk(Base, TimestampMixin):

    __tablename__ = "chunks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        index = True,
        nullable=False
    )
    
    chunk_hash = Column(
    String(64),
    nullable=False,
    index=True
)

    chunk_index = Column(
        Integer,
        nullable=False
    )

    chunk_text = Column(
        Text,
        nullable=False
    )
    


    embedding = Column(
        Vector(768),
        nullable=True
    )

    page_number = Column(
        Integer,
        nullable=True
    )

    token_count = Column(
        Integer,
        nullable=True
    )

    document = relationship(
        "Document",
        back_populates="chunks"
    )

  
    


   
    
   
class Conversation(Base , TimestampMixin):
        
        __tablename__ = "conversations"
        
        id      = Column( UUID(as_uuid=True) , 
                         primary_key= True ,
                         default= uuid.uuid4 , 
                         index= True ,
                        )        
        messages = relationship(
            "Message" , 
            back_populates= "conversation",
             order_by="Message.created_at.asc()"
        )
       
class Message(Base ,TimestampMixin ):
        
        __tablename__ =  "messages"
        
        id  = Column (UUID(as_uuid=True),
                      primary_key=True ,
                      default= uuid.uuid4 ,
                      index= True ,
                      )
        conversation_id =  Column(UUID(as_uuid=True),
                                  ForeignKey("conversations.id") ,
                                  nullable = False ,
                                  index= True
                                  )
        role           = Column(String , 
                                nullable= False
                                )  
        content     = Column(Text , 
                             nullable= False
                             )   
        
        citations = Column(JSONB, 
                           nullable=False,
                           default=list,
                           )
        
        
        conversation = relationship(
            "Conversation" ,
            back_populates= "messages"
        )  
        
       
        