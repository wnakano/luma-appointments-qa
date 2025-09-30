from sqlalchemy import (
    Column, String, Text, Date, DateTime, Integer, 
    CheckConstraint, UniqueConstraint, ForeignKey, Enum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum
import uuid

Base = declarative_base()


class ClinicORM(Base):
    __tablename__ = 'clinic'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    address_line1 = Column(Text)
    address_line2 = Column(Text)
    city = Column(Text)
    state = Column(Text)
    postal_code = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    providers = relationship('ProviderORM', back_populates='clinic', cascade='all, delete-orphan')
    appointments = relationship('AppointmentORM', back_populates='clinic')


class ProviderORM(Base):
    __tablename__ = 'provider'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey('clinic.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(Text, nullable=False)
    specialty = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    clinic = relationship('ClinicORM', back_populates='providers')
    appointments = relationship('AppointmentORM', back_populates='provider')


class PatientORM(Base):
    __tablename__ = 'patient'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('phone', name='uq_patients_phone'),
        CheckConstraint("phone ~ '^\\+?[1-9][0-9]{7,14}$'", name='ck_phone_format'),
        Index('idx_patients_verification', 'phone', 'date_of_birth', func.lower('full_name')),
    )
    
    # Relationships
    appointments = relationship('AppointmentORM', back_populates='patient')


class AppointmentORM(Base):
    __tablename__ = 'appointment'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patient.id', ondelete='CASCADE'), nullable=False)
    clinic_id = Column(UUID(as_uuid=True), ForeignKey('clinic.id', ondelete='RESTRICT'), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey('provider.id', ondelete='RESTRICT'), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text)
    status = Column(Text, nullable=False, server_default='scheduled')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        CheckConstraint('ends_at > starts_at', name='ck_time_order'),
        CheckConstraint(
            "status IN ('scheduled','confirmed','canceled_by_patient','canceled_by_clinic')", 
            name='ck_status'
        ),
    )
    
    # Relationships
    patient = relationship('PatientORM', back_populates='appointments')
    clinic = relationship('ClinicORM', back_populates='appointments')
    provider = relationship('ProviderORM', back_populates='appointments')
