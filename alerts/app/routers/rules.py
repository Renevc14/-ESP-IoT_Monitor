import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.dependencies import require_admin, require_operator
from app.models.alert import AlertRule
from app.schemas.rule import AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate

router = APIRouter(prefix="/alert-rules", tags=["Alert Rules"])


def _session_factory(request: Request) -> async_sessionmaker:
    return request.app.state.session_factory


@router.get("", response_model=list[AlertRuleResponse])
async def list_rules(
    device_id: uuid.UUID | None = Query(None),
    sf: async_sessionmaker = Depends(_session_factory),
    _=Depends(require_operator),
):
    async with sf() as s:
        q = select(AlertRule).order_by(AlertRule.created_at)
        if device_id:
            q = q.where(AlertRule.device_id == device_id)
        return (await s.execute(q)).scalars().all()


@router.post("", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    body: AlertRuleCreate,
    sf: async_sessionmaker = Depends(_session_factory),
    _=Depends(require_admin),
):
    async with sf() as s:
        rule = AlertRule(
            device_id=body.device_id,
            sensor_type=body.sensor_type,
            operator=body.operator,
            threshold=body.threshold,
            severity=body.severity,
            notification_emails=body.notification_emails,
        )
        s.add(rule)
        await s.commit()
        await s.refresh(rule)
        return rule


@router.patch("/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    body: AlertRuleUpdate,
    sf: async_sessionmaker = Depends(_session_factory),
    _=Depends(require_admin),
):
    async with sf() as s:
        rule = await s.get(AlertRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(rule, field, value)
        await s.commit()
        await s.refresh(rule)
        return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: uuid.UUID,
    sf: async_sessionmaker = Depends(_session_factory),
    _=Depends(require_admin),
):
    async with sf() as s:
        rule = await s.get(AlertRule, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        await s.delete(rule)
        await s.commit()
