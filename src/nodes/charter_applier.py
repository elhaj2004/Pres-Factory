import json
from pathlib import Path
from typing import Dict, Any, List

from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from pptx import Presentation
from pptx.util import Pt as PptPt
from pptx.dml.color import RGBColor as PptRGBColor

from src.state import PresFactoryState

CHARTER_PATH = Path(__file__).parent.parent / "charter" / "ocd_charter.json"

_ALIGN_DOCX = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ── DOCX ──────────────────────────────────────────────────────────────────────

def _apply_docx_para_style(para, style: Dict[str, Any]) -> None:
    pf = para.paragraph_format
    pf.alignment = _ALIGN_DOCX.get(style.get("alignment", "left"), WD_ALIGN_PARAGRAPH.LEFT)
    if style.get("space_before") is not None:
        pf.space_before = Pt(style["space_before"])
    if style.get("space_after") is not None:
        pf.space_after = Pt(style["space_after"])

    for run in para.runs:
        if style.get("font_name"):
            run.font.name = style["font_name"]
        if style.get("font_size"):
            run.font.size = Pt(float(style["font_size"]))
        if style.get("bold") is not None:
            run.font.bold = style["bold"]
        if style.get("italic") is not None:
            run.font.italic = style["italic"]
        if style.get("color"):
            r, g, b = _hex_to_rgb(style["color"])
            run.font.color.rgb = RGBColor(r, g, b)


def _apply_docx(file_path: str, elements: List[Dict], style_map: List[Dict], output_path: str) -> None:
    doc = DocxDocument(file_path)
    charter = json.loads(CHARTER_PATH.read_text(encoding="utf-8"))

    # Index styles by element id
    style_by_id: Dict[str, Dict] = {s["id"]: s for s in style_map if "id" in s}

    # Match paragraphs in order (parser et applier utilisent le même ordre)
    elem_iter = iter(elements)
    current_elem = next(elem_iter, None)

    for para in doc.paragraphs:
        if not para.text.strip() or current_elem is None:
            continue
        style = style_by_id.get(current_elem["id"])
        if style:
            _apply_docx_para_style(para, style)
        current_elem = next(elem_iter, None)

    # Tableaux : en-tête orange + corps conforme
    table_styles = charter["docx"]["styles"]
    header_color = charter["colors"]["table_header_bg"]
    header_text_color = charter["colors"]["table_header_text"]

    for table in doc.tables:
        for row_idx, row in enumerate(table.rows):
            style_key = "table_header" if row_idx == 0 else "table_body"
            s = table_styles[style_key]
            text_color = header_text_color if row_idx == 0 else s["color"]
            for cell in row.cells:
                for cell_para in cell.paragraphs:
                    for run in cell_para.runs:
                        if s.get("font_name"):
                            run.font.name = s["font_name"]
                        if s.get("font_size"):
                            run.font.size = Pt(float(s["font_size"]))
                        run.font.bold = s.get("bold", False)
                        r, g, b = _hex_to_rgb(text_color)
                        run.font.color.rgb = RGBColor(r, g, b)

    doc.save(output_path)


# ── PPTX ──────────────────────────────────────────────────────────────────────

def _apply_pptx_para_style(para, style: Dict[str, Any]) -> None:
    for run in para.runs:
        if style.get("font_name"):
            run.font.name = style["font_name"]
        if style.get("font_size"):
            run.font.size = PptPt(float(style["font_size"]))
        if style.get("bold") is not None:
            run.font.bold = style["bold"]
        if style.get("italic") is not None:
            run.font.italic = style["italic"]
        if style.get("color"):
            r, g, b = _hex_to_rgb(style["color"])
            run.font.color.rgb = PptRGBColor(r, g, b)


def _apply_pptx(file_path: str, elements: List[Dict], style_map: List[Dict], output_path: str) -> None:
    prs = Presentation(file_path)
    style_by_id: Dict[str, Dict] = {s["id"]: s for s in style_map if "id" in s}

    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                # Cherche l'élément correspondant par contenu (PPTX ids sont déterministes)
                for elem in elements:
                    if elem["content"][:60] == text[:60]:
                        style = style_by_id.get(elem["id"])
                        if style:
                            _apply_pptx_para_style(para, style)
                        break

    prs.save(output_path)


# ── NODE ──────────────────────────────────────────────────────────────────────

def apply_charter(state: PresFactoryState) -> dict:
    file_path = state["file_path"]
    file_type = state["file_type"]
    elements = state["anonymized_elements"]
    style_map = state["style_map"]
    iteration = state.get("iteration_count", 0)

    output_dir = Path(file_path).parent.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    base = Path(file_path).stem
    output_path = str(output_dir / f"{base}_ocd_v{iteration + 1}.{file_type}")

    try:
        if file_type == "docx":
            _apply_docx(file_path, elements, style_map, output_path)
        else:
            _apply_pptx(file_path, elements, style_map, output_path)

        return {
            "output_path": output_path,
            "iteration_count": iteration + 1,
        }
    except Exception as e:
        return {"error": f"Erreur application charte: {e}"}
