from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File

from app.services.sql_client import sql_client, _bind
from app.services.role_auth import require_permission, require_role, AuthenticatedUser

router = APIRouter(prefix="/documents", tags=["documents"])

CHUNK_SIZE = 500


def _chunk_text(text: str) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 1 > CHUNK_SIZE and current:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Query("general", description="Document category"),
    member_id: str | None = Query(None, description="Associated member ID"),
    user: AuthenticatedUser = Depends(
        require_role("SNOWCARE_ADMIN_ROLE", "CARE_MANAGER_ROLE", "PHYSICIAN_ROLE")
    ),
):
    filename = file.filename or "untitled"
    doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "txt":
        raw = await file.read()
        content_text = raw.decode("utf-8", errors="replace")
    elif ext == "pdf":
        await file.read()
        content_text = f"[PDF content from {filename} — parsing simulated for hackathon demo]"
    else:
        raw = await file.read()
        content_text = raw.decode("utf-8", errors="replace")

    insert_doc = """
        INSERT INTO DOCUMENT (DOCUMENT_ID, FILE_NAME, CATEGORY, MEMBER_ID, CONTENT_TEXT, PROCESSING_STATUS)
        VALUES (?, ?, ?, ?, ?, 'processing')
    """
    try:
        await sql_client.execute(insert_doc, bindings=_bind([doc_id, filename, category, member_id, content_text]))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc

    chunks = _chunk_text(content_text)
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}-C{i:04d}"
        insert_chunk = """
            INSERT INTO DOCUMENT_CHUNK (CHUNK_ID, DOCUMENT_ID, CHUNK_INDEX, CONTENT_TEXT)
            VALUES (?, ?, ?, ?)
        """
        try:
            await sql_client.execute(insert_chunk, bindings=_bind([chunk_id, doc_id, i, chunk]))
        except Exception:
            pass

    try:
        await sql_client.execute(
            "UPDATE DOCUMENT SET PROCESSING_STATUS = 'completed' WHERE DOCUMENT_ID = ?",
            bindings=_bind([doc_id]),
        )
    except Exception:
        pass

    return {
        "document_id": doc_id,
        "file_name": filename,
        "category": category,
        "member_id": member_id,
        "chunk_count": len(chunks),
        "processing_status": "completed",
    }


@router.get("")
async def list_documents(
    category: str | None = Query(None),
    member_id: str | None = Query(None),
    processing_status: str | None = Query(None),
    user: AuthenticatedUser = Depends(require_permission),
):
    conditions: list[str] = []
    params: list = []
    if category:
        conditions.append("CATEGORY = ?")
        params.append(category)
    if member_id:
        conditions.append("MEMBER_ID = ?")
        params.append(member_id)
    if processing_status:
        conditions.append("PROCESSING_STATUS = ?")
        params.append(processing_status)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT DOCUMENT_ID, FILE_NAME, CATEGORY, MEMBER_ID, PROCESSING_STATUS,
               TO_VARCHAR(INGESTED_AT, 'YYYY-MM-DD HH24:MI') AS INGESTED_AT
        FROM DOCUMENT{where}
        ORDER BY INGESTED_AT DESC
    """
    try:
        rows = await sql_client.execute(sql, bindings=_bind(params) if params else None)
        return [
            {
                "document_id": r["DOCUMENT_ID"],
                "file_name": r.get("FILE_NAME", ""),
                "category": r.get("CATEGORY", ""),
                "member_id": r.get("MEMBER_ID"),
                "processing_status": r.get("PROCESSING_STATUS", ""),
                "ingested_at": r.get("INGESTED_AT", ""),
            }
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    user: AuthenticatedUser = Depends(require_permission),
):
    try:
        doc_rows = await sql_client.execute(
            "SELECT DOCUMENT_ID, FILE_NAME, CATEGORY, MEMBER_ID, CONTENT_TEXT, PROCESSING_STATUS, "
            "TO_VARCHAR(INGESTED_AT, 'YYYY-MM-DD HH24:MI') AS INGESTED_AT "
            "FROM DOCUMENT WHERE DOCUMENT_ID = ?",
            bindings=_bind([document_id]),
        )
        if not doc_rows:
            raise HTTPException(status_code=404, detail="Document not found")
        d = doc_rows[0]

        chunk_rows = await sql_client.execute(
            "SELECT CHUNK_ID, CHUNK_INDEX, CONTENT_TEXT "
            "FROM DOCUMENT_CHUNK WHERE DOCUMENT_ID = ? ORDER BY CHUNK_INDEX",
            bindings=_bind([document_id]),
        )

        return {
            "document_id": d["DOCUMENT_ID"],
            "file_name": d.get("FILE_NAME", ""),
            "category": d.get("CATEGORY", ""),
            "member_id": d.get("MEMBER_ID"),
            "content_text": d.get("CONTENT_TEXT", ""),
            "processing_status": d.get("PROCESSING_STATUS", ""),
            "ingested_at": d.get("INGESTED_AT", ""),
            "chunks": [
                {
                    "chunk_id": c["CHUNK_ID"],
                    "chunk_index": int(c["CHUNK_INDEX"]),
                    "chunk_text": c.get("CONTENT_TEXT", ""),
                }
                for c in chunk_rows
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user: AuthenticatedUser = Depends(
        require_role("SNOWCARE_ADMIN_ROLE", "CARE_MANAGER_ROLE", "PHYSICIAN_ROLE")
    ),
):
    try:
        await sql_client.execute(
            "DELETE FROM DOCUMENT_CHUNK WHERE DOCUMENT_ID = ?",
            bindings=_bind([document_id]),
        )
        await sql_client.execute(
            "DELETE FROM DOCUMENT WHERE DOCUMENT_ID = ?",
            bindings=_bind([document_id]),
        )
        return {"status": "deleted", "document_id": document_id}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database error: {exc}") from exc
