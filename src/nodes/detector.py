import os
from src.state import PresFactoryState


def detect_format(state: PresFactoryState) -> dict:
    file_path = state["file_path"]
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".docx":
        return {"file_type": "docx"}
    elif ext in (".pptx", ".ppt"):
        return {"file_type": "pptx"}
    else:
        return {"error": f"Format non supporté: '{ext}'. Utilisez .docx ou .pptx"}
