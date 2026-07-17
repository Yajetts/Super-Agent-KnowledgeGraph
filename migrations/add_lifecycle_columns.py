"""Migration script to add lifecycle management columns to dynamic_agents table."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from sqlalchemy import create_engine, text


def add_lifecycle_columns() -> None:
    """Add last_used, success_score, and relevance_score columns to dynamic_agents table."""
    settings = get_settings()
    db_url = (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'dynamic_agents'
            AND column_name IN ('last_used', 'success_score', 'relevance_score')
        """))
        existing_columns = {row[0] for row in result}

        # Add last_used column if it doesn't exist
        if 'last_used' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE dynamic_agents
                ADD COLUMN last_used TIMESTAMP
            """))
            print("Added last_used column")
        else:
            print("last_used column already exists")

        # Add success_score column if it doesn't exist
        if 'success_score' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE dynamic_agents
                ADD COLUMN success_score FLOAT DEFAULT 1.0
            """))
            print("Added success_score column")
        else:
            print("success_score column already exists")

        # Add relevance_score column if it doesn't exist
        if 'relevance_score' not in existing_columns:
            conn.execute(text("""
                ALTER TABLE dynamic_agents
                ADD COLUMN relevance_score FLOAT DEFAULT 1.0
            """))
            print("Added relevance_score column")
        else:
            print("relevance_score column already exists")

        conn.commit()
        print("Migration completed successfully")


if __name__ == "__main__":
    add_lifecycle_columns()
