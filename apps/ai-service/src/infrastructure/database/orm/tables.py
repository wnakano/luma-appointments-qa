from sqlalchemy import create_engine, inspect
from typing import (
    Any, 
    Dict,
    Type, 
    Tuple
)

from .models.schemas import (
    Base,
    ClinicORM,
    ProviderORM,
    PatientORM,
    AppointmentORM
)
from .models.models import (
    ClinicModel,
    ProviderModel,
    PatientModel,
    AppointmentModel
)


class DBTables:
    clinic: str = "clinic"
    provider: str = "provider"
    patient: str = "patient"
    appointment: str = "appointment"

    TABLE_MAP: Dict[str, Tuple[Type[Any], Type[Any]]] = {
        clinic: (ClinicORM, ClinicModel),
        provider: (ProviderORM, ProviderModel),
        patient: (PatientORM, PatientModel),
        appointment: (AppointmentORM, AppointmentModel),
    }

    @staticmethod
    def ensure_table_exists(engine, table_orm: Any) -> bool:
        """
        Create preco_distribuidora if it doesn't exist.
        Returns True if it was created, False if it already existed.
        """
        insp = inspect(engine)
        exists = insp.has_table(table_orm.__tablename__)
        if exists:
            return False
        return True


