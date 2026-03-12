import datetime

import pytest
from sqlalchemy import text


@pytest.mark.integration
def test_readiness_engine_full_flow(db_engine):
    """
    End-to-end test for the readiness engine:
    1. Create a report
    2. Add a high-probability hazard prediction
    3. Trigger readiness recompute (via SQL update_readiness_scores)
    4. Verify readiness score and alerts
    """
    with db_engine.begin() as conn:
        # Pick a cell and a point inside it for the test
        cell = (
            conn.execute(
                text("""
            SELECT id, ST_X(ST_Centroid(geom::geometry)) as lon, ST_Y(ST_Centroid(geom::geometry)) as lat
            FROM public.grid_cells
            WHERE baseline_vulnerability IS NOT NULL
            LIMIT 1
        """)
            )
            .mappings()
            .first()
        )

        if not cell:
            pytest.skip("No grid cells with baseline vulnerability found for testing")

        cell_id = cell["id"]
        lon, lat = cell["lon"], cell["lat"]

        # Clear previous alerts/scores for this cell to ensure clean test
        conn.execute(
            text("DELETE FROM public.alerts WHERE cell_id = :cell_id"),
            {"cell_id": cell_id},
        )
        conn.execute(
            text("DELETE FROM public.readiness_scores WHERE cell_id = :cell_id"),
            {"cell_id": cell_id},
        )

        now = datetime.datetime.now(datetime.UTC)
        hour_ago = now - datetime.timedelta(hours=1)
        hour_hence = now + datetime.timedelta(hours=1)

        # Simulate the worker/AI by adding
        # a prediction at the cell centroid
        prediction_id = "00000000-0000-0000-0000-000000000002"
        # Ensure dummy prediction doesn't conflict
        conn.execute(
            text("DELETE FROM public.hazard_predictions WHERE id = :id"),
            {"id": prediction_id},
        )

        conn.execute(
            text("""
            INSERT INTO public.hazard_predictions (id, geom, prediction_type, probability, created_at, valid_from, valid_until)
            VALUES (:id, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography, 'flood', 0.95, now(), :start, :end)
        """),
            {
                "id": prediction_id,
                "lon": lon,
                "lat": lat,
                "start": hour_ago,
                "end": hour_hence,
            },
        )

        # Simulate the recompute (normally triggered by SQLPostProcessingHooks in the API)
        conn.execute(
            text("SELECT public.update_readiness_scores(:cell_id)"),
            {"cell_id": cell_id},
        )

        # Trigger alerts (normally triggered by SQLPostProcessingHooks)
        conn.execute(
            text("SELECT public.raise_alert_if_low_readiness(:cell_id, 100)"),
            {"cell_id": cell_id},
        )
        conn.execute(
            text("SELECT public.raise_alert_for_severe_hazard(:pred_id, :cell_id)"),
            {"pred_id": prediction_id, "cell_id": cell_id},
        )

        # Check readiness score exists and has a breakdown
        score_row = (
            conn.execute(
                text("""
            SELECT score, breakdown, coverage_confidence
            FROM public.readiness_scores
            WHERE cell_id = :cell_id
        """),
                {"cell_id": cell_id},
            )
            .mappings()
            .first()
        )

        assert score_row is not None
        assert score_row["score"] < 100  # Should be reduced by the hazard
        assert "hazard_count" in score_row["breakdown"]
        assert score_row["breakdown"]["hazard_count"] >= 1

        # Check alerts generated
        alerts = conn.execute(
            text("""
            SELECT message FROM public.alerts
            WHERE cell_id = :cell_id
            ORDER BY triggered_at ASC
        """),
            {"cell_id": cell_id},
        ).fetchall()

        assert len(alerts) >= 1
        messages = [a[0] for a in alerts]
        assert any("Readiness dropped" in msg for msg in messages)
        assert any("Severe flood detected" in msg for msg in messages)

        # Cleanup test data
        conn.execute(
            text("DELETE FROM public.hazard_predictions WHERE id = :id"),
            {"id": prediction_id},
        )
        # Leave the score for visual verification
        conn.execute(
            text("DELETE FROM public.alerts WHERE cell_id = :cell_id"),
            {"cell_id": cell_id},
        )
