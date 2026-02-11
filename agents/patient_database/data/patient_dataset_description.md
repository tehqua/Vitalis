# Patient Database Dataset Description

**Last Updated:** February 8, 2026  
**Version:** 1.0  
**Total Records:** 472,396 rows across 16 tables  
**Total Size:** ~244 MB

---

## Overview

This dataset contains comprehensive healthcare information for 1,171 patients, including their medical encounters, observations, medications, procedures, conditions, and other clinical data. The data is structured across 16 CSV files representing different aspects of patient care in a hospital system.

The dataset follows a relational database schema where patient information is linked through foreign key relationships, primarily using the patient identifier field to connect related records across different tables.

---

## Dataset Statistics

### Primary Statistics
- **Total Patients:** 1,171 unique individuals
- **Total Encounters:** 53,346 patient visits
- **Average Encounters per Patient:** 45.6 visits
- **Total Clinical Observations:** 299,697 measurements
- **Total Medication Prescriptions:** 42,989 records
- **Total Medical Procedures:** 34,981 procedures performed
- **Total Diagnoses:** 8,376 condition records

### Data Quality
- **Data Completeness:** Generally high with <16% missing values across most tables
- **Referential Integrity:** 100% - All foreign key references are valid
- **Primary Key Uniqueness:** Verified across all tables

---

## Table Descriptions

### 1. PATIENTS (patients.csv)
**Primary table containing core patient demographic and administrative information.**

- **Records:** 1,171
- **Columns:** 25
- **Size:** 1.30 MB
- **Missing Values:** 15.89%

**Key Fields:**
- `Id` (Primary Key): Unique patient identifier (UUID format)
- `BIRTHDATE`: Patient date of birth
- `DEATHDATE`: Date of death (if applicable, 14.6% of patients deceased)
- `SSN`: Social Security Number
- `DRIVERS`: Driver's license number
- `PASSPORT`: Passport number
- `PREFIX`: Name prefix (Mr., Mrs., Ms., Dr., etc.)
- `FIRST`: First name
- `LAST`: Last name
- `SUFFIX`: Name suffix
- `MAIDEN`: Maiden name (if applicable)
- `MARITAL`: Marital status
- `RACE`: Racial category
- `ETHNICITY`: Ethnic background
- `GENDER`: Biological sex (F/M)
- `BIRTHPLACE`: Place of birth
- `ADDRESS`: Current street address
- `CITY`: City of residence
- `STATE`: State of residence
- `COUNTY`: County of residence
- `ZIP`: Postal code
- `LAT`: Latitude coordinate
- `LON`: Longitude coordinate
- `HEALTHCARE_EXPENSES`: Total healthcare expenses incurred
- `HEALTHCARE_COVERAGE`: Total insurance coverage amount

**Demographics:**
- **Gender Distribution:** 52.01% Female, 47.99% Male
- **Race Distribution:** 82.41% White, 8.63% Black, 7.69% Asian, 1.11% Native, 0.17% Other
- **Ethnicity:** 90.35% Non-Hispanic, 9.65% Hispanic
- **Age Statistics:**
  - Mean Age: 50.0 years
  - Median Age: 49.0 years
  - Age Range: 5 to 116 years
- **Vital Status:** 85.40% Living, 14.60% Deceased

**Financial Summary:**
- Total Healthcare Expenses: $895,745,796.37
- Average per Patient: $764,940.90
- Total Coverage: $15,144,235.59
- Average Coverage per Patient: $12,932.74

---

### 2. ENCOUNTERS (encounters.csv)
**Records of patient visits and medical encounters.**

- **Records:** 53,346
- **Columns:** 15
- **Size:** 39.84 MB
- **Missing Values:** 9.89%

**Key Fields:**
- `Id` (Primary Key): Unique encounter identifier
- `START`: Encounter start date/time
- `STOP`: Encounter end date/time
- `PATIENT` (Foreign Key): References patients.Id
- `ORGANIZATION` (Foreign Key): Healthcare organization providing care
- `PROVIDER` (Foreign Key): Healthcare provider
- `PAYER` (Foreign Key): Insurance payer
- `ENCOUNTERCLASS`: Type of encounter (inpatient, outpatient, emergency, etc.)
- `CODE`: Medical code for encounter type
- `DESCRIPTION`: Human-readable encounter description
- `BASE_ENCOUNTER_COST`: Base cost of encounter
- `TOTAL_CLAIM_COST`: Total claim amount
- `PAYER_COVERAGE`: Amount covered by insurance
- `REASONCODE`: Medical code for reason of visit
- `REASONDESCRIPTION`: Description of visit reason

