import json
import re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import PresFactoryState
from src.llm.client import get_llm
from src.rag.store import similarity_search

CHARTER_PATH = Path(__file__).parent.parent / "charter" / "ocd_charter.json"

_SYSTEM_PROMPT = """Tu es un expert en charte graphique Orange Cyberdefense (OCD).

Ta mission : créer un style_map JSON qui assigne le style OCD correct à chaque élément du document.

RÈGLES :
- Respecte STRICTEMENT les spécifications de la charte OCD fournie.
- Pour chaque élément, conserve son "id" exactement tel quel.
- Le champ "ocd_style" doit correspondre à une clé des styles de la charte.
- Ne modifie JAMAIS le contenu textuel.
- Réponds UNIQUEMENT avec un JSON array valide, sans markdown ni commentaire.

FORMAT DE SORTIE (array JSON) :
[
  {
    "id": "<id_element>",
    "ocd_style": "<nom_style>",
    "font_name": "<police>",
    "font_size": <taille_pt>,
    "bold": <true|false>,
    "italic": <false|true>,
    "color": "<#RRGGBB>",
    "alignment": "<left|center|right|justify>",
    "space_before": <pt>,
    "space_after": <pt>
  }
]
"""


def _extract_json(text: str) -> list:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []


def map_styles(state: PresFactoryState) -> dict:
    elements = state["anonymized_elements"]
    file_type = state["file_type"]
    human_feedback = state.get("human_feedback") or ""

    charter = json.loads(CHARTER_PATH.read_text(encoding="utf-8"))
    charter_section = charter.get(file_type, {})

    # RAG : récupère des exemples similaires du BrandStore
    query = " ".join(e["content"] for e in elements[:5])
    rag_docs = similarity_search(query, k=3)
    rag_context = "\n---\n".join(doc.page_content for doc in rag_docs) if rag_docs else "Aucun exemple disponible."

    feedback_block = (
        f"\n\nFEEDBACK EXPERT (prioritaire) :\n{human_feedback}"
        if human_feedback else ""
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=f"""CHARTE OCD ({file_type.upper()}) :
{json.dumps(charter_section, indent=2, ensure_ascii=False)}

EXEMPLES BRANDSTORE SIMILAIRES :
{rag_context}
{feedback_block}

ÉLÉMENTS DU DOCUMENT :
{json.dumps(elements, indent=2, ensure_ascii=False)}

Génère le style_map JSON."""),
    ]

    response = llm.invoke(messages)
    style_map = _extract_json(response.content)

    similar_examples = [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in rag_docs
    ]

    return {
        "style_map": style_map,
        "similar_examples": similar_examples,
        "human_feedback": None,  # reset après usage
    }
