"""Run canonical cell_accessibility compute and export handoff CSV."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from apps.api.src.app.core.config import get_settings  # noqa: E402
from dotenv import load_dotenv

from routing.sql.accessibility import AccessibilityManager  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parents[2]
API_SRC = ROOT_DIR / "apps" / "api" / "src"
for path in (str(ROOT_DIR), str(API_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

load_dotenv(ROOT_DIR / ".env")


def _default_database_url() -> str:
    """Resolve DATABASE_URL from env first, then .env-backed app settings."""
    # Direct OS environment variable
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    # Pydantic Settings
    try:
        settings = get_settings()
        url = settings.database_url
        # Ensure url is a string and not the placeholder before returning
        if isinstance(url, str) and "YOUR_PROJECT_REF" not in url:
            return url
    except Exception:
        pass

    # Priority 3: Local Supabase CLI Fallback (Ensures a str is always returned)
    return "postgresql://postgres:postgres@127.0.0.1:54322/postgres"


def parse_args() -> argparse.Namespace:
    """Parse script arguments."""
    default_db_url = _default_database_url()
    parser = argparse.ArgumentParser(
        description="Compute public.cell_accessibility and export handoff CSV."
    )
    parser.add_argument(
        "--database-url",
        default=default_db_url,
        help="Postgres URL used for routing/readiness tables.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT_DIR / "routing/artifacts/cell_accessibility_handoff.csv"),
        help="Output CSV path for handoff to Member B.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Compute and verify only.",
    )
    return parser.parse_args()


def main() -> None:
    """Run accessibility compute, verification, and CSV export."""
    args = parse_args()
    if not args.database_url:
        raise RuntimeError("missing database URL; set --database-url or DATABASE_URL")

    manager = AccessibilityManager(database_url=args.database_url)
    total = manager.compute_accessibility()
    summary = manager.verify_metrics()

    print("Accessibility compute job passed.")
    print(f"Rows in public.cell_accessibility: {total}")
    print(f"Rows with travel time: {summary.with_travel_time}")
    print(f"Rows with road density: {summary.with_density}")

    if not args.skip_export:
        output_path = manager.export_handoff_csv(Path(args.output))
        print(f"Handoff CSV written: {output_path}")


if __name__ == "__main__":
    main()
