from datetime import date, datetime
from typing import (
	Any, 
	Dict,
	List,
	Union
)
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import (
    Session,
    joinedload
)
from .tables import DBTables
from .engine import DatabaseEngine
# from .models.models import 
from .models.schemas import (
    Base, 
    AppointmentORM, 
    PatientORM
)

from utils import Logger

logger = Logger(__name__)


class DatabaseReader(DatabaseEngine):
	def __init__(self):
		super().__init__()

	def _serialize(self, val):
		if isinstance(val, UUID):
			return str(val)
		if isinstance(val, (datetime, date)):
			return val.isoformat()
		return val
	
	def get_all(
		self, 
		table_name: str
		) -> List[Dict]:
		
		mapping = DBTables.TABLE_MAP.get(table_name)
		orm_cls, model_cls = mapping

		session: Session = self.get_session()
		try:
			records = session.query(orm_cls).all()
			return [
				{field: self._serialize(getattr(rec, field))
					for field in model_cls.__annotations__}
				for rec in records
			]
		finally:
			session.close()

	def get_feature_value(
		self,
		table_name: str,
		feature_name: str
		) -> List[Any]:
		"""
		Return all values for `feature_name` from the table `table_name`.

		Parameters
		----------
		table_name : str
			Name of the table as registered in Base.metadata (usually your
			ORM class’ __tablename__).
		feature_name : str
			Name of the column/feature in that table.

		Returns
		-------
		List[Any]
			All values (possibly with duplicates) in that column.
		"""
		session: Session = self.get_session()
		try:
			table = Base.metadata.tables.get(table_name)
			if table is None:
				raise NoSuchTableError(f"Table '{table_name}' not found")

			column = table.c.get(feature_name)
			if column is None:
				raise KeyError(f"Column '{feature_name}' not found in '{table_name}'")

			stmt = select(column)
			result = session.execute(stmt)

			return [row[0] for row in result.fetchall()]

		finally:
			session.close()

	def get_feature_values(
		self,
		table_name: str,
		feature_names: List[str]
		) -> List[Any]:
		"""
		Return all values for `feature_names` from the table `table_name`.

		Parameters
		----------
		table_name : str
			Name of the table as registered in Base.metadata (usually your
			ORM class’ __tablename__).
		feature_names : List[str]
			List of names of the columns/features in that table.

		Returns
		-------
		List[Any]
			All values (possibly with duplicates) in that column.
		"""
		session: Session = self.get_session()
		try:
			table = Base.metadata.tables.get(table_name)
			if table is None:
				raise NoSuchTableError(f"Table '{table_name}' not found")

			column_objs = []
			for col_name in feature_names:
				col = table.c.get(col_name)
				if col is None:
					raise KeyError(f"Column '{col_name}' not found in '{table_name}'")
				column_objs.append(col)

			# build and run query
			stmt = select(*column_objs)
			rows = session.execute(stmt).fetchall()

			# format results
			if len(column_objs) == 1:
				return [row[0] for row in rows]
			else:
				return [
					{col_name: value for col_name, value in zip(feature_names, row)}
					for row in rows
				]

		finally:
			session.close()

	def get_appointments_by_patient_id(
		self, 
		patient_id: UUID,
		include_past: bool = False
	) -> Union[None, List[Dict[str, Any]]]:
		"""
		Get all appointments for a patient using SQLAlchemy ORM.
		
		Parameters
		----------
		patient_id : UUID
			The UUID of the patient
		include_past : bool, optional
			If True, includes past appointments. Default is False (future only).
		
		Returns
		-------
		Union[None, List[Dict[str, Any]]]
			List of appointment records with clinic and provider information
		"""
		
		session: Session = self.get_session()
		try:
			query = (
				session.query(AppointmentORM)
				.options(
					joinedload(AppointmentORM.clinic),
					joinedload(AppointmentORM.provider)
				)
				.filter(AppointmentORM.patient_id == patient_id)
			)
			
			if not include_past:
				query = query.filter(AppointmentORM.starts_at >= datetime.now())
			
			query = query.order_by(AppointmentORM.starts_at.asc())
			
			appointments_orm = query.all()
			
			# Convert to dictionaries
			appointments = []
			for appt in appointments_orm:
				appointment = {
					"id": self._serialize(appt.id),
					"starts_at": self._serialize(appt.starts_at),
					"ends_at": self._serialize(appt.ends_at),
					"reason": appt.reason,
					"status": appt.status,
					"clinic": {
						"name": appt.clinic.name,
						"address_line1": appt.clinic.address_line1,
						"address_line2": appt.clinic.address_line2,
						"city": appt.clinic.city,
						"state": appt.clinic.state,
						"postal_code": appt.clinic.postal_code
					},
					"provider": {
						"full_name": appt.provider.full_name,
						"specialty": appt.provider.specialty
					}
				}
				appointments.append(appointment)
			
			return appointments
			
		except Exception as e:
			logger.error(f"get_patient_appointments_orm failed: {e}")
		finally:
			session.close()
		return None
		
	def get_user(
		self, 
		full_name: Union[str, None] = None,
		phone_number: Union[str, None] = None,
		date_of_birth: Union[str, None] = None
	) -> Union[None, List[Dict[str, Any]]]:
		"""
		Get all appointments for a patient using SQLAlchemy ORM.
		
		Parameters
		----------
		patient_id : UUID
			The UUID of the patient
		include_past : bool, optional
			If True, includes past appointments. Default is False (future only).
		
		Returns
		-------
		List[Dict[str, Any]]
			List of appointment records with clinic and provider information
		"""
		
		session: Session = self.get_session()
		patients = []
		try:
			conditions = []
			if full_name is not None:
				conditions.append(PatientORM.full_name == full_name)
			if phone_number is not None:
				conditions.append(PatientORM.phone == phone_number)
			if date_of_birth is not None:
				conditions.append(PatientORM.date_of_birth == date_of_birth)

			query = session.query(PatientORM)
			if conditions:
				query = query.filter(and_(*conditions))
			
			
			patients_orm = query.all()
			
			patients = []
			for patient_orm in patients_orm:
				patient = {
					"id": self._serialize(patient_orm.id),
					"full_name": patient_orm.full_name,
					"phone_number": patient_orm.phone,
					"date_of_birth": patient_orm.date_of_birth,
				}
				patients.append(patient)
			
			return patients
			
		except Exception as e:
			logger.error(f"get_user failed: {e}")
			
		finally:
			session.close()
			logger.info(f"patients = {patients}")
			return patients