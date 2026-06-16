import json
import re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import PresFactoryState
from src.llm.client import get_llm

CHARTER_PATH = Path(__file__).parent.parent / "charter" / "ocd_charter.json"

_SYSTEM_PROMPT = """Tu es un auditeur qualité charte graphique Orange Cyberdefense.

Évalue la conformité OCD du style_map appliqué sur le document.

Analyse :
1. Typographie (polices, tailles, graisse)
2. Couleurs (respect de la palette OCD)
3. Espacements (marges, espaces avant/après)
4. Cohérence globale (hiérarchie visuelle, uniformité)

Réponds UNIQUEMENT avec un JSON valide, sans markdown :
{
  "score": <entier 0-100>,
  "compliant": <true si score >= 75>,
  "breakdown": {
    "typography": <0-100>,
    "colors": <0-100>,
    "spacing": <0-100>,
    "consistency": <0-100>
  },
  "issues": ["<problème 1>", "<problème 2>"],
  "recommendations": ["<reco 1>", "<reco 2>"]
}
"""


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {
            "score": 50,
            "compliant": False,
            "breakdown": {"typography": 50, "colors": 50, "spacing": 50, "consistency": 50},
            "issues": ["Impossible d'évaluer automatiquement"],
            "recommendations": ["Vérification manuelle requise"],
        }


def check_quality(state: PresFactoryState) -> dict:
    style_map = state.get("style_map", [])
    file_type = state["file_type"]
    similar_examples = state.get("similar_examples", [])

    charter = json.loads(CHARTER_PATH.read_text(encoding="utf-8"))
    charter_section = charter.get(file_type, {})

    rag_context = (
        "\n---\n".join(e.get("content", "") for e in similar_examples[:2])
        if similar_examples else "Aucun exemple de référence."
    )

    # On limite la taille du payload pour ne pas dépasser les tokens
    style_sample = style_map[:25]

    llm = get_llm()
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=f"""CHARTE OCD ({file_type.upper()}) :
{json.dumps(charter_section, indent=2, ensure_ascii=False)}

EXEMPLES BRANDSTORE :
{rag_context}

STYLE_MAP APPLIQUÉ (extrait) :
{json.dumps(style_sample, indent=2, ensure_ascii=False)}

Évalue la conformité."""),
    ]

    response = llm.invoke(messages)
    report = _extract_json(response.content)

    return {
        "quality_score": float(report.get("score", 0)),
        "quality_report": report,
    }
