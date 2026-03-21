-- ============================================================
-- Migration 05: Security audit log (OWASP A09)
-- ============================================================

CREATE TABLE security.audit_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action      VARCHAR(100) NOT NULL,
    resource    VARCHAR(255),
    ip_address  VARCHAR(45),
    details     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON security.audit_logs (user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON security.audit_logs (action, created_at DESC);
