"""SQLAlchemy ORM models for patient database."""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .config import Base


class Patient(Base):
    """Patient demographics and personal information."""

    __tablename__ = "patients"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    birth_date = Column(DateTime, nullable=False, index=True)
    death_date = Column(DateTime, nullable=True)
    ssn = Column(String(11), nullable=True, index=True)
    drivers = Column(String(50), nullable=True)
    passport = Column(String(50), nullable=True)
    prefix = Column(String(10), nullable=True)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    suffix = Column(String(10), nullable=True)
    maiden_name = Column(String(100), nullable=True)
    marital_status = Column(String(10), nullable=True)
    race = Column(String(50), nullable=True)
    ethnicity = Column(String(50), nullable=True)
    gender = Column(String(1), nullable=False)
    birthplace = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    county = Column(String(100), nullable=True)
    zip_code = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    healthcare_expenses = Column(Float, nullable=True)
    healthcare_coverage = Column(Float, nullable=True)

    encounters = relationship("Encounter", back_populates="patient")
    observations = relationship("Observation", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    procedures = relationship("Procedure", back_populates="patient")
    conditions = relationship("Condition", back_populates="patient")
    immunizations = relationship("Immunization", back_populates="patient")
    allergies = relationship("Allergy", back_populates="patient")
    careplans = relationship("CarePlan", back_populates="patient")
    imaging_studies = relationship("ImagingStudy", back_populates="patient")
    devices = relationship("Device", back_populates="patient")
    payer_transitions = relationship("PayerTransition", back_populates="patient")


class Organization(Base):
    """Healthcare organizations and facilities."""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(50), nullable=True)
    revenue = Column(Float, nullable=True)
    utilization = Column(Integer, nullable=True)

    encounters = relationship("Encounter", back_populates="organization")
    providers = relationship("Provider", back_populates="organization")


class Provider(Base):
    """Healthcare providers (physicians, nurses, specialists)."""

    __tablename__ = "providers"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    organization_id = Column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )
    name = Column(String(255), nullable=False, index=True)
    gender = Column(String(1), nullable=True)
    speciality = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    utilization = Column(Integer, nullable=True)

    organization = relationship("Organization", back_populates="providers")
    encounters = relationship("Encounter", back_populates="provider")


class Payer(Base):
    """Insurance payers and coverage providers."""

    __tablename__ = "payers"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state_headquartered = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    amount_covered = Column(Float, nullable=True)
    amount_uncovered = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    covered_encounters = Column(Integer, nullable=True)
    uncovered_encounters = Column(Integer, nullable=True)
    covered_medications = Column(Integer, nullable=True)
    uncovered_medications = Column(Integer, nullable=True)
    covered_procedures = Column(Integer, nullable=True)
    uncovered_procedures = Column(Integer, nullable=True)
    covered_immunizations = Column(Integer, nullable=True)
    uncovered_immunizations = Column(Integer, nullable=True)
    unique_customers = Column(Integer, nullable=True)
    qols_avg = Column(Float, nullable=True)
    member_months = Column(Integer, nullable=True)

    encounters = relationship("Encounter", back_populates="payer")
    medications = relationship("Medication", back_populates="payer")
    payer_transitions = relationship("PayerTransition", back_populates="payer")


class Encounter(Base):
    """Patient visits and medical encounters."""

    __tablename__ = "encounters"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    start = Column(DateTime, nullable=False, index=True)
    stop = Column(DateTime, nullable=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    organization_id = Column(
        UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=True
    )
    provider_id = Column(
        UUID(as_uuid=False), ForeignKey("providers.id"), nullable=True
    )
    payer_id = Column(UUID(as_uuid=False), ForeignKey("payers.id"), nullable=True)
    encounter_class = Column(String(50), nullable=True, index=True)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    base_encounter_cost = Column(Float, nullable=True)
    total_claim_cost = Column(Float, nullable=True)
    payer_coverage = Column(Float, nullable=True)
    reason_code = Column(String(50), nullable=True)
    reason_description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="encounters")
    organization = relationship("Organization", back_populates="encounters")
    provider = relationship("Provider", back_populates="encounters")
    payer = relationship("Payer", back_populates="encounters")
    observations = relationship("Observation", back_populates="encounter")
    medications = relationship("Medication", back_populates="encounter")
    procedures = relationship("Procedure", back_populates="encounter")
    conditions = relationship("Condition", back_populates="encounter")
    immunizations = relationship("Immunization", back_populates="encounter")
    allergies = relationship("Allergy", back_populates="encounter")
    careplans = relationship("CarePlan", back_populates="encounter")
    imaging_studies = relationship("ImagingStudy", back_populates="encounter")
    devices = relationship("Device", back_populates="encounter")

    __table_args__ = (
        Index("idx_encounter_patient_date", "patient_id", "start"),
    )


