"""
Pres Factory — Interface Gradio
Orange Cyberdefense
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import uuid
import shutil
from pathlib import Path

import gradio as gr
from src.graph import graph
from src.state import PresFactoryState

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# thread_id → config actif (session en mémoire par thread)
_sessions: dict = {}

OCD_ORANGE = "#FF6600"
OCD_BLACK = "#1A1A1A"

CSS = f"""
:root {{
    --ocd-orange: {OCD_ORANGE};
    --ocd-black: {OCD_BLACK};
}}
.gradio-container {{ font-family: 'Calibri', 'Arial', sans-serif; }}
#header {{
    background: var(--ocd-black);
    border-left: 6px solid var(--ocd-orange);
    padding: 16px 20px;
    border-radius: 6px;
    margin-bottom: 8px;
}}
#header h1 {{ color: var(--ocd-orange); margin: 0; font-size: 1.6rem; }}
#header p  {{ color: #ccc; margin: 4px 0 0 0; font-size: 0.9rem; }}
.step-label {{ color: var(--ocd-orange); font-weight: bold; font-size: 1rem; }}
.score-box  {{ border-left: 4px solid var(--ocd-orange); padding-left: 12px; }}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _initial_state(file_path: str) -> dict:
    return {
        "file_path": file_path,
        "file_type": None,
        "raw_elements": [],
        "anonymized_elements": [],
        "similar_examples": [],
        "style_map": [],
        "output_path": None,
        "quality_score": None,
        "quality_report": None,
        "validation_status": "pending",
        "human_feedback": None,
        "iteration_count": 0,
        "max_iterations": int(os.getenv("MAX_ITERATIONS", "3")),
        "error": None,
        "messages": [],
    }


def _format_report(score, report: dict, iteration: int) -> str:
    if not report:
        return "*Aucun rapport disponible.*"
    bd = report.get("breakdown", {})
    issues = report.get("issues", [])
    recos = report.get("recommendations", [])
    score_emoji = "✅" if score >= 75 else ("⚠️" if score >= 50 else "❌")

    lines = [
        f"## {score_emoji} Score de conformité OCD : **{score:.0f} / 100**",
        f"*(Itération {iteration})*",
        "",
        "### Détail",
        f"- Typographie : **{bd.get('typography', '—')}/100**",
        f"- Couleurs : **{bd.get('colors', '—')}/100**",
        f"- Espacements : **{bd.get('spacing', '—')}/100**",
        f"- Cohérence : **{bd.get('consistency', '—')}/100**",
    ]
    if issues:
        lines += ["", "### Problèmes détectés"] + [f"- {i}" for i in issues]
    if recos:
        lines += ["", "### Recommandations"] + [f"- {r}" for r in recos]

    return "\n".join(lines)


def _run_until_interrupt(initial_state: dict, config: dict) -> dict:
    last = initial_state
    for event in graph.stream(initial_state, config, stream_mode="values"):
        last = event
    return last


def _resume_graph(config: dict) -> dict:
    last = {}
    for event in graph.stream(None, config, stream_mode="values"):
        last = event
    return last


# ── Callbacks Gradio ──────────────────────────────────────────────────────────

def cb_process(file_obj, progress=gr.Progress(track_tqdm=True)):
    """Étape 1 : upload + traitement jusqu'au garde-fou."""
    if file_obj is None:
        return (
            gr.update(),               # thread_id_state
            "⚠️ Aucun fichier sélectionné.",  # status
            gr.update(visible=False),  # report_md
            gr.update(visible=False),  # review_row
            gr.update(visible=False),  # download_file
            None,                      # download_file value
        )

    thread_id = str(uuid.uuid4())
    ext = Path(file_obj.name).suffix
    dest = UPLOAD_DIR / f"{thread_id}{ext}"
    shutil.copy(file_obj.name, str(dest))

    config = {"configurable": {"thread_id": thread_id}}
    _sessions[thread_id] = config

    progress(0.1, desc="Détection du format…")
    state = _initial_state(str(dest))

    progress(0.2, desc="Parsing et anonymisation…")
    final = _run_until_interrupt(state, config)

    error = final.get("error")
    if error:
        return (
            gr.update(),
            f"❌ {error}",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            None,
        )

    score = final.get("quality_score") or 0
    report = final.get("quality_report") or {}
    iteration = final.get("iteration_count", 1)
    output_path = final.get("output_path")

    report_md = _format_report(score, report, iteration)
    progress(1.0, desc="Analyse terminée")

    return (
        thread_id,
        f"✅ Traitement terminé — score {score:.0f}/100. Vérifiez le rapport et validez.",
        gr.update(value=report_md, visible=True),
        gr.update(visible=True),
        gr.update(visible=bool(output_path), value=output_path),
        output_path,
    )