**Relationship to Patients:**
- Foreign key `PATIENT` references `patients.Id`
- One-to-many relationship: One patient can have multiple encounters
- All 1,171 unique patient IDs in encounters match the patients table (100% referential integrity)
- Average 45.6 encounters per patient indicates longitudinal data collection

---

### 3. OBSERVATIONS (observations.csv)
**Clinical measurements and observations recorded during patient care.**

- **Records:** 299,697
- **Columns:** 8
- **Size:** 150.15 MB
- **Missing Values:** 1.80%

**Key Fields:**
- `DATE`: Date of observation
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Medical code for observation type
- `DESCRIPTION`: Description of observation
- `VALUE`: Measured value
- `UNITS`: Unit of measurement
- `TYPE`: Type of observation

**Statistics:**
- Average 255.9 observations per patient
- All 1,171 patients have at least one observation

**Most Frequent Observations:**
1. Pain severity (0-10 verbal numeric rating): 16,820 records
2. Systolic Blood Pressure: 12,963 records
3. Diastolic Blood Pressure: 12,963 records
4. Body Height: 12,552 records
5. Body Weight: 12,552 records
6. Respiratory rate: 12,552 records
7. Heart rate: 12,552 records
8. Tobacco smoking status NHIS: 12,552 records
9. Body Mass Index: 11,451 records
10. QOLS (Quality of Life Score): 10,121 records

---

### 4. MEDICATIONS (medications.csv)
**Prescription medication records.**

- **Records:** 42,989
- **Columns:** 13
- **Size:** 24.42 MB
- **Missing Values:** 4.32%

**Key Fields:**
- `START`: Medication start date
- `STOP`: Medication stop date
- `PATIENT` (Foreign Key): References patients.Id
- `PAYER` (Foreign Key): Insurance payer
- `ENCOUNTER` (Foreign Key): Encounter when prescribed
- `CODE`: Medication code
- `DESCRIPTION`: Medication name and dosage
- `BASE_COST`: Base medication cost
- `PAYER_COVERAGE`: Insurance coverage amount
- `DISPENSES`: Number of dispenses
- `TOTALCOST`: Total medication cost
- `REASONCODE`: Medical code for prescription reason
- `REASONDESCRIPTION`: Reason for prescription

**Statistics:**
- 1,107 patients have medication records (94.5% of total patients)
- Total medication costs: $13,775,459.68
- Average cost per prescription: $320.44

**Most Prescribed Medications:**
1. Hydrochlorothiazide 25 MG Oral Tablet: 3,954 prescriptions
2. Insulin human isophane 70 UNT/ML / Regular Insulin Human 30 UNT/ML Injectable Suspension (Humulin): 3,880
3. 1 ML Epoetin Alfa 4000 UNT/ML Injection (Epogen): 3,388
4. Atenolol 50 MG / Chlorthalidone 25 MG Oral Tablet: 3,347
5. 24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet: 2,895
6. amLODIPine 5 MG / Hydrochlorothiazide 12.5 MG / Olmesartan medoxomil 20 MG Oral Tablet: 2,867
7. Simvastatin 10 MG Oral Tablet: 2,273
8. NDA020503 200 ACTUAT Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler: 2,072
9. 120 ACTUAT Fluticasone propionate 0.044 MG/ACTUAT Metered Dose Inhaler: 2,072
10. Hydrochlorothiazide 12.5 MG: 1,598

---

### 5. PROCEDURES (procedures.csv)
**Medical procedures performed on patients.**

- **Records:** 34,981
- **Columns:** 8
- **Size:** 13.21 MB
- **Missing Values:** 11.11%

**Key Fields:**
- `DATE`: Procedure date
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Procedure code
- `DESCRIPTION`: Procedure description
- `BASE_COST`: Base procedure cost
- `REASONCODE`: Medical code for procedure reason
- `REASONDESCRIPTION`: Reason for procedure

**Statistics:**
- 1,165 patients have procedure records (99.5% of total patients)

