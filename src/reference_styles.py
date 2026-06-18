from collections import Counter
from typing import Any

from src.brand_knowledge import get_brand_placeholder_style


_ELEMENT_STYLE_FALLBACKS = {
    "docx": {
        "title": ["title", "heading_1", "heading_2", "body"],
        "heading": ["heading", "heading_1", "heading_2", "body"],
        "heading_1": ["heading_1", "heading_2", "body"],
        "heading_2": ["heading_2", "heading_1", "body"],
        "heading_3": ["heading_3", "heading_2", "body"],
        "subtitle": ["subtitle", "heading_2", "body"],
        "body": ["body", "heading_2"],
        "bullet": ["bullet", "body"],
        "bullet_level_1": ["bullet", "body"],
        "bullet_level_2": ["bullet", "body"],
        "caption": ["caption", "body"],
        "table": ["table", "body"],
    },
    "pptx": {
        "title": ["title", "heading", "subtitle", "body"],
        "subtitle": ["subtitle", "heading", "body"],
        "heading": ["heading", "title", "body"],
        "heading_1": ["heading", "title", "body"],
        "heading_2": ["heading", "subtitle", "body"],
        "heading_3": ["heading", "body"],
        "body": ["body", "heading"],
        "bullet": ["bullet_level_1", "body"],
        "bullet_level_1": ["bullet_level_1", "body"],
        "bullet_level_2": ["bullet_level_2", "bullet_level_1", "body"],
        "caption": ["caption", "body"],
        "table": ["body", "heading"],
    },
}

_TYPE_ALIASES = {
    "heading1": "heading_1",
    "heading2": "heading_2",
    "heading3": "heading_3",
    "bullet1": "bullet_level_1",
    "bullet2": "bullet_level_2",
    "bullet_1": "bullet_level_1",
    "bullet_2": "bullet_level_2",
    "bulletlevel1": "bullet_level_1",
    "bulletlevel2": "bullet_level_2",
    "paragraph": "body",
    "normal": "body",
    "text": "body",
}

_STYLE_FIELDS = (
    "font_name",
    "font_size",
    "bold",
    "italic",
    "color",
    "alignment",
    "space_before",
    "space_after",
)


def normalize_element_type(value: Any) -> str:
    if not isinstance(value, str):
        return "body"
    cleaned = "_".join(value.strip().lower().replace("-", "_").split())
    return _TYPE_ALIASES.get(cleaned, cleaned or "body")


