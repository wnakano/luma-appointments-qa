from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from enum import Enum


class AppointmentStatus(str, Enum):
    SCHEDULED = 'scheduled'
    CONFIRMED = 'confirmed'
    CANCELED_BY_PATIENT = 'canceled_by_patient'
    CANCELED_BY_CLINIC = 'canceled_by_clinic'


class ClinicCreate(BaseModel):
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class ProviderCreate(BaseModel):
    clinic_id: UUID
    full_name: str
    specialty: Optional[str] = None


class PatientCreate(BaseModel):
    full_name: str
    phone: str = Field(..., min_length=8, max_length=20)
    date_of_birth: date
    email: Optional[EmailStr] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        if not re.match(r'^\+?[1-9][0-9]{7,14}$', v):
            raise ValueError('Invalid phone format')
        return v


class AppointmentCreate(BaseModel):
    patient_id: UUID
    clinic_id: UUID
    provider_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    
    @field_validator('ends_at')
    @classmethod
    def validate_time_order(cls, v: datetime, info) -> datetime:
        if 'starts_at' in info.data and v <= info.data['starts_at']:
            raise ValueError('ends_at must be after starts_at')
        return v


class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class ProviderUpdate(BaseModel):
    clinic_id: Optional[UUID] = None
    full_name: Optional[str] = None
    specialty: Optional[str] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=8, max_length=20)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            import re
            if not re.match(r'^\+?[1-9][0-9]{7,14}$', v):
                raise ValueError('Invalid phone format')
        return v


class AppointmentUpdate(BaseModel):
    patient_id: Optional[UUID] = None
    clinic_id: Optional[UUID] = None
    provider_id: Optional[UUID] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    
    @field_validator('ends_at')
    @classmethod
    def validate_time_order(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v is not None and 'starts_at' in info.data and info.data['starts_at'] is not None:
            if v <= info.data['starts_at']:
                raise ValueError('ends_at must be after starts_at')
        return v


class ClinicModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    created_at: datetime


class ProviderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    clinic_id: UUID
    full_name: str
    specialty: Optional[str] = None
    created_at: datetime


class PatientModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    full_name: str
    phone: str
    date_of_birth: date
    email: Optional[str] = None
    created_at: datetime


class AppointmentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    patient_id: UUID
    clinic_id: UUID
    provider_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime


class ProviderWithClinic(ProviderModel):
    clinic: ClinicModel


class AppointmentDetailed(AppointmentModel):
    patient: PatientModel
    clinic: ClinicModel
    provider: ProviderModel


class PatientWithAppointments(PatientModel):
    appointments: list[AppointmentModel] = []


class ClinicWithProviders(ClinicModel):
    providers: list[ProviderModel] = []