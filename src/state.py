from typing import TypedDict, Optional, Literal, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages


class PresFactoryState(TypedDict):
    # Input
    file_path: str
    original_file_path: Optional[str]
    file_type: Optional[Literal["docx", "pptx"]]

    # Parsed content (indexed — ordre document préservé)
    raw_elements: List[Dict[str, Any]]
    anonymized_elements: List[Dict[str, Any]]
    document_title: Optional[str]

    # RAG context
    similar_examples: List[Dict[str, Any]]
    primary_reference_deck: Optional[Dict[str, Any]]

    # Style processing
    style_map: List[Dict[str, Any]]

    # Output
    output_path: Optional[str]

    # Quality control
    quality_score: Optional[float]
    quality_report: Optional[Dict[str, Any]]

    # Human in the loop
    validation_status: Literal["pending", "approved", "rejected"]
    human_feedback: Optional[str]

    # Loop control
    iteration_count: int
    max_iterations: int

    # Error
    error: Optional[str]

    # Conversation trace
    messages: Annotated[list, add_messages]
