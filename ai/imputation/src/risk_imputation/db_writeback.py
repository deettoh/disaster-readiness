"""DB writeback module for the risk imputation model.

Writes predicted vulnerability scores back to the grid_cells table
in Supabase/PostGIS.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

DEFAULT_PREDICTIONS_PATH = Path("ai/imputation/artifacts/cell_predictions.csv")


def write_predictions_to_db(
    predictions: pd.DataFrame,
    database_url: str,
    *,
    engine: Engine | None = None,
    dry_run: bool = False,
) -> int:
    """Write predicted vulnerability scores to grid_cells.baseline_vulnerability.

    Args:
        predictions: DataFrame with columns [cell_id, predicted_vulnerability].
        database_url: PostgreSQL connection string.
        engine: Optional preexisting SQLAlchemy engine (overrides database_url).
        dry_run: If True, log what would be written but do not execute.

    Returns:
        Number of cells updated.
    """
    if (
        "cell_id" not in predictions.columns
        or "predicted_vulnerability" not in predictions.columns
    ):
        msg = "predictions must have columns [cell_id, predicted_vulnerability]"
        raise ValueError(msg)

    db_engine = engine or create_engine(database_url)
    updated = 0

    with db_engine.begin() as conn:
        for _, row in predictions.iterrows():
            cell_id = int(row["cell_id"])
            score = round(float(row["predicted_vulnerability"]), 3)

            if dry_run:
                logger.info("[DRY RUN] Would set cell %d -> %.3f", cell_id, score)
                updated += 1
                continue

            result = conn.execute(
                text(
                    "UPDATE grid_cells "
                    "SET baseline_vulnerability = :score "
                    "WHERE id = :cell_id"
                ),
                {"score": score, "cell_id": cell_id},
            )
            if result.rowcount > 0:
                updated += 1

    logger.info(
        "%s %d cells in grid_cells.baseline_vulnerability",
        "Would update" if dry_run else "Updated",
        updated,
    )
    return updated


def verify_writeback(
    database_url: str, *, engine: Engine | None = None, limit: int = 10
) -> pd.DataFrame:
    """Read back a sample of grid_cells to verify baseline_vulnerability was written.

    Args:
        database_url: PostgreSQL connection string.
        engine: Optional preexisting SQLAlchemy engine.
        limit: Number of rows to return.

    Returns:
        DataFrame with columns [id, baseline_vulnerability].
    """
    db_engine = engine or create_engine(database_url)
    with db_engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT id, baseline_vulnerability "
                "FROM grid_cells "
                "WHERE baseline_vulnerability IS NOT NULL "
                "ORDER BY baseline_vulnerability DESC "
                "LIMIT :limit"
            ),
            {"limit": limit},
        )
        rows = result.fetchall()

    df = pd.DataFrame(rows, columns=["id", "baseline_vulnerability"])
    logger.info("Verified %d cells with non-NULL vulnerability", len(df))
    return df


def run_writeback(
    project_root: Path,
    database_url: str,
    *,
    predictions_path: Path | None = None,
    dry_run: bool = False,
) -> int:
    """End to end writeback: load predictions CSV and write to DB.

    Args:
        project_root: Project root directory.
        database_url: PostgreSQL connection string.
        predictions_path: Path to predictions CSV. Defaults to standard location.
        dry_run: If True, log without writing.

    Returns:
        Number of cells updated.
    """
    _predictions_path = predictions_path or (project_root / DEFAULT_PREDICTIONS_PATH)

    if not _predictions_path.exists():
        msg = f"Predictions file not found: {_predictions_path}. Run inference first."
        raise FileNotFoundError(msg)

    predictions = pd.read_csv(_predictions_path)
    logger.info("Loaded %d predictions from %s", len(predictions), _predictions_path)

    return write_predictions_to_db(predictions, database_url, dry_run=dry_run)
