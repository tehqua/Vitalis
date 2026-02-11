"""Medical history service for database operations."""

from typing import List, Optional
from datetime import datetime, timedelta

from database.models import (
    Encounter,
    Observation,
    Medication,
    Condition,
    Procedure,
    Allergy,
    Immunization,
)
from database.session import get_session


def _detach_objects(session, objects):
    """Helper to detach objects from session before it closes.
    
    Args:
        session: SQLAlchemy session
        objects: Single object or list of objects to detach
    
    Returns:
        The same objects, detached from session
    """
    if isinstance(objects, list):
        for obj in objects:
            # Access key attributes to force loading
            if hasattr(obj, 'description'):
                _ = obj.description
            if hasattr(obj, 'start'):
                _ = obj.start
            if hasattr(obj, 'date'):
                _ = obj.date
        session.expunge_all()
    else:
        if objects:
            session.expunge(objects)
    return objects


class MedicalHistoryService:
    """Service class for medical history-related database operations."""

    @staticmethod
    def get_encounters(
        patient_id: str, days_back: int = 365, limit: int = 100
    ) -> List[Encounter]:
        """
        Get patient encounters within a time period.

        Args:
            patient_id: Patient UUID string
            days_back: Number of days to look back from today
            limit: Maximum number of results

        Returns:
            List of Encounter objects ordered by most recent first
        """
        with get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            results = (
                session.query(Encounter)
                .filter(Encounter.patient_id == patient_id)
                .filter(Encounter.start >= cutoff_date)
                .order_by(Encounter.start.desc())
                .limit(limit)
                .all()
            )
            return _detach_objects(session, results)

    @staticmethod
    def get_observations(
        patient_id: str,
        observation_type: Optional[str] = None,
        days_back: int = 365,
        limit: int = 100,
    ) -> List[Observation]:
        """
        Get patient observations within a time period.

        Args:
            patient_id: Patient UUID string
            observation_type: Filter by description (partial match)
            days_back: Number of days to look back from today
            limit: Maximum number of results

        Returns:
            List of Observation objects ordered by most recent first
        """
        with get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query = (
                session.query(Observation)
                .filter(Observation.patient_id == patient_id)
                .filter(Observation.date >= cutoff_date)
            )

            if observation_type:
                query = query.filter(
                    Observation.description.ilike(f"%{observation_type}%")
                )

            results = query.order_by(Observation.date.desc()).limit(limit).all()
            return _detach_objects(session, results)

    @staticmethod
    def get_active_medications(patient_id: str) -> List[Medication]:
        """
        Get patient's currently active medications.

        Args:
            patient_id: Patient UUID string

        Returns:
            List of Medication objects that are currently active
        """
        with get_session() as session:
            current_date = datetime.now()
            results = (
                session.query(Medication)
                .filter(Medication.patient_id == patient_id)
                .filter(
                    (Medication.stop.is_(None))
                    | (Medication.stop >= current_date)
                )
                .order_by(Medication.start.desc())
                .all()
            )
            return _detach_objects(session, results)

    @staticmethod
    def get_medication_history(
        patient_id: str, days_back: int = 365, limit: int = 100
    ) -> List[Medication]:
        """
        Get patient medication history.

        Args:
            patient_id: Patient UUID string
            days_back: Number of days to look back from today
            limit: Maximum number of results

        Returns:
            List of Medication objects
        """
        with get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return (
                session.query(Medication)
                .filter(Medication.patient_id == patient_id)
                .filter(Medication.start >= cutoff_date)
                .order_by(Medication.start.desc())
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_active_conditions(patient_id: str) -> List[Condition]:
        """
        Get patient's currently active conditions.

        Args:
            patient_id: Patient UUID string

        Returns:
            List of Condition objects that are currently active
        """
        with get_session() as session:
            current_date = datetime.now()
            results = (
                session.query(Condition)
                .filter(Condition.patient_id == patient_id)
                .filter(
                    (Condition.stop.is_(None)) | (Condition.stop >= current_date)
                )
                .order_by(Condition.start.desc())
                .all()
            )
            return _detach_objects(session, results)

    @staticmethod
    def get_condition_history(
        patient_id: str, days_back: int = 365, limit: int = 100
    ) -> List[Condition]:
        """
        Get patient condition history.

        Args:
            patient_id: Patient UUID string
            days_back: Number of days to look back from today
            limit: Maximum number of results

        Returns:
            List of Condition objects
        """
        with get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return (
                session.query(Condition)
                .filter(Condition.patient_id == patient_id)
                .filter(Condition.start >= cutoff_date)
                .order_by(Condition.start.desc())
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_procedures(
        patient_id: str, days_back: int = 365, limit: int = 100
    ) -> List[Procedure]:
        """
        Get patient procedures.

        Args:
            patient_id: Patient UUID string
            days_back: Number of days to look back from today
            limit: Maximum number of results

        Returns:
            List of Procedure objects
        """
        with get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return (
                session.query(Procedure)
                .filter(Procedure.patient_id == patient_id)
                .filter(Procedure.date >= cutoff_date)
                .order_by(Procedure.date.desc())
                .limit(limit)
                .all()
            )

    @staticmethod
    def get_active_allergies(patient_id: str) -> List[Allergy]:
        """
        Get patient's currently active allergies.

        Args:
            patient_id: Patient UUID string

        Returns:
            List of Allergy objects that are currently active
        """
        with get_session() as session:
            current_date = datetime.now()
            results = (
                session.query(Allergy)
                .filter(Allergy.patient_id == patient_id)
                .filter(
                    (Allergy.stop.is_(None)) | (Allergy.stop >= current_date)
                )
                .order_by(Allergy.start.desc())
                .all()
            )
            return _detach_objects(session, results)

    @staticmethod
    def get_immunizations(
        patient_id: str, days_back: int = 365, limit: int = 100
    ) -> List[Immunization]:
        """
        Get patient immunization records.

        Args:
            patient_id: Patient UUID string
            days_back: Number of days to look back from today
            limit: Maximum number of results

        Returns:
            List of Immunization objects
        """
        with get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return (
                session.query(Immunization)
                .filter(Immunization.patient_id == patient_id)
                .filter(Immunization.date >= cutoff_date)
                .order_by(Immunization.date.desc())
                .limit(limit)
                .all()
            )