class Observation(Base):
    """Clinical measurements and observations."""

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True, index=True)
    value = Column(Text, nullable=True)
    units = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)

    patient = relationship("Patient", back_populates="observations")
    encounter = relationship("Encounter", back_populates="observations")

    __table_args__ = (
        Index("idx_observation_patient_date", "patient_id", "date"),
        Index("idx_observation_code", "code"),
    )


class Medication(Base):
    """Prescription medication records."""

    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False, index=True)
    stop = Column(DateTime, nullable=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    payer_id = Column(UUID(as_uuid=False), ForeignKey("payers.id"), nullable=True)
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True, index=True)
    base_cost = Column(Float, nullable=True)
    payer_coverage = Column(Float, nullable=True)
    dispenses = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)
    reason_code = Column(String(50), nullable=True)
    reason_description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="medications")
    payer = relationship("Payer", back_populates="medications")
    encounter = relationship("Encounter", back_populates="medications")

    __table_args__ = (
        Index("idx_medication_patient_date", "patient_id", "start"),
        Index("idx_medication_active", "patient_id", "stop"),
    )


class Procedure(Base):
    """Medical procedures performed on patients."""

    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    base_cost = Column(Float, nullable=True)
    reason_code = Column(String(50), nullable=True)
    reason_description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="procedures")
    encounter = relationship("Encounter", back_populates="procedures")

    __table_args__ = (
        Index("idx_procedure_patient_date", "patient_id", "date"),
    )


class Condition(Base):
    """Patient diagnoses and medical conditions."""

    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False, index=True)
    stop = Column(DateTime, nullable=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True, index=True)

    patient = relationship("Patient", back_populates="conditions")
    encounter = relationship("Encounter", back_populates="conditions")

    __table_args__ = (
        Index("idx_condition_patient_date", "patient_id", "start"),
        Index("idx_condition_active", "patient_id", "stop"),
    )


class Immunization(Base):
    """Vaccination records."""

    __tablename__ = "immunizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    base_cost = Column(Float, nullable=True)

    patient = relationship("Patient", back_populates="immunizations")
    encounter = relationship("Encounter", back_populates="immunizations")

    __table_args__ = (
        Index("idx_immunization_patient_date", "patient_id", "date"),
    )


class Allergy(Base):
    """Patient allergy records."""

    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False, index=True)
    stop = Column(DateTime, nullable=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="allergies")
    encounter = relationship("Encounter", back_populates="allergies")

    __table_args__ = (Index("idx_allergy_active", "patient_id", "stop"),)


class CarePlan(Base):
    """Care plan records for patient treatment."""

    __tablename__ = "careplans"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    start = Column(DateTime, nullable=False, index=True)
    stop = Column(DateTime, nullable=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    reason_code = Column(String(50), nullable=True)
    reason_description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="careplans")
    encounter = relationship("Encounter", back_populates="careplans")

    __table_args__ = (
        Index("idx_careplan_patient_date", "patient_id", "start"),
    )


class ImagingStudy(Base):
    """Medical imaging study records."""

    __tablename__ = "imaging_studies"

    id = Column(UUID(as_uuid=False), primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    bodysite_code = Column(String(50), nullable=True)
    bodysite_description = Column(Text, nullable=True)
    modality_code = Column(String(50), nullable=True)
    modality_description = Column(Text, nullable=True)
    sop_code = Column(String(50), nullable=True)
    sop_description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="imaging_studies")
    encounter = relationship("Encounter", back_populates="imaging_studies")

    __table_args__ = (
        Index("idx_imaging_patient_date", "patient_id", "date"),
    )


class Device(Base):
    """Medical devices used in patient care."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=False, index=True)
    stop = Column(DateTime, nullable=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id = Column(
        UUID(as_uuid=False), ForeignKey("encounters.id"), nullable=True
    )
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    udi = Column(String(255), nullable=True)

    patient = relationship("Patient", back_populates="devices")
    encounter = relationship("Encounter", back_populates="devices")

    __table_args__ = (Index("idx_device_patient_date", "patient_id", "start"),)


class PayerTransition(Base):
    """Insurance payer transition history."""

    __tablename__ = "payer_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(
        UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False, index=True
    )
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=True)
    payer_id = Column(UUID(as_uuid=False), ForeignKey("payers.id"), nullable=False)
    ownership = Column(String(50), nullable=True)

    patient = relationship("Patient", back_populates="payer_transitions")
    payer = relationship("Payer", back_populates="payer_transitions")

    __table_args__ = (
        Index("idx_payer_transition_patient", "patient_id", "start_year"),
    )


class Supply(Base):
    """Medical supplies used in patient care."""

    __tablename__ = "supplies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=False), nullable=True)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=True)