def cb_approve(thread_id, feedback):
    """Étape 2a : approbation."""
    if not thread_id or thread_id not in _sessions:
        return "❌ Session expirée. Recommencez.", gr.update(), gr.update(visible=False)

    config = _sessions[thread_id]
    graph.update_state(config, {"validation_status": "approved", "human_feedback": None})
    final = _resume_graph(config)

    output_path = final.get("output_path")
    return (
        "✅ Document approuvé et disponible en téléchargement.",
        gr.update(visible=bool(output_path), value=output_path),
        gr.update(visible=False),
    )


def cb_reject(thread_id, feedback):
    """Étape 2b : rejet + feedback → nouvelle itération."""
    if not thread_id or thread_id not in _sessions:
        return "❌ Session expirée.", gr.update(), gr.update(), gr.update(visible=False)

    if not feedback or not feedback.strip():
        return (
            "⚠️ Merci de fournir un feedback avant de rejeter.",
            gr.update(),
            gr.update(),
            gr.update(visible=True),
        )

    config = _sessions[thread_id]
    graph.update_state(
        config,
        {
            "validation_status": "rejected",
            "human_feedback": feedback.strip(),
        },
    )

    # Reprend le graphe → human_review → map_styles → … → nouvel interrupt
    final = _resume_graph(config)

    error = final.get("error")
    if error:
        return f"❌ {error}", gr.update(), gr.update(), gr.update(visible=True)

    score = final.get("quality_score") or 0
    report = final.get("quality_report") or {}
    iteration = final.get("iteration_count", 1)
    output_path = final.get("output_path")

    if final.get("validation_status") == "approved" or not final.get("style_map"):
        return (
            f"✅ Révision terminée — score {score:.0f}/100.",
            gr.update(value=_format_report(score, report, iteration)),
            gr.update(visible=bool(output_path), value=output_path),
            gr.update(visible=False),
        )

    return (
        f"🔄 Révision {iteration} effectuée — score {score:.0f}/100. Revalidez.",
        gr.update(value=_format_report(score, report, iteration)),
        gr.update(visible=bool(output_path), value=output_path),
        gr.update(visible=True),
    )


# ── Layout ────────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Pres Factory — OCD") as demo:

        gr.HTML("""
        <div id="header">
          <h1>⚙️ Pres Factory</h1>
          <p>Agent de mise en conformité charte graphique — Orange Cyberdefense</p>
        </div>
        """)

        thread_id_state = gr.State(None)

        with gr.Row():
            # ── Colonne gauche : Upload + validation ──────────────────────────
            with gr.Column(scale=1, min_width=320):
                gr.Markdown("### 📂 1. Importer le document", elem_classes="step-label")
                file_input = gr.File(
                    label="Déposer un fichier .docx ou .pptx",
                    file_types=[".docx", ".pptx"],
                    type="filepath",
                )
                process_btn = gr.Button(
                    "▶ Appliquer la charte OCD",
                    variant="primary",
                    size="lg",
                )

                gr.Markdown("---")
                gr.Markdown("### ✅ 2. Valider le résultat", elem_classes="step-label")

                feedback_box = gr.Textbox(
                    label="Feedback (obligatoire en cas de rejet)",
                    placeholder="Ex : Les titres devraient être plus grands, la couleur des tableaux est incorrecte…",
                    lines=3,
                    visible=False,
                )

                with gr.Row(visible=False) as review_row:
                    approve_btn = gr.Button("✅ Approuver", variant="primary")
                    reject_btn = gr.Button("🔄 Rejeter et réviser", variant="stop")

                status_box = gr.Markdown("")

                gr.Markdown("---")
                gr.Markdown("### ⬇️ 3. Télécharger", elem_classes="step-label")
                download_file = gr.File(
                    label="Document conforme charte OCD",
                    visible=False,
                    interactive=False,
                )

            # ── Colonne droite : Rapport qualité ─────────────────────────────
            with gr.Column(scale=1, min_width=320):
                gr.Markdown("### 📊 Rapport de conformité OCD", elem_classes="step-label")
                report_md = gr.Markdown(
                    "*Le rapport de conformité apparaîtra ici après traitement.*",
                    visible=True,
                    elem_classes="score-box",
                )

        # ── Événements ────────────────────────────────────────────────────────

        process_btn.click(
            fn=cb_process,
            inputs=[file_input],
            outputs=[
                thread_id_state,
                status_box,
                report_md,
                review_row,
                download_file,
                download_file,
            ],
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=[feedback_box],
        )

        approve_btn.click(
            fn=cb_approve,
            inputs=[thread_id_state, feedback_box],
            outputs=[status_box, download_file, review_row],
        )

        reject_btn.click(
            fn=cb_reject,
            inputs=[thread_id_state, feedback_box],
            outputs=[status_box, report_md, download_file, review_row],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Base(),
        css=CSS,
    )
