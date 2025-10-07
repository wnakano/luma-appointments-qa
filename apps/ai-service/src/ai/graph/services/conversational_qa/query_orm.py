from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from typing import (
	Any, 
	Dict,
	List, 
	Optional,
	Union
)
from uuid import UUID

from infrastructure.database.orm import DatabaseEngine, DatabaseReader
from infrastructure.database.orm.models.schemas import AppointmentORM

from ...models.conversational_qa import VerificationInfoModel
from ...types.conversational_qa import DBAppointmentStatus

from utils import Logger

logger = Logger(__name__)


class QueryORMService:
	VALID_STATUSES = {
		DBAppointmentStatus.CONFIRMED,
		DBAppointmentStatus.CANCELED_BY_PATIENT,
	}
	
	def __init__(self) -> None:
		self.reader = DatabaseReader()
	
	def find_appointments_by_patient_id(
		self, 
		patient_id: Union[UUID, str],
	) -> Optional[List[Dict[str, Any]]]:

		logger.info("[SERVICE] QueryORMService.find_appointments_by_patient_id")
		
		try:
			if not isinstance(patient_id, UUID):
				patient_id = UUID(patient_id)
			
			logger.info(f" ... Searching appointments for patient: {patient_id}")

			appointments = self.reader.get_appointments_by_patient_id(
				patient_id=patient_id
			)
			
			if appointments:
				logger.info(f" ... Found {len(appointments)} appointment(s)")
			else:
				logger.info(" ... No appointments found")
			
			return appointments
			
		except ValueError as e:
			logger.error(f"Invalid patient_id format: {e}")
			return None
		except Exception as e:
			logger.error(f"Error in find_appointments_by_patient_id: {e}", exc_info=True)
			return None
	
	def update_appointment_status(
		self,
		appointment_id: Union[UUID, str],
		new_status: str
	) -> Optional[AppointmentORM]:
		logger.info("[SERVICE] QueryORMService.update_appointment_status")
		
		session: Optional[Session] = None
		
		try:
			if not isinstance(appointment_id, UUID):
				appointment_id = UUID(appointment_id)
			if new_status not in self.VALID_STATUSES:
				raise ValueError(
					f"Invalid status '{new_status}'. "
					f"Valid statuses: {list(self.VALID_STATUSES)}"
				)
			
			logger.info(
				f" ... Updating appointment {appointment_id} to status '{new_status}'"
			)
			
			engine = DatabaseEngine()
			session = engine.get_session()
			
			appointment = session.query(AppointmentORM).filter(
				AppointmentORM.id == appointment_id
			).first()
			
			if not appointment:
				raise ValueError(f"Appointment {appointment_id} not found")
			
			old_status = appointment.status
			logger.info(f" ... Changing status from '{old_status}' to '{new_status}'")
			appointment.status = new_status
			
			session.commit()
			session.refresh(appointment)
			
			logger.info(f" ... Successfully updated appointment {appointment_id}")
			
			return appointment
			
		except ValueError as e:
			logger.error(f"Validation error: {e}")
			if session:
				session.rollback()
			raise
		except SQLAlchemyError as e:
			logger.error(f"Database error updating appointment: {e}", exc_info=True)
			if session:
				session.rollback()
			return None
		except Exception as e:
			logger.error(f"Unexpected error updating appointment: {e}", exc_info=True)
			if session:
				session.rollback()
			return None
		finally:
			if session:
				session.close()
	
	def find_user(
		self, 
		user_info: VerificationInfoModel,
		allow_partial: bool = False
	) -> Optional[List[Dict[str, Any]]]:
		logger.info("[SERVICE] QueryORMService.find_user")
		logger.info(f" ... Searching for user with: {user_info.model_dump()}")
		
		try:
			strategies = self._build_search_strategies(
				user_info=user_info, 
				allow_partial=allow_partial
			)
			
			for idx, strategy in enumerate(strategies, 1):
				if not all(strategy.values()):
					continue
				
				logger.info(f" ... Trying strategy {idx}: {list(strategy.keys())}")
				
				result = self.reader.get_user(**strategy)
				
				if result:
					fields = ' + '.join(strategy.keys())
					logger.info(f" ... Found match using: {fields}")
					return result
			
			logger.info(" ... No user match found with any strategy")
			return None
			
		except Exception as e:
			logger.error(f"Error in find_user: {e}", exc_info=True)
			return None
	
	def _build_search_strategies(
		self,
		user_info: VerificationInfoModel,
		allow_partial: bool = False
	) -> List[Dict[str, Any]]:

		strategies = []
		
		if not allow_partial:
			if all([user_info.full_name, user_info.phone_number, user_info.date_of_birth]):
				strategies.append({
					'full_name': user_info.full_name,
					'phone_number': user_info.phone_number,
					'date_of_birth': user_info.date_of_birth
				})
			
		else:
			if user_info.full_name:
				strategies.append({
					'full_name': user_info.full_name
				})
			
			if user_info.phone_number:
				strategies.append({
					'phone_number': user_info.phone_number
				})
			
			if user_info.date_of_birth:
				strategies.append({
					'date_of_birth': user_info.date_of_birth
				})
			
		logger.info(f" ... Built {len(strategies)} search strategy(ies)")
		
		return strategies