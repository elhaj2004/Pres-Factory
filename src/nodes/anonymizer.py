import re
import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import PresFactoryState
from src.llm.client import get_llm

# Patterns RGPD basiques appliqués en pre-pass (avant LLM)
_REGEX_RULES = [
    (r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b(?:\+33|0)[1-9](?:[\s.\-]?\d{2}){4}\b', '[TELEPHONE]'),
    (r'\b\d{1,3}[,.\s]\d{3}(?:[,.\s]\d{3})?\s*€', '[MONTANT]'),
    (r'\b\d+\s*[Mm]€\b', '[MONTANT]'),
]

_SYSTEM_PROMPT = """Tu es un expert en anonymisation de données RGPD pour Orange Cyberdefense.

Remplace UNIQUEMENT les données sensibles suivantes par leur placeholder :
- Noms de clients / entreprises clientes → [NOM_CLIENT]
- Noms de personnes (prénom + nom) → [NOM_PERSONNE]
- Montants et prix → [MONTANT]
- Dates précises → [DATE]
- Références de projets/contrats clients spécifiques → [REF_PROJET]
- Données personnelles non encore remplacées → [DONNEE_PERSO]

Règles impératives :
1. NE MODIFIE PAS le reste du texte (structure, mise en forme, contenu métier).
2. Conserve EXACTEMENT la numérotation JSON fournie.
3. Réponds UNIQUEMENT avec le JSON modifié, sans markdown.
"""


def _apply_regex(text: str) -> str:
    for pattern, repl in _REGEX_RULES:
        text = re.sub(pattern, repl, text)
    return text


def anonymize(state: PresFactoryState) -> dict:
    elements = state["raw_elements"]

    # Pre-pass regex
    pre_processed = [
        {**e, "content": _apply_regex(e["content"])} for e in elements
    ]

    # LLM anonymization (batch de 30 éléments max pour éviter le dépassement de tokens)
    batch_size = 30
    anonymized = list(pre_processed)

    llm = get_llm()

    for start in range(0, len(pre_processed), batch_size):
        batch = pre_processed[start : start + batch_size]
        batch_payload = {str(i + start): e["content"] for i, e in enumerate(batch)}

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(batch_payload, ensure_ascii=False)),
        ]

        try:
            response = llm.invoke(messages)
            result = json.loads(response.content)
            for key, new_content in result.items():
                idx = int(key)
                if 0 <= idx < len(anonymized):
                    anonymized[idx] = {**anonymized[idx], "content": new_content}
        except Exception:
            # En cas d'échec LLM, on garde le pre-pass regex
            pass

    return {"anonymized_elements": anonymized}
