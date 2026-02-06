import sqlalchemy as sa

from app.db.base import Base
from app.db.session import engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def _project_columns(sync_conn) -> set[str]:
            inspector = sa.inspect(sync_conn)
            if not inspector.has_table("projects"):
                return set()
            return {col["name"] for col in inspector.get_columns("projects")}

        project_columns = await conn.run_sync(_project_columns)
        if not project_columns:
            return

        dialect = conn.dialect.name

        # Self-heal for old DB volumes created before `projects.key` existed.
        if "key" not in project_columns:
            await conn.execute(sa.text("ALTER TABLE projects ADD COLUMN key VARCHAR(20)"))

        if dialect == "postgresql":
            await conn.execute(
                sa.text("""
                    UPDATE projects
                    SET key = CONCAT('PRJ', id)
                    WHERE key IS NULL
                """)
            )
            await conn.execute(
                sa.text("ALTER TABLE projects ALTER COLUMN key SET NOT NULL")
            )
        else:
            await conn.execute(
                sa.text("""
                    UPDATE projects
                    SET key = 'PRJ' || id
                    WHERE key IS NULL
                """)
            )

        await conn.execute(
            sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_key ON projects (key)")
        )
