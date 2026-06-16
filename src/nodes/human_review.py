from src.state import PresFactoryState


def human_review(state: PresFactoryState) -> dict:
    """
    Nœud garde-fou humain.
    Ce nœud est un pass-through : le graphe s'arrête juste AVANT lui
    (interrupt_before=["human_review"]).
    L'interface UI met à jour validation_status + human_feedback dans le state,
    puis relance le graphe. Le routing post-nœud décide la suite.
    """
    return {}