def flatten_reference_exemplars(reference_examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exemplars: list[dict[str, Any]] = []
    for example in reference_examples or []:
        for exemplar in example.get("style_exemplars", []) or []:
            if isinstance(exemplar, dict):
                exemplars.append(exemplar)
    return exemplars


def _most_common(values: list[Any]) -> Any:
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _average_number(values: list[Any]) -> float | None:
    numeric_values = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric_values:
        return None
    return round(sum(numeric_values) / len(numeric_values), 2)


def build_reference_profiles(reference_examples: list[dict[str, Any]], file_type: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for exemplar in flatten_reference_exemplars(reference_examples):
        exemplar_type = normalize_element_type(exemplar.get("element_type"))
        grouped.setdefault(exemplar_type, []).append(exemplar)

    profiles: dict[str, dict[str, Any]] = {}
    for exemplar_type, exemplars in grouped.items():
        profile = {
            "profile_name": exemplar_type,
            "element_type": exemplar_type,
            "file_type": file_type,
            "example_count": len(exemplars),
        }
        for field in _STYLE_FIELDS:
            values = [exemplar.get(field) for exemplar in exemplars if exemplar.get(field) not in (None, "")]
            if field in {"font_size", "space_before", "space_after"}:
                profile[field] = _average_number(values)
            else:
                profile[field] = _most_common(values)
        profiles[exemplar_type] = profile

    return profiles


def build_reference_profiles_by_role(reference_examples: list[dict[str, Any]], file_type: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for exemplar in flatten_reference_exemplars(reference_examples):
        exemplar_type = normalize_element_type(exemplar.get("element_type"))
        placeholder_type = str(exemplar.get("placeholder_type") or "")
        geometry_bucket = exemplar.get("geometry_bucket") or ""
        key_parts = [exemplar_type]
        if placeholder_type:
            key_parts.append(placeholder_type)
        if geometry_bucket:
            key_parts.append(geometry_bucket)
        grouped.setdefault("::".join(key_parts), []).append(exemplar)

    profiles: dict[str, dict[str, Any]] = {}
    for key, exemplars in grouped.items():
        base = build_reference_profiles([{"style_exemplars": exemplars}], file_type)
        base_profile = next(iter(base.values())) if base else {
            "element_type": normalize_element_type(exemplars[0].get("element_type")) if exemplars else "body",
            "example_count": len(exemplars),
        }
        profiles[key] = {
            **base_profile,
            "profile_name": key,
            "element_type": normalize_element_type(exemplars[0].get("element_type")) if exemplars else "body",
            "placeholder_type": exemplars[0].get("placeholder_type") if exemplars else None,
            "geometry_bucket": exemplars[0].get("geometry_bucket") if exemplars else None,
            "example_count": len(exemplars),
        }
    return profiles


def resolve_reference_profile_name(
    element_type: Any,
    file_type: str,
    reference_profiles: dict[str, dict[str, Any]],
    preferred_name: Any = None,
) -> str | None:
    preferred = normalize_element_type(preferred_name) if preferred_name else None
    if preferred and preferred in reference_profiles:
        return preferred

    normalized_type = normalize_element_type(element_type)
    candidates = _ELEMENT_STYLE_FALLBACKS.get(file_type, {}).get(normalized_type, [normalized_type, "body"])
    for candidate in candidates:
        normalized_candidate = normalize_element_type(candidate)
        if normalized_candidate in reference_profiles:
            return normalized_candidate

    if preferred:
        return preferred
    if reference_profiles:
        return max(reference_profiles.items(), key=lambda item: item[1].get("example_count", 0))[0]
    return None


def build_style_from_profile(
    element: dict[str, Any],
    profile_name: str | None,
    reference_profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    profile = reference_profiles.get(profile_name or "", {})
    style = {
        "id": element["id"],
        "ocd_style": profile_name or normalize_element_type(element.get("type")),
        "element_type": element.get("type"),
        "level": element.get("level"),
    }

    for field in _STYLE_FIELDS:
        style[field] = profile.get(field)

    for locator_key in ("slide_idx", "shape_idx", "para_idx"):
        if locator_key in element:
            style[locator_key] = element[locator_key]

    placeholder_type = element.get("placeholder_type")
    if placeholder_type:
        style["placeholder_type"] = placeholder_type
        defaults = get_brand_placeholder_style(str(placeholder_type), "pptx")
        for key, value in defaults.items():
            if style.get(key) in (None, ""):
                style[key] = value

    return style


def resolve_profile_for_element(
    element: dict[str, Any],
    file_type: str,
    reference_profiles: dict[str, dict[str, Any]],
    preferred_name: Any = None,
) -> str | None:
    preferred = normalize_element_type(preferred_name) if preferred_name else None
    if preferred and preferred in reference_profiles:
        return preferred

    element_type = normalize_element_type(element.get("type"))
    placeholder_type = str(element.get("placeholder_type") or "")
    geometry_bucket = element.get("geometry_bucket") or ""
    candidates: list[str] = []
    if placeholder_type and geometry_bucket:
        candidates.append(f"{element_type}::{placeholder_type}::{geometry_bucket}")
    if placeholder_type:
        candidates.append(f"{element_type}::{placeholder_type}")
    if geometry_bucket:
        candidates.append(f"{element_type}::{geometry_bucket}")
    candidates.append(element_type)

    for candidate in candidates:
        if candidate in reference_profiles:
            return candidate

    return resolve_reference_profile_name(element_type, file_type, reference_profiles, preferred_name=preferred_name)


def resolve_table_profiles(
    style_map: list[dict[str, Any]],
    file_type: str,
    reference_profiles: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    table_styles = [style for style in style_map if style.get("element_type") == "table"]
    if table_styles:
        header_style = table_styles[0]
        body_style = table_styles[0]
        return header_style, body_style

    header_profile_name = resolve_reference_profile_name("heading", file_type, reference_profiles, preferred_name="heading")
    body_profile_name = resolve_reference_profile_name("body", file_type, reference_profiles, preferred_name="body")
    header_style = reference_profiles.get(header_profile_name or "")
    body_style = reference_profiles.get(body_profile_name or "")
    return header_style, body_style


def extract_profile_name_from_style(style: dict[str, Any] | None) -> str | None:
    if not style:
        return None
    value = style.get("ocd_style") or style.get("profile_name") or style.get("element_type")
    return normalize_element_type(value)


def score_style_map_against_references(
    style_map: list[dict[str, Any]],
    raw_elements: list[dict[str, Any]],
    file_type: str,
    reference_profiles: dict[str, dict[str, Any]],
    brand_targets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    brand_targets = brand_targets or {}
    if not reference_profiles:
        return {
            "score": 15,
            "compliant": False,
            "breakdown": {
                "brandguide": 0,
                "official_templates": 0,
                "domain_references": 15,
                "typography": 10,
                "colors": 10,
                "spacing": 20,
                "consistency": 20,
            },
            "issues": ["Aucun profil de style exploitable n'a ete extrait des documents de reference."],
            "recommendations": ["Verifier le BrandStore local et reindexer des fichiers de reference riches en styles."],
        }

    element_by_id = {element["id"]: element for element in raw_elements or [] if isinstance(element, dict) and "id" in element}
    totals = {"typography": 0.0, "colors": 0.0, "spacing": 0.0, "consistency": 0.0}
    count = 0

    for style in style_map or []:
        element = element_by_id.get(style.get("id"))
        if not element:
            continue
        profile_name = resolve_reference_profile_name(
            element.get("type"),
            file_type,
            reference_profiles,
            preferred_name=style.get("ocd_style"),
        )
        profile = reference_profiles.get(profile_name or "", {})
        if not profile:
            continue

        typography_checks = [
            style.get("font_name") == profile.get("font_name"),
            style.get("font_size") == profile.get("font_size"),
            style.get("bold") == profile.get("bold"),
            style.get("italic") == profile.get("italic"),
        ]
        color_checks = [style.get("color") == profile.get("color")]
        spacing_checks = []
        if profile.get("alignment") is not None or style.get("alignment") is not None:
            spacing_checks.append(style.get("alignment") == profile.get("alignment"))
        if file_type == "docx":
            if profile.get("space_before") is not None or style.get("space_before") is not None:
                spacing_checks.append(style.get("space_before") == profile.get("space_before"))
            if profile.get("space_after") is not None or style.get("space_after") is not None:
                spacing_checks.append(style.get("space_after") == profile.get("space_after"))
        consistency_checks = [style.get("ocd_style") == profile_name]

        totals["typography"] += 100.0 * sum(1 for item in typography_checks if item) / max(len(typography_checks), 1)
        totals["colors"] += 100.0 * sum(1 for item in color_checks if item) / max(len(color_checks), 1)
        totals["spacing"] += 100.0 * sum(1 for item in spacing_checks if item) / max(len(spacing_checks), 1)
        totals["consistency"] += 100.0 * sum(1 for item in consistency_checks if item) / max(len(consistency_checks), 1)
        count += 1

    if count == 0:
        return {
            "score": 25,
            "compliant": False,
            "breakdown": {
                "brandguide": 25,
                "official_templates": 25,
                "domain_references": 25,
                "typography": 25,
                "colors": 25,
                "spacing": 25,
                "consistency": 25,
            },
            "issues": ["Aucun element du style_map n'a pu etre compare aux profils issus des references."],
            "recommendations": ["Verifier le parsing du document et la generation du style_map."],
        }

    breakdown = {key: round(value / count, 2) for key, value in totals.items()}

    preferred_fonts = set(brand_targets.get("preferred_fonts") or [])
    allowed_colors = set(brand_targets.get("allowed_colors") or [])
    preferred_placeholders = set(brand_targets.get("preferred_placeholders") or [])
    preferred_sizes = set(brand_targets.get("preferred_sizes") or [])

    style_count = max(len(style_map or []), 1)
    brandguide_checks = 0
    template_checks = 0
    content_checks = 0

    for style in style_map or []:
        if not isinstance(style, dict):
            continue
        if preferred_fonts and style.get("font_name") in preferred_fonts:
            brandguide_checks += 1
        if allowed_colors and style.get("color") in allowed_colors:
            brandguide_checks += 1
        if preferred_sizes and style.get("font_size") in preferred_sizes:
            template_checks += 1
        if preferred_placeholders and style.get("element_type"):
            content_checks += 1

    brandguide_score = round(100.0 * brandguide_checks / max(style_count * 2, 1), 2)
    official_template_score = round(100.0 * template_checks / max(style_count, 1), 2)
    domain_reference_score = round(
        (breakdown["typography"] + breakdown["colors"] + breakdown["spacing"] + breakdown["consistency"]) / 4,
        2,
    )

    weighted_score = (
        brandguide_score * 0.45
        + official_template_score * 0.35
        + domain_reference_score * 0.20
    )
    score = round(weighted_score, 2)
    issues: list[str] = []
    recommendations: list[str] = []

    breakdown = {
        "brandguide": brandguide_score,
        "official_templates": official_template_score,
        "domain_references": domain_reference_score,
        **breakdown,
    }

    if breakdown["typography"] < 90:
        issues.append("La typographie s'ecarte encore des styles extraits des documents de reference.")
        recommendations.append("Verifier les profils title/heading/body issus du BrandStore et enrichir les references si besoin.")
    if breakdown["colors"] < 90:
        issues.append("Les couleurs appliquees ne sont pas assez coherentes avec les fichiers de reference recuperes.")
        recommendations.append("Ajouter des references contenant des couleurs explicites pour renforcer les profils utilises.")
    if breakdown["spacing"] < 85:
        issues.append("Les alignements ou espacements restent incomplets par rapport aux styles observes dans les references.")
        recommendations.append("Completer le BrandStore avec des documents de reference plus riches en mise en page.")
    if breakdown["consistency"] < 95:
        issues.append("Certains elements n'ont pas ete rattaches au meilleur profil de reference disponible.")
        recommendations.append("Verifier le typing des elements (title, heading, body, bullet) et la selection RAG des references.")
    if breakdown["brandguide"] < 80:
        issues.append("La sortie respecte insuffisamment le brandguide Orange, qui doit rester prioritaire.")
        recommendations.append("Renforcer l'alignement sur GuidelinesFR.pdf et les regles officielles de typographie/couleurs.")
    if breakdown["official_templates"] < 80:
        issues.append("La sortie n'est pas encore assez proche des templates officiels PPT-FR.")
        recommendations.append("Verifier la selection des templates officiels et faire primer leurs layouts/styles sur les references metier.")

    if not issues:
        issues.append("La mise en forme suit de facon coherente le brandguide, les templates officiels et les references selectionnees.")
    if not recommendations:
        recommendations.append("Faire une validation visuelle rapide sur le document genere pour confirmer le rendu final.")

    return {
        "score": score,
        "compliant": score >= 75,
        "breakdown": breakdown,
        "issues": issues,
        "recommendations": recommendations,
    }
