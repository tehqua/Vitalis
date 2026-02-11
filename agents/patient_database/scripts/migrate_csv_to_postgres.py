"""Migrate CSV data to PostgreSQL database."""

import os
import sys
import pandas as pd
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine
from database.models import (
    Patient,
    Organization,
    Provider,
    Payer,
    Encounter,
    Observation,
    Medication,
    Procedure,
    Condition,
    Immunization,
    Allergy,
    CarePlan,
    ImagingStudy,
    Device,
    PayerTransition,
)
from database.session import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'csv')
BATCH_SIZE = 1000


def parse_date(date_str):
    """Parse date string to datetime, handling NaN values."""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return None


def migrate_organizations():
    """Migrate organizations data."""
    logger.info("Migrating organizations...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'organizations.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            org = Organization(
                id=row['Id'],
                name=row['NAME'],
                address=row['ADDRESS'],
                city=row['CITY'],
                state=row['STATE'],
                zip_code=row['ZIP'],
                latitude=float(row['LAT']) if row['LAT'] else None,
                longitude=float(row['LON']) if row['LON'] else None,
                phone=row['PHONE'] if row['PHONE'] else None,
                revenue=float(row['REVENUE']) if row['REVENUE'] else None,
                utilization=int(row['UTILIZATION']) if row['UTILIZATION'] else None,
            )
            batch.append(org)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} organizations")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} organizations")
        
        logger.info(f"Total organizations migrated: {len(df)}")
    finally:
        session.close()


def migrate_providers():
    """Migrate providers data."""
    logger.info("Migrating providers...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'providers.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            provider = Provider(
                id=row['Id'],
                organization_id=row['ORGANIZATION'] if row['ORGANIZATION'] else None,
                name=row['NAME'],
                gender=row['GENDER'] if row['GENDER'] else None,
                speciality=row['SPECIALITY'] if row['SPECIALITY'] else None,
                address=row['ADDRESS'],
                city=row['CITY'],
                state=row['STATE_HEADQUARTERED'] if 'STATE_HEADQUARTERED' in row else row.get('STATE', ''),
                zip_code=row['ZIP'],
                latitude=float(row['LAT']) if row['LAT'] else None,
                longitude=float(row['LON']) if row['LON'] else None,
                utilization=int(row['UTILIZATION']) if row['UTILIZATION'] else None,
            )
            batch.append(provider)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} providers")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} providers")
        
        logger.info(f"Total providers migrated: {len(df)}")
    finally:
        session.close()


def migrate_payers():
    """Migrate payers data."""
    logger.info("Migrating payers...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'payers.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            payer = Payer(
                id=row['Id'],
                name=row['NAME'],
                address=row['ADDRESS'] if row['ADDRESS'] else None,
                city=row['CITY'] if row['CITY'] else None,
                state_headquartered=row['STATE_HEADQUARTERED'] if row['STATE_HEADQUARTERED'] else None,
                zip_code=row['ZIP'] if row['ZIP'] else None,
                phone=row['PHONE'] if row['PHONE'] else None,
                amount_covered=float(row['AMOUNT_COVERED']) if row['AMOUNT_COVERED'] else None,
                amount_uncovered=float(row['AMOUNT_UNCOVERED']) if row['AMOUNT_UNCOVERED'] else None,
                revenue=float(row['REVENUE']) if row['REVENUE'] else None,
                covered_encounters=int(row['COVERED_ENCOUNTERS']) if row['COVERED_ENCOUNTERS'] else None,
                uncovered_encounters=int(row['UNCOVERED_ENCOUNTERS']) if row['UNCOVERED_ENCOUNTERS'] else None,
                covered_medications=int(row['COVERED_MEDICATIONS']) if row['COVERED_MEDICATIONS'] else None,
                uncovered_medications=int(row['UNCOVERED_MEDICATIONS']) if row['UNCOVERED_MEDICATIONS'] else None,
                covered_procedures=int(row['COVERED_PROCEDURES']) if row['COVERED_PROCEDURES'] else None,
                uncovered_procedures=int(row['UNCOVERED_PROCEDURES']) if row['UNCOVERED_PROCEDURES'] else None,
                covered_immunizations=int(row['COVERED_IMMUNIZATIONS']) if row['COVERED_IMMUNIZATIONS'] else None,
                uncovered_immunizations=int(row['UNCOVERED_IMMUNIZATIONS']) if row['UNCOVERED_IMMUNIZATIONS'] else None,
                unique_customers=int(row['UNIQUE_CUSTOMERS']) if row['UNIQUE_CUSTOMERS'] else None,
                qols_avg=float(row['QOLS_AVG']) if row['QOLS_AVG'] else None,
                member_months=int(row['MEMBER_MONTHS']) if row['MEMBER_MONTHS'] else None,
            )
            batch.append(payer)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} payers")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} payers")
        
        logger.info(f"Total payers migrated: {len(df)}")
    finally:
        session.close()


