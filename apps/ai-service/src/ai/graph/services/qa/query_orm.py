from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import (
	Any, 
	Dict, 
	Optional,
	Union
)
from uuid import UUID

from infrastructure.database.orm import DatabaseEngine, DatabaseReader
from infrastructure.database.orm.models.schemas import AppointmentORM

from utils import Logger

logger = Logger(__name__)


class QueryORMService:
	"""Service for finding and retrieving exact user matches from database using ORM queries"""


	def __init__(
		self
	) -> None:
		pass

	def find_appointments_by_patient_id(
		self, 
		patient_id: Union[UUID, str],
		# intent: UserIntent
	) -> Any:
		"""
		Find exact user match in database and return complete user record
		
		Args:
			user_info: Extracted user information (name, birthday, phone)
			intent: User intent for context
			
		Returns:
			UserValidationResult with found user data or validation failure details
		"""
		try:
			if not isinstance(patient_id, UUID):
				patient_id = UUID(patient_id)
			reader = DatabaseReader()
			appointments = reader.get_appointments_by_patient_id(patient_id=patient_id)
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
	
	# async def find_user(
	# 	self, 
	# 	user_info: UserValidationResult
	# ) -> Optional[Dict[str, Any]]:
	# 	"""
	# 	Find exact user match using direct database queries
		
	# 	Returns:
	# 		Complete user record if found, None otherwise
	# 	"""
	# 	logger.info(f"Searching for user: {user_info.model_dump()}")
	# 	try:
	# 		# Match all three fields (most restrictive)
	# 		exact_match = await self._query_user_by_all_fields(
	# 			user_info=user_info
	# 		)
	# 		if exact_match:
	# 			logger.info(f"Found exact match for user: {user_info.full_name}")
	# 			return exact_match
			
	# 		# Match by phone + name (phone is usually unique)
	# 		phone_name_match = await self._query_user_by_phone_name(
	# 			user_info=user_info
	# 		)
	# 		if phone_name_match:
	# 			logger.info(f"Found match by phone+name for user: {user_info.full_name}")
	# 			return phone_name_match
			
	# 		# Match by phone only (if phone is unique identifier)
	# 		phone_match = await self._query_user_by_phone(
	# 			user_info=user_info
	# 		)
	# 		if phone_match:
	# 			logger.info(f"Found match by phone for user: {user_info.phone_number}")
	# 			return phone_match
				
	# 		return None
			
	# 	except Exception as e:
	# 		logger.error(f"Error in exact user match search: {e}")
	# 		return None
	
	# async def _query_user_by_all_fields(
	# 	self, 
	# 	user_info: UserValidationResult
	# ) -> Optional[Dict[str, Any]]:
	# 	query = """
	# 	SELECT patient_id, full_name, phone, date_of_birth, email
	# 	FROM patients 
	# 	WHERE LOWER(TRIM(full_name)) = LOWER(TRIM($1)) 
	# 	AND phone = $2
	# 	AND date_of_birth = $3
	# 	LIMIT 1
	# 	"""	
	# 	# Convert date to string format for PostgreSQL
	# 	date_str = user_info.date_of_birth.strftime("%Y-%m-%d") if user_info.date_of_birth else None
		
	# 	params = [
	# 		user_info.full_name,
	# 		user_info.phone,
	# 		date_str
	# 	]
		
	# 	result = await mcp_manager.execute_db_query(query, params)
	# 	logger.info(f"[_query_user_by_all_fields] result: {result}")
		
	# 	if result.get("status") == "success" and result.get("data"):
	# 		return result["data"][0]
	# 	return None
	
	# async def _query_user_by_phone_name(
	# 	self, 
	# 	user_info: UserValidationResult
	# ) -> Optional[Dict[str, Any]]:
	# 	"""Query user by phone number and name"""
	# 	query = """
	# 	SELECT patient_id, full_name, phone, date_of_birth, email
	# 	FROM patients 
	# 	WHERE LOWER(TRIM(full_name)) = LOWER(TRIM($1)) 
	# 	AND phone = $2
	# 	LIMIT 1
	# 	"""
		
	# 	params = [user_info.full_name, user_info.phone]
	# 	result = await mcp_manager.execute_db_query(query, params)
	# 	logger.info(f"[_query_user_by_phone_name] result: {result}")
	# 	if result.get("status") == "success" and result.get("data"):
	# 		return result["data"][0]
	# 	return None
	
	# async def _query_user_by_phone(
	# 	self, 
	# 	user_info: UserValidationResult
	# ) -> Optional[Dict[str, Any]]:
	# 	"""Query user by phone number only"""
	# 	query = """
	# 	SELECT patient_id, full_name, phone, date_of_birth, email
	# 	FROM patients 
	# 	WHERE phone = $1
	# 	LIMIT 1
	# 	"""
		
	# 	params = [user_info.phone]
	# 	result = await mcp_manager.execute_db_query(query, params)
	# 	logger.info(f"[_query_user_by_phone] result: {result}")
	# 	if result.get("status") == "success" and result.get("data"):
	# 		return result["data"][0]
	# 	return None
	