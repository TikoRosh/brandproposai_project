from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from docx import Document
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from services.document_service import (
    ProposalData,
    create_docx,
    create_pdf,
    generate_proposal_html,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "app.db"
DOCS_DIR = BASE_DIR / "generated_docs"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="BrandProposAI RU",
    description="ИС формирования коммерческих предложений",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    company_name: str = Field(default="", max_length=255)
    prompt: str = Field(default="", max_length=5000)


class ExportRequest(BaseModel):
    generation_id: str | None = None
    company_name: str = Field(default="", max_length=255)
    prompt: str = Field(default="", max_length=5000)
    html_content: str = Field(default="", max_length=30000)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                html_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    DOCS_DIR.mkdir(exist_ok=True)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "1.html")


@app.get("/1.html")
def first_page():
    return FileResponse(STATIC_DIR / "1.html")


@app.get("/2.html")
def second_page():
    return FileResponse(STATIC_DIR / "2.html")


@app.get("/logo-header.png")
def logo_header():
    return FileResponse(STATIC_DIR / "logo-header.png")


@app.get("/logo.png")
def logo():
    return FileResponse(STATIC_DIR / "logo.png")


@app.post("/api/generate")
def generate(request: GenerateRequest):
    proposal_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    html_content = generate_proposal_html(
        request.company_name,
        request.prompt,
    )

    with db() as conn:
        conn.execute(
            """
            INSERT INTO proposals (
                id,
                company_name,
                prompt,
                html_content,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                request.company_name.strip() or "Клиент",
                request.prompt.strip(),
                html_content,
                now,
                now,
            ),
        )
        conn.commit()

    return {
        "id": proposal_id,
        "redirect": f"/2.html?id={proposal_id}",
        "html_content": html_content,
    }


@app.get("/api/proposals/{proposal_id}")
def get_proposal(proposal_id: str):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM proposals WHERE id = ?",
            (proposal_id,),
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Коммерческое предложение не найдено",
        )

    return dict(row)


@app.post("/api/proposals/{proposal_id}")
def update_proposal(proposal_id: str, request: ExportRequest):
    now = datetime.now().isoformat(timespec="seconds")

    with db() as conn:
        cur = conn.execute(
            """
            UPDATE proposals
            SET company_name = ?,
                prompt = ?,
                html_content = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                request.company_name.strip() or "Клиент",
                request.prompt.strip(),
                request.html_content,
                now,
                proposal_id,
            ),
        )
        conn.commit()

    if cur.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Коммерческое предложение не найдено",
        )

    return {"status": "ok", "updated_at": now}


def _filename(prefix: str, ext: str) -> Path:
    safe_prefix = "".join(
        ch for ch in prefix if ch.isalnum() or ch in (" ", "_", "-")
    )[:40].strip() or "proposal"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return DOCS_DIR / f"{safe_prefix}_{stamp}.{ext}"


@app.post("/api/export/docx")
def export_docx(request: ExportRequest):
    path = _filename(request.company_name, "docx")

    create_docx(
        path,
        ProposalData(
            request.company_name,
            request.prompt,
            request.html_content,
        ),
    )

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


@app.post("/api/export/pdf")
def export_pdf(request: ExportRequest):
    path = _filename(request.company_name, "pdf")

    create_pdf(
        path,
        ProposalData(
            request.company_name,
            request.prompt,
            request.html_content,
        ),
    )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")