def migrate_patients():
    """Migrate patients data."""
    logger.info("Migrating patients...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'patients.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            patient = Patient(
                id=row['Id'],
                birth_date=parse_date(row['BIRTHDATE']),
                death_date=parse_date(row['DEATHDATE']) if row['DEATHDATE'] and row['DEATHDATE'] != '2999-12-31 00:00:00' else None,
                ssn=row['SSN'] if row['SSN'] else None,
                drivers=row['DRIVERS'] if row['DRIVERS'] else None,
                passport=row['PASSPORT'] if row['PASSPORT'] else None,
                prefix=row['PREFIX'] if row['PREFIX'] else None,
                first_name=row['FIRST'],
                last_name=row['LAST'],
                suffix=row['SUFFIX'] if row['SUFFIX'] else None,
                maiden_name=row['MAIDEN'] if row['MAIDEN'] else None,
                marital_status=row['MARITAL'] if row['MARITAL'] else None,
                race=row['RACE'],
                ethnicity=row['ETHNICITY'],
                gender=row['GENDER'],
                birthplace=row['BIRTHPLACE'] if row['BIRTHPLACE'] else None,
                address=row['ADDRESS'],
                city=row['CITY'],
                state=row['STATE'],
                county=row['COUNTY'] if row['COUNTY'] else None,
                zip_code=row['ZIP'],
                latitude=float(row['LAT']) if row['LAT'] else None,
                longitude=float(row['LON']) if row['LON'] else None,
                healthcare_expenses=float(row['HEALTHCARE_EXPENSES']) if row['HEALTHCARE_EXPENSES'] else None,
                healthcare_coverage=float(row['HEALTHCARE_COVERAGE']) if row['HEALTHCARE_COVERAGE'] else None,
            )
            batch.append(patient)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} patients")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} patients")
        
        logger.info(f"Total patients migrated: {len(df)}")
    finally:
        session.close()


def migrate_encounters():
    """Migrate encounters data."""
    logger.info("Migrating encounters...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'encounters.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            encounter = Encounter(
                id=row['Id'],
                start=parse_date(row['START']),
                stop=parse_date(row['STOP']),
                patient_id=row['PATIENT'],
                organization_id=row['ORGANIZATION'] if row['ORGANIZATION'] else None,
                provider_id=row['PROVIDER'] if row['PROVIDER'] else None,
                payer_id=row['PAYER'] if row['PAYER'] else None,
                encounter_class=row['ENCOUNTERCLASS'] if row['ENCOUNTERCLASS'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                base_encounter_cost=float(row['BASE_ENCOUNTER_COST']) if row['BASE_ENCOUNTER_COST'] else None,
                total_claim_cost=float(row['TOTAL_CLAIM_COST']) if row['TOTAL_CLAIM_COST'] else None,
                payer_coverage=float(row['PAYER_COVERAGE']) if row['PAYER_COVERAGE'] else None,
                reason_code=row['REASONCODE'] if row['REASONCODE'] else None,
                reason_description=row['REASONDESCRIPTION'] if row['REASONDESCRIPTION'] else None,
            )
            batch.append(encounter)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} encounters")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} encounters")
        
        logger.info(f"Total encounters migrated: {len(df)}")
    finally:
        session.close()


def migrate_observations():
    """Migrate observations data."""
    logger.info("Migrating observations...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'observations.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            observation = Observation(
                date=parse_date(row['DATE']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=str(row['CODE']) if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                value=str(row['VALUE']) if row['VALUE'] else None,
                units=row['UNITS'] if row['UNITS'] else None,
                type=row['TYPE'] if row['TYPE'] else None,
            )
            batch.append(observation)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} observations")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} observations")
        
        logger.info(f"Total observations migrated: {len(df)}")
    finally:
        session.close()


def migrate_medications():
    """Migrate medications data."""
    logger.info("Migrating medications...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'medications.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            medication = Medication(
                start=parse_date(row['START']),
                stop=parse_date(row['STOP']),
                patient_id=row['PATIENT'],
                payer_id=row['PAYER'] if row['PAYER'] else None,
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                base_cost=float(row['BASE_COST']) if row['BASE_COST'] else None,
                payer_coverage=float(row['PAYER_COVERAGE']) if row['PAYER_COVERAGE'] else None,
                dispenses=int(row['DISPENSES']) if row['DISPENSES'] else None,
                total_cost=float(row['TOTALCOST']) if row['TOTALCOST'] else None,
                reason_code=row['REASONCODE'] if row['REASONCODE'] else None,
                reason_description=row['REASONDESCRIPTION'] if row['REASONDESCRIPTION'] else None,
            )
            batch.append(medication)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} medications")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} medications")
        
        logger.info(f"Total medications migrated: {len(df)}")
    finally:
        session.close()


def migrate_procedures():
    """Migrate procedures data."""
    logger.info("Migrating procedures...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'procedures.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            procedure = Procedure(
                date=parse_date(row['DATE']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                base_cost=float(row['BASE_COST']) if row['BASE_COST'] else None,
                reason_code=row['REASONCODE'] if row['REASONCODE'] else None,
                reason_description=row['REASONDESCRIPTION'] if row['REASONDESCRIPTION'] else None,
            )
            batch.append(procedure)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} procedures")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} procedures")
        
        logger.info(f"Total procedures migrated: {len(df)}")
    finally:
        session.close()


