"""Runner script for the risk imputation model.

Usage:
    poetry run python ai/imputation/scripts/run_imputation.py
    poetry run python ai/imputation/scripts/run_imputation.py --write-db
    poetry run python ai/imputation/scripts/run_imputation.py --write-db --verify
    poetry run python ai/imputation/scripts/run_imputation.py --dry-run

Inference loads the trained model from ai/imputation/models/ and predicts
vulnerability scores saved to ai/imputation/artifacts/cell_predictions.csv.
Training is handled in the Jupyter notebook (ai/imputation/notebook/).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from ai.imputation.src.risk_imputation.db_writeback import (
    run_writeback,
    verify_writeback,
)
from ai.imputation.src.risk_imputation.inference import run_inference
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Risk Imputation Model runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="Write predictions to grid_cells.baseline_vulnerability in db",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="After DB write, read back and display top cells to verify",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be written to db without actually writing",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Custom path to model .joblib file",
    )
    parser.add_argument(
        "--features-path",
        type=Path,
        default=None,
        help="Custom path to features CSV",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Custom path to save predictions CSV",
    )
    return parser.parse_args()


def main() -> None:
    """Run the imputation model pipeline."""
    args = parse_args()

    logger.info("Running inference...")
    predictions = run_inference(
        project_root=PROJECT_ROOT,
        model_path=args.model_path,
        features_path=args.features_path,
        output_path=args.output_path,
    )
    logger.info("Inference complete: %d cell predictions", len(predictions))

    if args.write_db or args.dry_run:
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            logger.error("DATABASE_URL not set. Cannot write to DB.")
            sys.exit(1)

        logger.info(
            "Writing predictions to DB%s...", " (DRY RUN)" if args.dry_run else ""
        )
        updated = run_writeback(
            project_root=PROJECT_ROOT,
            database_url=database_url,
            dry_run=args.dry_run,
        )
        logger.info("DB writeback complete: %d cells updated", updated)

        if args.verify and not args.dry_run:
            logger.info("Verifying writeback...")
            top_cells = verify_writeback(database_url)
            logger.info("Top vulnerable cells after writeback:")
            for _, row in top_cells.iterrows():
                logger.info(
                    "  Cell %d: vulnerability = %.3f",
                    row["id"],
                    row["baseline_vulnerability"],
                )
    elif not args.write_db:
        logger.info(
            "Predictions saved to CSV only. Use --write-db to write to database."
        )


if __name__ == "__main__":
    main()
