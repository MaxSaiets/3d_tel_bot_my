#!/bin/sh
set -e

echo "Waiting for database..."
until python3 -c "
import asyncio, asyncpg, os, sys
async def check():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    try:
        conn = await asyncpg.connect(url)
        await conn.close()
        print('DB ready')
    except Exception as e:
        print(f'DB not ready: {e}')
        sys.exit(1)
asyncio.run(check())
"; do
  echo "DB not ready, retrying in 3s..."
  sleep 3
done

echo "Running migrations (with advisory lock)..."
python3 - <<'PYEOF'
import asyncio, asyncpg, os, subprocess, sys

async def migrate():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    # Acquire exclusive advisory lock (key=777777) to prevent concurrent migrations
    acquired = await conn.fetchval("SELECT pg_try_advisory_lock(777777)")
    if not acquired:
        print("Another instance is running migrations, waiting...")
        # Wait for lock to be released (other instance finished)
        await conn.fetchval("SELECT pg_advisory_lock(777777)")
        await conn.fetchval("SELECT pg_advisory_unlock(777777)")
        await conn.close()
        print("Migration done by other instance, skipping.")
        return
    try:
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    finally:
        await conn.fetchval("SELECT pg_advisory_unlock(777777)")
        await conn.close()

asyncio.run(migrate())
PYEOF

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
