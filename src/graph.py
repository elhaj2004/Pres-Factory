import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.state import PresFactoryState
from src.nodes.detector import detect_format
from src.nodes.parser import parse_document
from src.nodes.anonymizer import anonymize
from src.nodes.style_mapper import map_styles
from src.nodes.charter_applier import apply_charter
from src.nodes.quality_checker import check_quality
from src.nodes.human_review import human_review

QUALITY_THRESHOLD = int(os.getenv("QUALITY_THRESHOLD", "70"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_after_detect(state: PresFactoryState) -> str:
    return END if state.get("error") else "parse_document"


def _route_after_parse(state: PresFactoryState) -> str:
    return END if state.get("error") else "anonymize"


def _route_after_apply(state: PresFactoryState) -> str:
    return END if state.get("error") else "check_quality"


def _route_after_quality(state: PresFactoryState) -> str:
    score = state.get("quality_score", 0)
    iteration = state.get("iteration_count", 0)

    # Force human review si score ok ou nb max d'itérations atteint
    if score >= QUALITY_THRESHOLD or iteration >= MAX_ITERATIONS:
        return "human_review"
    return "map_styles"  # retry automatique


def _route_after_review(state: PresFactoryState) -> str:
    status = state.get("validation_status", "pending")
    iteration = state.get("iteration_count", 0)

    if status == "approved":
        return END
    if iteration >= MAX_ITERATIONS:
        return END  # Force la sortie après trop d'itérations
    return "map_styles"  # Relance avec le feedback humain


# ── Graph factory ─────────────────────────────────────────────────────────────

def create_graph(checkpointer=None):
    builder = StateGraph(PresFactoryState)

    builder.add_node("detect_format", detect_format)
    builder.add_node("parse_document", parse_document)
    builder.add_node("anonymize", anonymize)
    builder.add_node("map_styles", map_styles)
    builder.add_node("apply_charter", apply_charter)
    builder.add_node("check_quality", check_quality)
    builder.add_node("human_review", human_review)

    builder.add_edge(START, "detect_format")
    builder.add_conditional_edges("detect_format", _route_after_detect)
    builder.add_conditional_edges("parse_document", _route_after_parse)
    builder.add_edge("anonymize", "map_styles")
    builder.add_edge("map_styles", "apply_charter")
    builder.add_conditional_edges("apply_charter", _route_after_apply)
    builder.add_conditional_edges("check_quality", _route_after_quality)
    builder.add_conditional_edges("human_review", _route_after_review)

    cp = checkpointer or MemorySaver()
    return builder.compile(
        checkpointer=cp,
        interrupt_before=["human_review"],
    )


# Singleton utilisé par l'UI
graph = create_graph()
