from .parser import FHIRBundleParser
from .episode_builder import EncounterEpisodeBuilder
from .narrative_transformer import EpisodeNarrativeTransformer


def process_fhir_bundle(bundle_path: str):
    """
    Step 1 → Parse FHIR Bundle
    Step 2 → Build Encounter Episodes
    Step 3 → Transform to Narrative Documents

    Returns:
        List[Dict] with:
        {
            "encounter_id": str,
            "text": str,
            "metadata": {
                "patient_id": str,
                "year": str
            }
        }
    """

    # -------------------------
    # Step 1: Parse
    # -------------------------
    parser = FHIRBundleParser(bundle_path)
    parsed_data = parser.parse()

    # -------------------------
    # Step 2: Build Episodes
    # -------------------------
    builder = EncounterEpisodeBuilder(parsed_data)
    episodes = builder.build()

    # -------------------------
    # Step 3: Transform
    # -------------------------
    transformer = EpisodeNarrativeTransformer()

    documents = []
    for ep in episodes:
        doc = transformer.transform(ep)
        documents.append(doc)

    return documents