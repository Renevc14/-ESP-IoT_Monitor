from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import require_admin

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", dependencies=[Depends(require_admin)])
async def list_audit_logs(
    action: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = "SELECT id, user_id, action, resource, ip_address, details, created_at FROM security.audit_logs"
    params: dict = {}
    if action:
        query += " WHERE action = :action"
        params["action"] = action
    query += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit
    rows = (await db.execute(text(query), params)).fetchall()
    return [
        {
            "id": r[0],
            "user_id": str(r[1]) if r[1] else None,
            "action": r[2],
            "resource": r[3],
            "ip_address": r[4],
            "details": r[5],
            "created_at": r[6].isoformat(),
        }
        for r in rows
    ]
