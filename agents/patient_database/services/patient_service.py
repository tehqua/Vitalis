"""Patient service for database operations."""

from typing import List, Optional
from sqlalchemy.orm import Session

from database.models import Patient
from database.session import get_session


class PatientService:
    """Service class for patient-related database operations."""

    @staticmethod
    def get_by_id(patient_id: str) -> Optional[Patient]:
        """
        Get patient by ID.

        Args:
            patient_id: Patient UUID string

        Returns:
            Patient object or None if not found
        """
        with get_session() as session:
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            if patient:
                # Access all attributes while session is open
                # This forces SQLAlchemy to load all data before session closes
                _ = patient.first_name
                _ = patient.last_name
                _ = patient.birth_date
                _ = patient.death_date
                session.expunge(patient)  # Detach from session
            return patient

    @staticmethod
    def search(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        ssn: Optional[str] = None,
        limit: int = 100,
    ) -> List[Patient]:
        """
        Search patients by criteria.

        Args:
            first_name: Patient first name (partial match)
            last_name: Patient last name (partial match)
            ssn: Social Security Number (exact match)
            limit: Maximum number of results to return

        Returns:
            List of Patient objects matching criteria
        """
        with get_session() as session:
            query = session.query(Patient)

            if first_name:
                query = query.filter(
                    Patient.first_name.ilike(f"%{first_name}%")
                )

            if last_name:
                query = query.filter(
                    Patient.last_name.ilike(f"%{last_name}%")
                )

            if ssn:
                query = query.filter(Patient.ssn == ssn)

            return query.limit(limit).all()

    @staticmethod
    def get_all(limit: int = 1000, offset: int = 0) -> List[Patient]:
        """
        Get all patients with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of Patient objects
        """
        with get_session() as session:
            return session.query(Patient).limit(limit).offset(offset).all()
