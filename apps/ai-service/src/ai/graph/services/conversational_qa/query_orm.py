from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
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

from ...models.conversational_qa import (
    VerificationInfoModel, 
    VerificationRecordModel
)

from utils import Logger

logger = Logger(__name__)


class QueryORMService:
	"""Service for finding and retrieving exact user matches from database using ORM queries"""


	def __init__(
		self
	) -> None:
		self.reader = DatabaseReader()

	def find_appointments_by_patient_id(
		self, 
		patient_id: Union[UUID, str],
		# intent: UserIntent
	) -> Union[None, List[Dict[str, Any]]]:
		
		"""
		Find exact user match in database and return complete user record
		
		Args:
			user_info: Extracted user information (name, birthday, phone)
			intent: User intent for context
			
		Returns:
			UserValidationResult with found user data or validation failure details
		"""
		logger.info("[SERVICE] QueryORMService.find_appointments_by_patient_id")
		try:
			if not isinstance(patient_id, UUID):
				patient_id = UUID(patient_id)
			
			appointments = self.reader.get_appointments_by_patient_id(
				patient_id=patient_id
			)
			return appointments

		except Exception as e:
			logger.error(f"Error in find_appointments_by_patient_id: {e}")
			return None
		
	def update_appointment_status(
		self,
		appointment_id: Union[UUID, str],
		new_status: str
	) -> AppointmentORM:
		"""
		Update the status of an appointment.

		Args:
			appointment_id: UUID of the appointment to update
			new_status: New status value (must be one of: 'scheduled', 'confirmed',
					'canceled_by_patient', 'canceled_by_clinic')

		Returns:
			AppointmentORM: The updated appointment object

		Raises:
			AppointmentStatusError: If appointment not found or invalid status provided
		"""
		logger.info("[SERVICE] QueryORMService.update_appointment_status")

		logger.info(f"Updating appointment {appointment_id} to status '{new_status}'")
		if not isinstance(appointment_id, UUID):
			appointment_id = UUID(appointment_id)
		VALID_STATUSES = {
			'confirmed', 
			'canceled', 
		}
		engine = DatabaseEngine()
		session: Session = engine.get_session()

		# Fetch the appointment
		appointment = session.query(AppointmentORM).filter(
			AppointmentORM.id == appointment_id
		).first()
		
		
		# Update the status
		appointment.status = new_status
		
		# Commit the changes
		session.commit()
		session.refresh(appointment)
		
		return appointment
	
	def find_user(
		self, 
		user_info: VerificationInfoModel
	) -> Optional[Dict[str, Any]]:
		"""Find user match using progressive fallback strategies"""
		logger.info("[SERVICE] QueryORMService.find_user")
		logger.info(f"Searching for user: {user_info.model_dump()}")
		
		# Define search strategies in priority order
		strategies = [
			# All three fields
			{
				'full_name': user_info.full_name,
				'phone_number': user_info.phone_number,
				'date_of_birth': user_info.date_of_birth
			},
			# Two fields
			# {'full_name': user_info.full_name, 'phone_number': user_info.phone_number},
			# {'full_name': user_info.full_name, 'date_of_birth': user_info.date_of_birth},
			# {'date_of_birth': user_info.date_of_birth, 'phone_number': user_info.phone_number},
			# # Single fields
			# {'full_name': user_info.full_name},
			{'phone_number': user_info.phone_number},
		]
		
		try:
			for strategy in strategies:
				result = self.reader.get_user(**strategy)
				if result:
					fields = '+'.join(strategy.keys())
					logger.info(f"Found match by {fields}")
					return result
			
			return None
			
		except Exception as e:
			logger.error(f"Error in exact user match search: {e}")
			return None
	