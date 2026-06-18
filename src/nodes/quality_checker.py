from src.brand_knowledge import build_brand_quality_targets
from src.reference_styles import build_reference_profiles, score_style_map_against_references
from src.state import PresFactoryState


def check_quality(state: PresFactoryState) -> dict:
    style_map = state.get("style_map", [])
    file_type = state["file_type"]
    similar_examples = state.get("similar_examples", [])
    raw_elements = state.get("raw_elements", [])

    reference_profiles = build_reference_profiles(similar_examples, file_type)
    brand_targets = build_brand_quality_targets(file_type)
    report = score_style_map_against_references(
        style_map=style_map,
        raw_elements=raw_elements,
        file_type=file_type,
        reference_profiles=reference_profiles,
        brand_targets=brand_targets,
    )

    return {
        "quality_score": float(report.get("score", 0)),
        "quality_report": report,
    }
