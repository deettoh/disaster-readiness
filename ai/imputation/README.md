# Risk Imputation Model

This module implements a machine learning pipeline to build the **baseline vulnerability score** for each grid cell in Petaling Jaya. It uses geographical features to estimate disaster risk in areas where historical damage data may be sparse.

## Pipeline

Data Loading (SRTM, Hotspots, Waterways, Accessibility) -> Feature Extraction -> Proxy Label Construction -> XGBoost Training (with W&B Tracking) -> Model Artifacts & DB Writeback

## Components

### Feature Extraction

The model derives features from multiple geospatial sources:

- **Elevation & Slope**: Extracted from SRTM GL1 (30m) raster data.
- **Proximity**: Minimum distance to nearest waterways (OSM) and historical flood hotspots (JPS).
- **Accessibility**: Road density and average travel time to the nearest shelter.

### Model

- **Algorithm**: XGBoost Regressor
- **Experiment Tracking**: Weights & Biases (wandb)
**Target:** Per-grid-cell `vulnerability_score` (0–1), written to `grid_cells.baseline_vulnerability`.

## Vulnerability Proxy

Since real world flood damage labels are unavailable at scale, the model is trained on a synthetic **Proxy Label** calculated as:

```
vulnerability = (0.50 * hotspot_proximity) + (0.25 * low_elevation) + (0.25 * river_proximity)
```

- **Hotspot Proximity**: Decays linearly from max score within 500m to zero at 2km.
- **Low Elevation**: Normalized inverse of elevation (lower = higher risk).
- **River Proximity**: Decays linearly over 1km from the bank.

## Output

The model and its associated metadata are stored in separate directories:

- **Model**: `ai/imputation/models/`
    - `vulnerability_model.joblib`: The trained XGBoost model.
- **Artifacts**: `ai/imputation/artifacts/`
    - `cell_predictions.csv`: Predicted scores for integration into the spatial database.
    - `training_metrics.json`: Detailed performance metrics and model limitations.
    - `feature_importance.json`: Gain-based importance scores for input features.
    - `imputation_features.csv`: Full feature table used for training/inference.

## Data Requirements

To train or run the model, the following datasets must be present in `data/external/` (not tracked in Git due to size constraints):

| Dataset | Source | Location / File Pattern |
| :--- | :--- | :--- |
| **SRTM Elevation** | [ArduPilot Terrain Generator](https://terrain.ardupilot.org/SRTM3/Eurasia/) | `data/external/N03E101.hgt` |
| **Waterways** | [HOTOSM Malaysia](https://data.humdata.org/) | `data/external/*waterways_lines*.geojson` |
| **Flood Hotspots** | JPS Malaysia | `ai/imputation/data/pj_hotspots.csv` |
| **Accessibility** | Internal `routing` module | `routing/artifacts/cell_accessibility_handoff.csv` |

## Model Training

The baseline model was trained with the following hyperparameters:

- **n_estimators**: 200
- **max_depth**: 5
- **learning_rate**: 0.1
- **subsample**: 0.8
- **random_state**: 42

### Feature Importance (Gain)

1. **dist_to_hotspot_m** (Highest impact)
2. **mean_elevation**
3. **dist_to_river_m**
4. **road_density**
5. **travel_time_to_shelter_s**

## Running the Model

The main runner script is now part of the module. Run it from the project root using `poetry`:

```bash
# Inference only (saves to artifacts/)
poetry run python ai/imputation/scripts/run_imputation.py

# Inference + Write to Database
poetry run python ai/imputation/scripts/run_imputation.py --write-db

# Full check (Write + Verify)
poetry run python ai/imputation/scripts/run_imputation.py --write-db --verify

# Generate sanity check map
poetry run python ai/imputation/scripts/visualize_results.py
```

## Limitations

- **Proxy Labels**: The model learns a theoretical risk formula rather than actual historical damage.
- **Resolution**: SRTM 30m resolution may not capture micro-topography in dense urban environments.
- **Regionality**: Currently optimized for Petaling Jaya (PJ) and requires retraining for other regions.
