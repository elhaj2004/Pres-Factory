import json
from typing import List, Dict, Any
from docx import Document as DocxDocument
from pptx import Presentation
from src.state import PresFactoryState


def _docx_element_type(style_name: str) -> tuple[str, int]:
    name = style_name.lower()
    if "heading 1" in name:
        return "heading_1", 1
    if "heading 2" in name:
        return "heading_2", 2
    if "heading 3" in name:
        return "heading_3", 3
    if any(k in name for k in ("list", "bullet", "liste")):
        return "bullet", 1
    if "caption" in name or "légende" in name:
        return "caption", 0
    return "body", 0


def _parse_docx(file_path: str) -> List[Dict[str, Any]]:
    doc = DocxDocument(file_path)
    elements = []
    idx = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        elem_type, level = _docx_element_type(para.style.name)
        elements.append({
            "id": f"para_{idx}",
            "type": elem_type,
            "content": text,
            "original_style": para.style.name,
            "level": level,
            "source": "paragraph",
        })
        idx += 1

    for t_idx, table in enumerate(doc.tables):
        rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
        elements.append({
            "id": f"table_{t_idx}",
            "type": "table",
            "content": json.dumps(rows, ensure_ascii=False),
            "original_style": "table",
            "level": 0,
            "source": "table",
        })

    return elements


def _pptx_element_type(shape_idx: int, para_level: int, is_first_shape: bool) -> str:
    if is_first_shape and shape_idx == 0:
        return "title"
    if para_level == 0:
        return "heading" if shape_idx == 0 else "body"
    if para_level == 1:
        return "bullet_level_1"
    return "bullet_level_2"


def _parse_pptx(file_path: str) -> List[Dict[str, Any]]:
    prs = Presentation(file_path)
    elements = []

    for slide_idx, slide in enumerate(prs.slides):
        for shape_idx, shape in enumerate(slide.shapes):
            if not shape.has_text_frame:
                continue
            for para_idx, para in enumerate(shape.text_frame.paragraphs):
                text = para.text.strip()
                if not text:
                    continue
                elem_type = _pptx_element_type(
                    shape_idx, para.level, slide_idx == 0
                )
                elements.append({
                    "id": f"s{slide_idx}_sh{shape_idx}_p{para_idx}",
                    "type": elem_type,
                    "content": text,
                    "original_style": None,
                    "level": para.level,
                    "source": "slide",
                    "slide_idx": slide_idx,
                    "shape_idx": shape_idx,
                    "para_idx": para_idx,
                })

    return elements


def parse_document(state: PresFactoryState) -> dict:
    try:
        if state["file_type"] == "docx":
            elements = _parse_docx(state["file_path"])
        else:
            elements = _parse_pptx(state["file_path"])
        return {"raw_elements": elements}
    except Exception as e:
        return {"error": f"Erreur de parsing: {e}"}
