from sqlalchemy import (
    Column, String, Text, DateTime, Integer, UUID, Date, 
    ForeignKey, CheckConstraint, UniqueConstraint, Index,
    Enum as SQLEnum, ARRAY
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
from enum import Enum
import uuid

Base = declarative_base()


class MenuChoices(Enum):
    USER_VERIFICATION = "USER_VERIFICATION"
    LIST = "LIST"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"
    RESCHEDULE = "RESCHEDULE"
    ROUTING = "ROUTING"

class Patient(Base):
    __tablename__ = "patients"
    
    patient_id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('phone', name='uq_patients_phone'),
        CheckConstraint("phone ~ '^\\+?[1-9][0-9]{7,14}$'", name='ck_phone_format'),
        Index('idx_patients_verification', 'phone', 'date_of_birth', func.lower('full_name'))
    )

class Conversation(Base):
    __tablename__ = "conversation"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    qa_system = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = "message"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(PostgresUUID(as_uuid=True), ForeignKey('conversation.id', ondelete='CASCADE'), nullable=False)
    request_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    user_message = Column(Text, nullable=False)
    latency_ms = Column(Integer)
    menu_choice = Column(SQLEnum(MenuChoices), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    system_message = Column(Text, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        CheckConstraint('input_tokens >= 0', name='ck_input_tokens_positive'),
        CheckConstraint('output_tokens >= 0', name='ck_output_tokens_positive'),
    )
