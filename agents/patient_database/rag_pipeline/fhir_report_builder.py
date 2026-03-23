"""
fhir_report_builder.py

Parses a FHIR R4 Bundle JSON file and generates a comprehensive,
structured plain-text medical record report for display to patients.

Does NOT use RAG or LLM - all data is extracted directly from the bundle.
"""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .parser import FHIRBundleParser


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _code_display(code_block: Any) -> Optional[str]:
    """Extract human-readable display text from a FHIR CodeableConcept."""
    if not code_block:
        return None
    if isinstance(code_block, list):
        code_block = code_block[0]
    coding = code_block.get("coding")
    if coding and isinstance(coding, list):
        return coding[0].get("display") or code_block.get("text")
    return code_block.get("text")


def _fmt_date(iso_str: Optional[str]) -> str:
    """Format ISO-8601 date string -> DD/MM/YYYY."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", ""))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return iso_str[:10] if len(iso_str) >= 10 else iso_str


def _name_str(name_list: List[Dict]) -> str:
    """Build full name from FHIR HumanName list."""
    if not name_list:
        return "Unknown"
    n = name_list[0]
    prefix = " ".join(n.get("prefix", []))
    given  = " ".join(n.get("given",  []))
    family = n.get("family", "")
    return " ".join(p for p in [prefix, given, family] if p).strip()


def _divider(char: str = "─", width: int = 55) -> str:
    return char * width


# ---------------------------------------------------------------------------
# FHIRReportBuilder
# ---------------------------------------------------------------------------

class FHIRReportBuilder:
    """
    Builds a structured, human-readable medical report from a FHIR Bundle.

    Usage:
        builder = FHIRReportBuilder("/path/to/patient.json")
        result  = builder.build_report()
        # result["report_text"] -> full formatted string
        # result["sections"]    -> dict of section_key -> section_text
        # result["patient_name"]
    """

    def __init__(self, bundle_path: str):
        self.bundle_path = bundle_path
        self._resources: Dict[str, Dict] = {}  # resourceType -> {id -> resource}

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def build_report(self) -> Dict[str, Any]:
        parser = FHIRBundleParser(self.bundle_path)
        parsed = parser.parse()
        self._resources = parsed["by_type"]

        patient    = self._get_patient()
        pat_name   = _name_str(patient.get("name", [])) if patient else "Unknown"
        pat_id_val = self._get_patient_external_id(patient)

        sections: Dict[str, str] = {
            "demographics":  self._section_demographics(patient),
            "conditions":    self._section_conditions(),
            "encounters":    self._section_encounters(),
            "medications":   self._section_medications(),
            "vitals":        self._section_vitals(),
            "immunizations": self._section_immunizations(),
            "devices":       self._section_devices(),
            "billing":       self._section_billing(patient),
        }

        header = self._build_header(pat_name, pat_id_val)
        report_text = header + "\n\n" + "\n\n".join(
            text for text in sections.values() if text
        )

        return {
            "patient_name": pat_name,
            "report_text":  report_text,
            "sections":     sections,
        }

    # ------------------------------------------------------------------
    # header
    # ------------------------------------------------------------------

    def _build_header(self, name: str, pid: str) -> str:
        today = datetime.now().strftime("%d/%m/%Y %H:%M")
        line = "═" * 57
        return (
            f"{line}\n"
            f"  PATIENT MEDICAL RECORD — {name.upper()}\n"
            f"  Patient ID : {pid}\n"
            f"  Generated  : {today}\n"
            f"{line}"
        )

    # ------------------------------------------------------------------
    # section builders
    # ------------------------------------------------------------------

    def _section_demographics(self, patient: Optional[Dict]) -> str:
        if not patient:
            return ""

        lines = ["📋  I. PERSONAL INFORMATION", _divider()]

        # Name
        lines.append(f"  Full Name     : {_name_str(patient.get('name', []))}")

        # Birth date
        lines.append(f"  Date of Birth : {_fmt_date(patient.get('birthDate'))}")

        # Gender
        gender_map = {"male": "Male", "female": "Female", "other": "Other", "unknown": "Unknown"}
        lines.append(f"  Gender        : {gender_map.get(patient.get('gender', ''), 'N/A')}")

        # Address
        addresses = patient.get("address", [])
        if addresses:
            a = addresses[0]
            line_parts = a.get("line", [])
            city    = a.get("city", "")
            state   = a.get("state", "")
            country = a.get("country", "")
            addr_str = ", ".join(p for p in [", ".join(line_parts), city, state, country] if p)
            lines.append(f"  Address       : {addr_str}")

        # Phone
        telecoms = patient.get("telecom", [])
        for t in telecoms:
            if t.get("system") == "phone":
                lines.append(f"  Phone         : {t.get('value', 'N/A')}")
                break

        # Language
        comms = patient.get("communication", [])
        if comms:
            lang = _code_display(comms[0].get("language")) or "N/A"
            lines.append(f"  Language      : {lang}")

        # Marital status
        marital = patient.get("maritalStatus", {})
        if marital:
            m_text = marital.get("text") or _code_display(marital) or "N/A"
            lines.append(f"  Marital Status: {m_text}")

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _section_conditions(self) -> str:
        conditions = list(self._resources.get("Condition", {}).values())
        lines = ["🩺  II. DIAGNOSES / CONDITIONS", _divider()]

        if not conditions:
            lines.append("  No conditions recorded.")
            return "\n".join(lines)

        # Sort by onset date (oldest first)
        def onset_key(c):
            return c.get("onsetDateTime") or c.get("recordedDate") or ""

        active, resolved, other = [], [], []
        for c in sorted(conditions, key=onset_key):
            status = ""
            cs = c.get("clinicalStatus", {}).get("coding", [])
            if cs:
                status = cs[0].get("code", "")
            name = _code_display(c.get("code")) or "Unknown condition"
            date = _fmt_date(c.get("onsetDateTime") or c.get("recordedDate"))

            entry = f"  • {name:<50} [{status}]  ({date})"
            if status == "active":
                active.append(entry)
            elif status in ("resolved", "inactive", "remission"):
                resolved.append(entry)
            else:
                other.append(entry)

        if active:
            lines.append("  ── Active ──")
            lines.extend(active)
        if resolved:
            lines.append("  ── Resolved ──")
            lines.extend(resolved)
        if other:
            lines.extend(other)

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _section_encounters(self) -> str:
        encounters = list(self._resources.get("Encounter", {}).values())
        lines = ["📅  III. ENCOUNTER HISTORY", _divider()]

        if not encounters:
            lines.append("  No encounters recorded.")
            return "\n".join(lines)

        # Sort newest first
        def enc_date(e):
            return e.get("period", {}).get("start") or ""

        for enc in sorted(encounters, key=enc_date, reverse=True):
            date      = _fmt_date(enc.get("period", {}).get("start"))
            enc_type  = _code_display(enc.get("type")) or "General Visit"
            enc_class = enc.get("class", {}).get("code", "")

            # Provider
            provider  = enc.get("serviceProvider", {}).get("display", "")

            # Practitioner
            participants = enc.get("participant", [])
            doctor = ""
            if participants:
                doctor = participants[0].get("individual", {}).get("display", "")

            class_tag = f"[{enc_class.upper()}]" if enc_class else ""
            lines.append(f"  {date}  {enc_type}")
            if doctor:
                lines.append(f"            Physician : {doctor}")
            if provider:
                lines.append(f"            Facility  : {provider}")
            if class_tag:
                lines.append(f"            Class     : {class_tag}")
            lines.append("")  # blank line between entries

        return "\n".join(lines).rstrip()

    # ------------------------------------------------------------------

    def _section_medications(self) -> str:
        meds = list(self._resources.get("MedicationRequest", {}).values())
        lines = ["💊  IV. MEDICATIONS", _divider()]

        if not meds:
            lines.append("  No medications recorded.")
            return "\n".join(lines)

        active_meds, other_meds = [], []
        for med in meds:
            name = _code_display(med.get("medicationCodeableConcept")) or "Unknown medication"
            status = med.get("status", "")
            date   = _fmt_date(med.get("authoredOn"))
            entry  = f"  • {name:<55} ({date})"
            if status == "active":
                active_meds.append(entry)
            else:
                other_meds.append(f"  • {name:<55} ({date}) [{status}]")

        if active_meds:
            lines.append("  ── Active ──")
            lines.extend(active_meds)
        if other_meds:
            lines.append("  ── Stopped / Other ──")
            lines.extend(other_meds)

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _section_vitals(self) -> str:
        observations = list(self._resources.get("Observation", {}).values())
        lines = ["📊  V. LATEST VITAL SIGNS & OBSERVATIONS", _divider()]

        if not observations:
            lines.append("  No observations recorded.")
            return "\n".join(lines)

        # Group by observation name, keep only the most recent
        latest: Dict[str, Dict] = {}
        for obs in observations:
            name = _code_display(obs.get("code")) or "Unknown"
            date = obs.get("effectiveDateTime") or obs.get("issued") or ""
            existing = latest.get(name)
            if existing is None or date > (
                existing.get("effectiveDateTime") or existing.get("issued") or ""
            ):
                latest[name] = obs

        for name, obs in sorted(latest.items()):
            date  = _fmt_date(obs.get("effectiveDateTime") or obs.get("issued"))
            value = self._extract_obs_value(obs)
            lines.append(f"  • {name:<45} {value:<20} ({date})")

        return "\n".join(lines)

    def _extract_obs_value(self, obs: Dict) -> str:
        # Simple quantity
        vq = obs.get("valueQuantity")
        if vq:
            val  = vq.get("value")
            unit = vq.get("unit", "")
            return f"{round(val, 1)} {unit}" if val is not None else "N/A"

        # CodeableConcept value (e.g. smoking status)
        vc = obs.get("valueCodeableConcept")
        if vc:
            return _code_display(vc) or "N/A"

        # String value
        vs = obs.get("valueString")
        if vs:
            return vs

        # Blood pressure (component-based)
        components = obs.get("component")
        if components:
            parts = []
            for comp in components:
                cname = _code_display(comp.get("code")) or ""
                cval  = comp.get("valueQuantity", {})
                cv    = cval.get("value")
                cu    = cval.get("unit", "")
                if cv is not None:
                    parts.append(f"{round(cv, 0):.0f} {cu}")
            return " / ".join(parts) if parts else "N/A"

        return "N/A"

    # ------------------------------------------------------------------

    def _section_immunizations(self) -> str:
        immunizations = list(self._resources.get("Immunization", {}).values())
        lines = ["💉  VI. IMMUNIZATIONS", _divider()]

        if not immunizations:
            lines.append("  No immunizations recorded.")
            return "\n".join(lines)

        def imm_date(i):
            return i.get("occurrenceDateTime") or ""

        for imm in sorted(immunizations, key=imm_date, reverse=True):
            vaccine = _code_display(imm.get("vaccineCode")) or "Unknown vaccine"
            date    = _fmt_date(imm.get("occurrenceDateTime"))
            status  = imm.get("status", "")
            lines.append(f"  • {vaccine:<55} ({date})")

        return "\n".join(lines)

    # ------------------------------------------------------------------

    def _section_devices(self) -> str:
        devices = list(self._resources.get("Device", {}).values())
        lines = ["🔧  VII. IMPLANTED DEVICES", _divider()]

        if not devices:
            lines.append("  No devices recorded.")
            return "\n".join(lines)

        for dev in devices:
            name_list = dev.get("deviceName", [])
            name      = name_list[0].get("name") if name_list else (
                _code_display(dev.get("type")) or "Unknown device"
            )
            serial    = dev.get("serialNumber", "N/A")
            mfg_date  = _fmt_date(dev.get("manufactureDate"))
            status    = dev.get("status", "")
            lines.append(f"  • {name}")
            lines.append(f"    Serial: {serial}  |  Date: {mfg_date}  |  Status: {status}")
            lines.append("")

        return "\n".join(lines).rstrip()

    # ------------------------------------------------------------------

    def _section_billing(self, patient: Optional[Dict]) -> str:
        claims = list(self._resources.get("Claim", {}).values())
        lines  = ["🏥  VIII. INSURANCE & BILLING SUMMARY", _divider()]

        # Detect insurers
        insurers = set()
        total_cost = 0.0
        for claim in claims:
            for ins in claim.get("insurance", []):
                cov = ins.get("coverage", {})
                display = cov.get("display")
                if display:
                    insurers.add(display)
            total = claim.get("total")
            if total and isinstance(total, dict):
                total_cost += total.get("value", 0.0)

        insurer_str = ", ".join(sorted(insurers)) if insurers else "Not recorded"
        lines.append(f"  Insurance    : {insurer_str}")
        lines.append(f"  Total Claims : ${total_cost:,.2f} USD")
        lines.append(f"  Visit Count  : {len(claims)} claim(s)")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # utilities
    # ------------------------------------------------------------------

    def _get_patient(self) -> Optional[Dict]:
        patients = self._resources.get("Patient", {})
        if not patients:
            return None
        return next(iter(patients.values()))

    def _get_patient_external_id(self, patient: Optional[Dict]) -> str:
        if not patient:
            return "N/A"
        for ident in patient.get("identifier", []):
            system = ident.get("system", "")
            if "synthea" in system or "smart" in system:
                return ident.get("value", "N/A")
        return patient.get("id", "N/A")
