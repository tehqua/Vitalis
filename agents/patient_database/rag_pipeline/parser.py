import json
from collections import defaultdict
from typing import Dict, Any


class FHIRBundleParser:
    def __init__(self, bundle_path: str):
        self.bundle_path = bundle_path
        self.bundle = None
        
        # Indexed storage
        self.resources_by_type: Dict[str, Dict[str, dict]] = defaultdict(dict)
        self.resources_by_id: Dict[str, dict] = {}
        
        # Reference graph (to build later)
        self.reference_graph: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    def load_bundle(self):
        with open(self.bundle_path, "r", encoding="utf-8") as f:
            self.bundle = json.load(f)

        if self.bundle.get("resourceType") != "Bundle":
            raise ValueError("Provided file is not a FHIR Bundle")

    def index_resources(self):
        """
        Index resources by:
        - resourceType
        - resource.id
        """
        entries = self.bundle.get("entry", [])

        for entry in entries:
            resource = entry.get("resource")
            if not resource:
                continue

            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")

            if not resource_type or not resource_id:
                continue

            # Store by type
            self.resources_by_type[resource_type][resource_id] = resource

            # Store by id
            self.resources_by_id[resource_id] = resource

    def extract_reference(self, reference_obj: Dict[str, Any]):
        """
        Extract ID from reference string like:
        "urn:uuid:5c818f3d-7051-4b86-8203-1dc624a91804"
        """
        ref = reference_obj.get("reference")
        if not ref:
            return None

        if ref.startswith("urn:uuid:"):
            return ref.replace("urn:uuid:", "")

        # fallback: split by slash
        if "/" in ref:
            return ref.split("/")[-1]

        return None

    def build_reference_graph(self):
        """
        Build simple graph of references between resources
        """
        for resource_id, resource in self.resources_by_id.items():
            for key, value in resource.items():
                # Direct reference
                if isinstance(value, dict) and "reference" in value:
                    target_id = self.extract_reference(value)
                    if target_id:
                        self.reference_graph[resource_id][key].append(target_id)

                # List of references
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "reference" in item:
                            target_id = self.extract_reference(item)
                            if target_id:
                                self.reference_graph[resource_id][key].append(target_id)

    def parse(self):
        self.load_bundle()
        self.index_resources()
        self.build_reference_graph()

        return {
            "by_type": self.resources_by_type,
            "by_id": self.resources_by_id,
            "references": self.reference_graph
        }