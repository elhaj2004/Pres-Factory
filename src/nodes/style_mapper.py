import json
import re
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm.client import get_llm
from src.reference_decks import find_primary_reference_deck
from src.rag.store import extract_style_aware_exemplars, similarity_search
from src.reference_styles import (
    build_reference_profiles,
    build_reference_profiles_by_role,
    build_style_from_profile,
    resolve_profile_for_element,
)
from src.state import PresFactoryState

_SYSTEM_PROMPT = """Tu derives les styles d'un document cible uniquement a partir des documents de reference recuperes.

Regles obligatoires :
- N'utilise PAS de charte JSON externe ni de palette predefinie.
- Appuie-toi uniquement sur les exemples de reference fournis.
- Couvre TOUS les elements du document cible.
- Conserve exactement chaque champ `id`.
- Pour les fichiers PPTX, preserve les coordonnees parser (`slide_idx`, `shape_idx`, `para_idx`) comme reperes conceptuels.
- Le champ `ocd_style` doit etre le nom du profil de reference le plus proche (`title`, `heading`, `subtitle`, `body`, `bullet_level_1`, `bullet_level_2`, `caption`, etc.).
- Ne modifie jamais le contenu textuel.
- Reponds UNIQUEMENT avec un JSON array valide, sans markdown ni commentaire.

Format de sortie :
[
  {
    "id": "<id_element>",
    "ocd_style": "<nom_profil_reference>"
  }
]
"""


def _extract_json(text: str) -> list:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return []


def _build_reference_examples(state: PresFactoryState, file_type: str) -> list[dict[str, Any]]:
    query_parts = [
        element.get("content", "")
        for element in state["anonymized_elements"][:6]
        if element.get("content")
    ]
    query = " ".join(query_parts).strip()
    rag_docs = similarity_search(query or file_type, k=8)

    expected_extension = f".{file_type}"
    filtered_docs = [doc for doc in rag_docs if doc.metadata.get("extension") == expected_extension]
    selected_docs = filtered_docs[:4] if filtered_docs else rag_docs[:4]

    reference_examples: list[dict[str, Any]] = []
    for doc in selected_docs:
        source = doc.metadata.get("source")
        exemplars = extract_style_aware_exemplars(Path(source), file_type, limit=10) if source else []
        if not exemplars:
            continue
        reference_examples.append(
            {
                "content": doc.page_content[:1400],
                "metadata": doc.metadata,
                "style_exemplars": exemplars,
            }
        )

    return reference_examples


def _finalize_style_map(
    raw_style_map: Any,
    elements: list[dict[str, Any]],
    file_type: str,
    reference_profiles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    entries = raw_style_map if isinstance(raw_style_map, list) else []
    by_id = {
        entry.get("id"): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    finalized: list[dict[str, Any]] = []
    for element in elements:
        llm_entry = by_id.get(element["id"], {})
        profile_name = resolve_profile_for_element(
            element,
            file_type,
            reference_profiles,
            preferred_name=llm_entry.get("ocd_style"),
        )
        finalized.append(build_style_from_profile(element, profile_name, reference_profiles))
    return finalized


def map_styles(state: PresFactoryState) -> dict:
    elements = state["anonymized_elements"]
    file_type = state["file_type"]
    human_feedback = state.get("human_feedback") or ""
    primary_reference_deck = find_primary_reference_deck(
        original_file_path=state.get("original_file_path") or state.get("file_path"),
        file_type=file_type,
        document_title=state.get("document_title"),
        raw_elements=state.get("raw_elements", []),
    )

    reference_examples = _build_reference_examples(state, file_type)
    if primary_reference_deck:
        primary_path = Path(primary_reference_deck["path"])
        primary_exemplars = extract_style_aware_exemplars(primary_path, file_type, limit=24)
        if primary_exemplars:
            reference_examples.insert(
                0,
                {
                    "content": f"PRIMARY_REFERENCE_DECK::{primary_path.name}",
                    "metadata": {
                        "source": str(primary_path),
                        "filename": primary_path.name,
                        "extension": primary_path.suffix.lower(),
                        "priority": "primary_reference_deck",
                        "selection_strategy": primary_reference_deck.get("strategy"),
                        "selection_score": primary_reference_deck.get("score"),
                    },
                    "style_exemplars": primary_exemplars,
                },
            )
    generic_profiles = build_reference_profiles(reference_examples, file_type)
    role_profiles = build_reference_profiles_by_role(reference_examples, file_type)
    reference_profiles = {**generic_profiles, **role_profiles}
    reference_profiles_payload = {
        key: {
            profile_key: profile_value
            for profile_key, profile_value in profile.items()
            if profile_key != "file_type"
        }
        for key, profile in reference_profiles.items()
    }

    element_summary = {
        "count": len(elements),
        "types": {
            elem_type: sum(1 for element in elements if element.get("type") == elem_type)
            for elem_type in sorted({element.get("type") for element in elements})
        },
    }

    feedback_block = (
        f"\n\nFEEDBACK EXPERT (prioritaire) :\n{human_feedback}"
        if human_feedback
        else ""
    )

    raw_style_map: list[dict[str, Any]] = []
    if reference_profiles:
        try:
            llm = get_llm()
            messages = [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=f"""RÉSUMÉ DU DOCUMENT CIBLE :
{json.dumps(element_summary, indent=2, ensure_ascii=False)}

DECK DE RÉFÉRENCE PRIORITAIRE :
{json.dumps(primary_reference_deck, indent=2, ensure_ascii=False) if primary_reference_deck else "null"}

PROFILS DE STYLE DÉRIVÉS DES DOCUMENTS DE RÉFÉRENCE :
{json.dumps(reference_profiles_payload, indent=2, ensure_ascii=False)}

EXEMPLES BRANDSTORE STYLE-AWARE :
{json.dumps(reference_examples, indent=2, ensure_ascii=False)}
{feedback_block}

ÉLÉMENTS DU DOCUMENT :
{json.dumps(elements, indent=2, ensure_ascii=False)}

Génère le style_map JSON."""),
            ]
            response = llm.invoke(messages)
            raw_style_map = _extract_json(response.content)
        except Exception:
            raw_style_map = []

    style_map = _finalize_style_map(raw_style_map, elements, file_type, reference_profiles)

    return {
        "style_map": style_map,
        "similar_examples": reference_examples,
        "primary_reference_deck": primary_reference_deck,
        "human_feedback": None,
    }
