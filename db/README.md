# Database Migrations

Run these scripts against your Supabase project in order.

## Prerequisites

1. Create a Supabase project at https://supabase.com
2. Enable the TimescaleDB extension in your Supabase project:
   - Go to: Database → Extensions → Search "timescaledb" → Enable

## Run Migrations

### Option A — Supabase SQL Editor

Open each file and paste its contents into the Supabase SQL Editor, running them in order:

1. `01_schemas.sql`
2. `02_auth_tables.sql`
3. `03_iot_tables.sql`
4. `04_alerts_tables.sql`
5. `05_security_tables.sql`
6. `06_seed_data.sql`

### Option B — psql CLI

```bash
# Get your DATABASE_URL from Supabase Dashboard → Settings → Database → URI
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"

psql "$DATABASE_URL" -f 01_schemas.sql
psql "$DATABASE_URL" -f 02_auth_tables.sql
psql "$DATABASE_URL" -f 03_iot_tables.sql
psql "$DATABASE_URL" -f 04_alerts_tables.sql
psql "$DATABASE_URL" -f 05_security_tables.sql
psql "$DATABASE_URL" -f 06_seed_data.sql
```

## After Migrations

Update your `.env` file with the Supabase connection string:

```env
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
```