**Most Common Procedures:**
1. Medication Reconciliation (procedure): 5,632 occurrences
2. Renal dialysis (procedure): 3,389 occurrences
3. Auscultation of the fetal heart: 2,705 occurrences
4. Evaluation of uterine fundal height: 2,705 occurrences
5. Subcutaneous immunotherapy: 1,497 occurrences
6. Intramuscular injection: 1,324 occurrences
7. Electrical cardioversion: 981 occurrences
8. Combined chemotherapy and radiation therapy (procedure): 655 occurrences
9. Hemoglobin / Hematocrit / Platelet count: 602 occurrences
10. Colonoscopy: 527 occurrences

---

### 6. CONDITIONS (conditions.csv)
**Patient diagnoses and medical conditions.**

- **Records:** 8,376
- **Columns:** 6
- **Size:** 2.86 MB
- **Missing Values:** 7.58%

**Key Fields:**
- `START`: Condition onset date
- `STOP`: Condition resolution date (if applicable)
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): Encounter when diagnosed
- `CODE`: Condition code
- `DESCRIPTION`: Condition description

**Statistics:**
- 1,152 patients have condition records (98.4% of total patients)

**Most Common Conditions:**
1. Viral sinusitis (disorder): 1,248 cases
2. Acute viral pharyngitis (disorder): 653 cases
3. Acute bronchitis (disorder): 563 cases
4. Normal pregnancy: 516 cases
5. Body mass index 30+ - obesity (finding): 449 cases
6. Prediabetes: 317 cases
7. Hypertension: 302 cases
8. Anemia (disorder): 300 cases
9. Chronic sinusitis (disorder): 236 cases
10. Miscarriage in first trimester: 221 cases

---

### 7. IMMUNIZATIONS (immunizations.csv)
**Vaccination records.**

- **Records:** 15,478
- **Columns:** 6
- **Size:** 5.03 MB
- **Missing Values:** 0%

**Key Fields:**
- `DATE`: Immunization date
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Vaccine code
- `DESCRIPTION`: Vaccine description
- `BASE_COST`: Cost of immunization

---

### 8. ALLERGIES (allergies.csv)
**Patient allergy records.**

- **Records:** 597
- **Columns:** 6
- **Size:** 0.19 MB
- **Missing Values:** 14.88%

**Key Fields:**
- `START`: Allergy identification date
- `STOP`: Allergy resolution date (if applicable)
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Allergy code
- `DESCRIPTION`: Allergy description

---

### 9. CAREPLANS (careplans.csv)
**Care plan records for patient treatment.**

- **Records:** 3,483
- **Columns:** 9
- **Size:** 1.72 MB
- **Missing Values:** 6.97%

**Key Fields:**
- `Id` (Primary Key): Unique care plan identifier
- `START`: Care plan start date
- `STOP`: Care plan end date
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Care plan code
- `DESCRIPTION`: Care plan description
- `REASONCODE`: Medical code for care plan reason
- `REASONDESCRIPTION`: Reason for care plan

---

### 10. IMAGING_STUDIES (imaging_studies.csv)
**Medical imaging study records.**

- **Records:** 855
- **Columns:** 10
- **Size:** 0.56 MB
- **Missing Values:** 0%

**Key Fields:**
- `Id` (Primary Key): Unique imaging study identifier
- `DATE`: Study date
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `BODYSITE_CODE`: Body site code
- `BODYSITE_DESCRIPTION`: Body site description
- `MODALITY_CODE`: Imaging modality code
- `MODALITY_DESCRIPTION`: Imaging modality description
- `SOP_CODE`: Standard operating procedure code
- `SOP_DESCRIPTION`: SOP description

---

### 11. ORGANIZATIONS (organizations.csv)
**Healthcare organizations and facilities.**

- **Records:** 1,119
- **Columns:** 11
- **Size:** 0.50 MB
- **Missing Values:** 1.49%

**Key Fields:**
- `Id` (Primary Key): Unique organization identifier
- `NAME`: Organization name
- `ADDRESS`: Street address
- `CITY`: City
- `STATE`: State
- `ZIP`: Postal code
- `LAT`: Latitude
- `LON`: Longitude
- `PHONE`: Contact phone number
- `REVENUE`: Organization revenue
- `UTILIZATION`: Utilization metrics

---

### 12. PROVIDERS (providers.csv)
**Healthcare providers (physicians, nurses, specialists).**

- **Records:** 5,855
- **Columns:** 12
- **Size:** 3.41 MB
- **Missing Values:** 0%

**Key Fields:**
- `Id` (Primary Key): Unique provider identifier
- `ORGANIZATION` (Foreign Key): References organizations.Id
- `NAME`: Provider name
- `GENDER`: Provider gender
- `SPECIALITY`: Medical specialty
- `ADDRESS`: Street address
- `CITY`: City
- `STATE`: State
- `ZIP`: Postal code
- `LAT`: Latitude
- `LON`: Longitude
- `UTILIZATION`: Utilization metrics

