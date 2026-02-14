from typing import List, Dict, Any
from collections import defaultdict


class EncounterEpisodeBuilder:
    def __init__(self, parsed_data: Dict[str, Any]):
        self.resources_by_type = parsed_data["by_type"]
        self.resources_by_id = parsed_data["by_id"]

    def extract_reference_id(self, ref_obj):
        if not ref_obj:
            return None

        ref = ref_obj.get("reference")
        if not ref:
            return None

        if ref.startswith("urn:uuid:"):
            return ref.replace("urn:uuid:", "")

        if "/" in ref:
            return ref.split("/")[-1]

        return None

    def build(self) -> List[Dict[str, Any]]:
        episodes = []

        encounters = self.resources_by_type.get("Encounter", {})

        for encounter_id, encounter in encounters.items():
            episode = {
                "encounter_id": encounter_id,
                "date": encounter.get("period", {}).get("start"),
                "type": self._extract_code_display(encounter.get("type")),
                "patient": None,
                "conditions": [],
                "observations": [],
                "medications": [],
                "immunizations": [],
                "claims": []
            }

            # 1️. Patient
            patient_ref = encounter.get("subject")
            patient_id = self.extract_reference_id(patient_ref)
            if patient_id:
                episode["patient"] = self.resources_by_id.get(patient_id)

            # 2️. Condition
            for cond in self.resources_by_type.get("Condition", {}).values():
                enc_ref = cond.get("encounter")
                if self.extract_reference_id(enc_ref) == encounter_id:
                    episode["conditions"].append(cond)

            # 3️. Observation
            for obs in self.resources_by_type.get("Observation", {}).values():
                enc_ref = obs.get("encounter")
                if self.extract_reference_id(enc_ref) == encounter_id:
                    episode["observations"].append(obs)

            # 4️. MedicationRequest
            for med in self.resources_by_type.get("MedicationRequest", {}).values():
                enc_ref = med.get("encounter")
                if self.extract_reference_id(enc_ref) == encounter_id:
                    episode["medications"].append(med)

            # 5️. Immunization
            for imm in self.resources_by_type.get("Immunization", {}).values():
                enc_ref = imm.get("encounter")
                if self.extract_reference_id(enc_ref) == encounter_id:
                    episode["immunizations"].append(imm)

            # 6️. Claim (Can be more complex depending on bundle)
            for claim in self.resources_by_type.get("Claim", {}).values():
                # Some Claims reference encounter through item.detail or prescription
                # We just check direct encounter reference for simplicity
                enc_ref = claim.get("encounter")
                if enc_ref:
                    for ref in enc_ref:
                        if self.extract_reference_id(ref) == encounter_id:
                            episode["claims"].append(claim)

            episodes.append(episode)

        return episodes

    def _extract_code_display(self, code_block):
        if not code_block:
            return None

        if isinstance(code_block, list):
            code_block = code_block[0]

        coding = code_block.get("coding")
        if coding and isinstance(coding, list):
            return coding[0].get("display")

        return None