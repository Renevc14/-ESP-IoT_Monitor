import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies import require_admin, require_operator
from app.models.device import AlertRule, Device
from app.schemas.device import AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate

router = APIRouter(prefix="/alert-rules", tags=["Alert Rules"])


@router.get("", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    device_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_operator),
):
    stmt = select(AlertRule).order_by(AlertRule.created_at)
    if device_id:
        stmt = stmt.where(AlertRule.device_id == device_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    body: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    # Verify device exists
    device = await db.get(Device, body.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    rule = AlertRule(
        device_id=body.device_id,
        sensor_type=body.sensor_type,
        operator=body.operator,
        threshold=body.threshold,
        severity=body.severity,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: uuid.UUID,
    body: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    rule = await db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    rule = await db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    await db.delete(rule)
    await db.commit()