**Provider Specialties (Top 10):**
1. General Practice: 1,120 providers
2. Internal Medicine: 608 providers
3. Nurse Practitioner: 511 providers
4. Clinical Social Worker: 367 providers
5. Physician Assistant: 311 providers
6. Physical Therapy: 308 providers
7. Family Practice: 279 providers
8. Clinical Psychologist: 204 providers
9. Diagnostic Radiology: 171 providers
10. Chiropractic: 148 providers

---

### 13. PAYERS (payers.csv)
**Insurance payers and coverage providers.**

- **Records:** 10
- **Columns:** 21
- **Size:** 0.00 MB
- **Missing Values:** 2.38%

**Key Fields:**
- `Id` (Primary Key): Unique payer identifier
- `NAME`: Payer name
- `ADDRESS`: Street address
- `CITY`: City
- `STATE_HEADQUARTERED`: State where headquartered
- `ZIP`: Postal code
- `PHONE`: Contact phone
- `AMOUNT_COVERED`: Total amount covered
- `AMOUNT_UNCOVERED`: Total amount not covered
- `REVENUE`: Payer revenue
- `COVERED_ENCOUNTERS`: Number of covered encounters
- `UNCOVERED_ENCOUNTERS`: Number of uncovered encounters
- `COVERED_MEDICATIONS`: Number of covered medications
- `UNCOVERED_MEDICATIONS`: Number of uncovered medications
- `COVERED_PROCEDURES`: Number of covered procedures
- Plus additional coverage metrics

---

### 14. PAYER_TRANSITIONS (payer_transitions.csv)
**Insurance payer transition history.**

- **Records:** 3,801
- **Columns:** 5
- **Size:** 0.87 MB
- **Missing Values:** 1.24%

**Key Fields:**
- `PATIENT` (Foreign Key): References patients.Id
- `START_YEAR`: Transition start year
- `END_YEAR`: Transition end year
- `PAYER` (Foreign Key): References payers.Id
- `OWNERSHIP`: Ownership type

---

### 15. DEVICES (devices.csv)
**Medical devices used in patient care.**

- **Records:** 78
- **Columns:** 7
- **Size:** 0.04 MB
- **Missing Values:** 14.29%

**Key Fields:**
- `START`: Device usage start date
- `STOP`: Device usage stop date
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Device code
- `DESCRIPTION`: Device description
- `UDI`: Unique Device Identifier

---

### 16. SUPPLIES (supplies.csv)
**Medical supplies used in patient care.**

- **Records:** 0 (Empty table)
- **Columns:** 6
- **Size:** 0.00 MB

**Key Fields:**
- `DATE`: Supply usage date
- `PATIENT` (Foreign Key): References patients.Id
- `ENCOUNTER` (Foreign Key): References encounters.Id
- `CODE`: Supply code
- `DESCRIPTION`: Supply description
- `QUANTITY`: Quantity used

**Note:** This table contains no data in the current dataset.

---

## Data Relationships and Schema

### Primary Key and Foreign Key Relationships

The dataset follows a star schema with the `PATIENTS` table at the center. The primary relationship pattern is:

```
PATIENTS.Id (Primary Key)
    |
    +-- ENCOUNTERS.PATIENT (Foreign Key) [1 to many]
    +-- OBSERVATIONS.PATIENT (Foreign Key) [1 to many]
    +-- MEDICATIONS.PATIENT (Foreign Key) [1 to many]
    +-- PROCEDURES.PATIENT (Foreign Key) [1 to many]
    +-- CONDITIONS.PATIENT (Foreign Key) [1 to many]
    +-- IMMUNIZATIONS.PATIENT (Foreign Key) [1 to many]
    +-- ALLERGIES.PATIENT (Foreign Key) [1 to many]
    +-- CAREPLANS.PATIENT (Foreign Key) [1 to many]
    +-- IMAGING_STUDIES.PATIENT (Foreign Key) [1 to many]
    +-- PAYER_TRANSITIONS.PATIENT (Foreign Key) [1 to many]
    +-- DEVICES.PATIENT (Foreign Key) [1 to many]
```

### Important Distinction: Id vs PATIENT Fields

**This is a critical concept for understanding the dataset structure:**