def migrate_conditions():
    """Migrate conditions data."""
    logger.info("Migrating conditions...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'conditions.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            condition = Condition(
                start=parse_date(row['START']),
                stop=parse_date(row['STOP']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
            )
            batch.append(condition)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} conditions")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} conditions")
        
        logger.info(f"Total conditions migrated: {len(df)}")
    finally:
        session.close()


def migrate_immunizations():
    """Migrate immunizations data."""
    logger.info("Migrating immunizations...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'immunizations.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            immunization = Immunization(
                date=parse_date(row['DATE']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                base_cost=float(row['BASE_COST']) if row['BASE_COST'] else None,
            )
            batch.append(immunization)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} immunizations")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} immunizations")
        
        logger.info(f"Total immunizations migrated: {len(df)}")
    finally:
        session.close()


def migrate_allergies():
    """Migrate allergies data."""
    logger.info("Migrating allergies...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'allergies.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            allergy = Allergy(
                start=parse_date(row['START']),
                stop=parse_date(row['STOP']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
            )
            batch.append(allergy)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} allergies")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} allergies")
        
        logger.info(f"Total allergies migrated: {len(df)}")
    finally:
        session.close()


def migrate_careplans():
    """Migrate careplans data."""
    logger.info("Migrating careplans...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'careplans.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            careplan = CarePlan(
                id=row['Id'],
                start=parse_date(row['START']),
                stop=parse_date(row['STOP']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                reason_code=row['REASONCODE'] if row['REASONCODE'] else None,
                reason_description=row['REASONDESCRIPTION'] if row['REASONDESCRIPTION'] else None,
            )
            batch.append(careplan)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} careplans")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} careplans")
        
        logger.info(f"Total careplans migrated: {len(df)}")
    finally:
        session.close()


def migrate_imaging_studies():
    """Migrate imaging studies data."""
    logger.info("Migrating imaging studies...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'imaging_studies.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            imaging_study = ImagingStudy(
                id=row['Id'],
                date=parse_date(row['DATE']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                bodysite_code=row['BODYSITE_CODE'] if row['BODYSITE_CODE'] else None,
                bodysite_description=row['BODYSITE_DESCRIPTION'] if row['BODYSITE_DESCRIPTION'] else None,
                modality_code=row['MODALITY_CODE'] if row['MODALITY_CODE'] else None,
                modality_description=row['MODALITY_DESCRIPTION'] if row['MODALITY_DESCRIPTION'] else None,
                sop_code=row['SOP_CODE'] if row['SOP_CODE'] else None,
                sop_description=row['SOP_DESCRIPTION'] if row['SOP_DESCRIPTION'] else None,
            )
            batch.append(imaging_study)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} imaging studies")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} imaging studies")
        
        logger.info(f"Total imaging studies migrated: {len(df)}")
    finally:
        session.close()


def migrate_devices():
    """Migrate devices data."""
    logger.info("Migrating devices...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'devices.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            device = Device(
                start=parse_date(row['START']),
                stop=parse_date(row['STOP']),
                patient_id=row['PATIENT'],
                encounter_id=row['ENCOUNTER'] if row['ENCOUNTER'] else None,
                code=row['CODE'] if row['CODE'] else None,
                description=row['DESCRIPTION'] if row['DESCRIPTION'] else None,
                udi=row['UDI'] if row['UDI'] else None,
            )
            batch.append(device)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} devices")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} devices")
        
        logger.info(f"Total devices migrated: {len(df)}")
    finally:
        session.close()


def migrate_payer_transitions():
    """Migrate payer transitions data."""
    logger.info("Migrating payer transitions...")
    df = pd.read_csv(os.path.join(CSV_DIR, 'payer_transitions.csv'))
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df = df.fillna('')
    
    session = SessionLocal()
    try:
        batch = []
        for _, row in df.iterrows():
            transition = PayerTransition(
                patient_id=row['PATIENT'],
                start_year=int(row['START_YEAR']) if row['START_YEAR'] else None,
                end_year=int(row['END_YEAR']) if row['END_YEAR'] else None,
                payer_id=row['PAYER'],
                ownership=row['OWNERSHIP'] if row['OWNERSHIP'] else None,
            )
            batch.append(transition)
            
            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Inserted {len(batch)} payer transitions")
                batch = []
        
        if batch:
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"Inserted {len(batch)} payer transitions")
        
        logger.info(f"Total payer transitions migrated: {len(df)}")
    finally:
        session.close()


def main():
    """Main migration function."""
    logger.info("Starting database migration...")
    logger.info("Creating database tables...")
    
    Base.metadata.create_all(bind=engine)
    
    logger.info("Tables created successfully.")
    logger.info("Starting data migration in dependency order...")
    
    migrate_organizations()
    migrate_providers()
    migrate_payers()
    migrate_patients()
    migrate_encounters()
    migrate_observations()
    migrate_medications()
    migrate_procedures()
    migrate_conditions()
    migrate_immunizations()
    migrate_allergies()
    migrate_careplans()
    migrate_imaging_studies()
    migrate_devices()
    migrate_payer_transitions()
    
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    main()
