"""Bulk initialize readiness scores for all grid cells."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")


def bulk_initialize() -> None:
    """Bulk initialize readiness scores for all grid cells by calling SQL functions."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in environment.")
        sys.exit(1)

    print("Connecting to database...")
    engine = create_engine(db_url)

    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT id FROM public.grid_cells ORDER BY id"))
            cell_ids = [row[0] for row in result]

            if not cell_ids:
                print(
                    "No grid cells found in public.grid_cells. Please run grid generation first."
                )
                return

            print(f"Found {len(cell_ids)} cells. Starting bulk recompute...")

            count = 0
            for cell_id in cell_ids:
                conn.execute(
                    text("SELECT public.update_readiness_scores(:id)"), {"id": cell_id}
                )
                count += 1
                if count % 50 == 0:
                    print(f"  Processed {count}/{len(cell_ids)} cells...")

            print(f"SUCCESS: {count} readiness scores initialized/updated.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    bulk_initialize()
