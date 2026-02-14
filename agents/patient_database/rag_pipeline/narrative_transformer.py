from typing import Dict, Any, List
from datetime import datetime


class EpisodeNarrativeTransformer:
    def __init__(self):
        pass

    def transform(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        lines = []

        encounter_date = self._format_date(episode.get("date"))
        encounter_type = episode.get("type")

        lines.append(f"Encounter Date: {encounter_date}")
        if encounter_type:
            lines.append(f"Encounter Type: {encounter_type}")

        # ----------------------
        # CONDITIONS
        # ----------------------
        if episode["conditions"]:
            lines.append("\nDiagnoses:")
            for cond in episode["conditions"]:
                name = self._extract_code_display(cond.get("code"))
                status = self._extract_status(cond)
                lines.append(f"- {name} ({status})")

        # ----------------------
        # VITALS & OBSERVATIONS
        # ----------------------
        vitals_lines = self._extract_vitals(episode["observations"])
        if vitals_lines:
            lines.append("\nVitals and Observations:")
            lines.extend(vitals_lines)

        # ----------------------
        # MEDICATIONS
        # ----------------------
        if episode["medications"]:
            lines.append("\nMedications:")
            for med in episode["medications"]:
                med_name = self._extract_code_display(
                    med.get("medicationCodeableConcept")
                )
                lines.append(f"- {med_name}")

        # ----------------------
        # IMMUNIZATIONS
        # ----------------------
        if episode["immunizations"]:
            lines.append("\nImmunizations:")
            for imm in episode["immunizations"]:
                vaccine = self._extract_code_display(imm.get("vaccineCode"))
                lines.append(f"- {vaccine}")

        # ----------------------
        # CLAIM TOTAL
        # ----------------------
        total_cost = self._extract_claim_total(episode["claims"])
        if total_cost:
            lines.append(f"\nTotal Claim Amount: {total_cost}")

        text = "\n".join(lines)

        return {
            "text": text,
            "metadata": {
                "encounter_id": episode["encounter_id"],
                "year": encounter_date[:4] if encounter_date else None,
                "resource_type": "Encounter"
            }
        }

    
    # Helper methods
    

    def _format_date(self, date_str):
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", ""))
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str

    def _extract_code_display(self, code_block):
        if not code_block:
            return None

        coding = code_block.get("coding")
        if coding and isinstance(coding, list):
            return coding[0].get("display")

        return code_block.get("text")

    def _extract_status(self, condition):
        clinical = condition.get("clinicalStatus", {}).get("coding", [])
        if clinical:
            return clinical[0].get("code")
        return "unknown"

    def _extract_vitals(self, observations: List[Dict[str, Any]]):
        lines = []

        for obs in observations:
            code_display = self._extract_code_display(obs.get("code"))

            # Simple quantity
            value_quantity = obs.get("valueQuantity")
            if value_quantity:
                val = round(value_quantity.get("value", 0), 2)
                unit = value_quantity.get("unit")
                lines.append(f"- {code_display}: {val} {unit}")
                continue

            # Blood pressure (component-based)
            components = obs.get("component")
            if components:
                systolic = None
                diastolic = None

                for comp in components:
                    comp_name = self._extract_code_display(comp.get("code"))
                    val = comp.get("valueQuantity", {}).get("value")

                    if "Systolic" in comp_name:
                        systolic = round(val, 2)
                    elif "Diastolic" in comp_name:
                        diastolic = round(val, 2)

                if systolic and diastolic:
                    lines.append(
                        f"- Blood Pressure: {systolic}/{diastolic} mmHg"
                    )

            # CodeableConcept (e.g., Smoking Status)
            value_concept = obs.get("valueCodeableConcept")
            if value_concept:
                concept_display = self._extract_code_display(value_concept)
                lines.append(f"- {code_display}: {concept_display}")

        return lines

    def _extract_claim_total(self, claims):
        for claim in claims:
            total = claim.get("total")
            if total:
                value = total.get("value")
                currency = total.get("currency")
                return f"{value} {currency}"
        return None