- **`Id` field** (in PATIENTS table): 
  - This is the PRIMARY KEY
  - Uniquely identifies each individual patient
  - Each patient has exactly one unique Id value
  - Total unique values: 1,171
  
- **`PATIENT` field** (in all other tables):
  - This is a FOREIGN KEY
  - References the Id field in the PATIENTS table
  - Indicates which patient the record belongs to
  - A single PATIENT value can appear many times (one patient, many visits)
  - Example: 53,346 encounter records reference only 1,171 unique patients

**Relationship Type:** One-to-Many
- One patient (1 Id in PATIENTS) maps to many encounters (many PATIENT values in ENCOUNTERS)
- Average ratio: 45.6 encounters per patient
- This pattern repeats across all clinical tables

### Referential Integrity

All foreign key relationships have been verified:
- 100% of PATIENT values in ENCOUNTERS exist in PATIENTS.Id
- 100% of PATIENT values in all other tables exist in PATIENTS.Id
- No orphaned records
- No invalid references

### Secondary Relationships

- `ENCOUNTERS.ORGANIZATION` references `ORGANIZATIONS.Id`
- `ENCOUNTERS.PROVIDER` references `PROVIDERS.Id`
- `ENCOUNTERS.PAYER` references `PAYERS.Id`
- `PROVIDERS.ORGANIZATION` references `ORGANIZATIONS.Id`
- `PAYER_TRANSITIONS.PAYER` references `PAYERS.Id`

---

## Data Collection Period

Based on patient birth dates and death dates:
- Earliest birth date in dataset: 1913
- Latest birth date in dataset: 2020
- Dataset includes patients spanning over 100 years
- Active encounter data suggests longitudinal tracking over extended periods
- Average 45.6 encounters per patient indicates long-term follow-up

---

## Geographic Distribution

All patients are located in Massachusetts, United States:
- Multiple cities represented
- County-level geographic data available
- Latitude/longitude coordinates provided for spatial analysis
- Coverage across urban and rural areas

---

## Data Usage Considerations

### Strengths
1. **Comprehensive Coverage:** Captures multiple aspects of patient care
2. **Longitudinal Data:** Long-term patient follow-up (45+ encounters per patient on average)
3. **High Quality:** Low missing data rates, verified referential integrity
4. **Rich Clinical Detail:** Detailed observations, medications, procedures, and diagnoses
5. **Structured Format:** Clean CSV format with consistent naming conventions

### Limitations
1. **Geographic Scope:** Limited to Massachusetts; may not generalize to other regions
2. **Sample Size:** 1,171 patients may be limited for some analyses
3. **Race/Ethnicity Representation:** 82% white population; limited diversity
4. **Empty Tables:** SUPPLIES table contains no data
5. **Missing Data:** Some fields have up to 15% missing values
6. **Synthetic Nature:** Data appears to be synthetically generated (perfect UUID formats, clean relationships)

### Recommended Use Cases
- Healthcare cost analysis
- Treatment pathway analysis
- Medication adherence studies
- Chronic disease management research
- Healthcare utilization patterns
- Longitudinal patient outcome studies
- Provider and organization performance analysis

### Privacy and Ethics
- Data contains identifiable information (names, SSN, addresses)
- Appropriate de-identification should be applied before sharing
- Follow HIPAA guidelines if using for research
- Consider re-identification risks with geographic coordinates and detailed demographics

---

## File Format Specifications

**Format:** CSV (Comma-Separated Values)
**Encoding:** UTF-8
**Line Terminator:** CRLF (Windows style)
**Date Format:** YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
**Missing Values:** Represented as empty strings or NULL
**UUID Format:** Standard 8-4-4-4-12 format (e.g., "1d604da9-9a81-4ba9-80c2-de3375d59b40")

---

## Loading the Data

The dataset includes Python loader scripts in the `loaders/` directory that demonstrate how to:
1. Load CSV files into pandas DataFrames
2. Handle missing values appropriately
3. Establish relationships between tables
4. Insert data into a TigerGraph database

Example loader scripts include:
- `loadPatients.py`: Loads patient demographic data
- `loadVisits.py`: Loads encounter/visit data
- `loadObservations.py`: Loads clinical observations
- `loadMedications.py`: Loads medication prescriptions
- And others for each table

---

## Contact and Support

For questions about this dataset or to report data quality issues, please refer to the project documentation or contact the data administrator.

---

**Document Version History:**
- Version 1.0 (February 8, 2026): Initial comprehensive dataset description
