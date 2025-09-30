"""Tests for QueryORMService (ORM-based database operations)."""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4


@pytest.mark.unit
class TestQueryORMService:
    """Test cases for QueryORMService (ORM-based database operations)."""
    
    @patch("ai.graph.services.qa.query_orm.DatabaseEngine")
    def test_query_orm_service_initialization(self, mock_db_engine):
        """Test that QueryORMService initializes with database connection."""
        from ai.graph.services.qa.query_orm import QueryORMService
        
        service = QueryORMService()
        
        assert service is not None
    
    @patch("ai.graph.services.qa.query_orm.DatabaseReader")
    def test_query_appointments(
        self, 
        mock_db_reader,
        sample_appointment
    ):
        """Test querying appointments for a patient from database."""
        from ai.graph.services.qa.query_orm import QueryORMService
        
        mock_appointment = Mock()
        mock_appointment.id = sample_appointment["id"]
        mock_appointment.date = sample_appointment["date"]
        mock_appointment.time = sample_appointment["time"]
        mock_appointment.doctor = sample_appointment["doctor"]
        mock_appointment.type = sample_appointment["type"]
        
        mock_reader_instance = Mock()
        mock_reader_instance.get_appointments_by_patient_id.return_value = [mock_appointment]
        mock_db_reader.return_value = mock_reader_instance
        
        service = QueryORMService()
        patient_id = uuid4()
        
        result = service.find_appointments_by_patient_id(patient_id=patient_id)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].doctor == sample_appointment["doctor"]
        mock_reader_instance.get_appointments_by_patient_id.assert_called_once_with(patient_id=patient_id)
    
    @patch("ai.graph.services.qa.query_orm.DatabaseEngine")
    def test_update_appointment_status(
        self,
        mock_db_engine,
        sample_appointment
    ):
        """Test updating an appointment status from scheduled to confirmed."""
        from ai.graph.services.qa.query_orm import QueryORMService
        
        appointment_id = sample_appointment["id"]
        mock_appointment = Mock()
        mock_appointment.id = appointment_id
        mock_appointment.status = sample_appointment["status"]
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_appointment
        
        mock_session = Mock()
        mock_session.query.return_value = mock_query
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        mock_engine_instance = Mock()
        mock_engine_instance.get_session.return_value = mock_session
        mock_db_engine.return_value = mock_engine_instance
        
        service = QueryORMService()
        new_status = "confirmed"
        
        result = service.update_appointment_status(
            appointment_id=appointment_id,
            new_status=new_status
        )
        
        assert result is not None
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_appointment)
        
