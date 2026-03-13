# Frontend (React + MapLibre)

The `apps/frontend/` directory contains the web-first React application for the Hyperlocal Disaster Readiness platform. It provides an interactive map dashboard, hazard report submission flow, readiness/alert panels, and evacuation routing, optimized for mobile browsers.

## Tech Stack

- **React** (Vite build tool)
- **MapLibre GL JS** for interactive map layers
- **Vanilla CSS** for styling
- **Vite** dev server with HMR

## Source Layout

```
apps/frontend/src/
├── App.jsx                 # Root app with map + panel layout
├── main.jsx                # React DOM entry
├── index.css               # Global styles
├── api/
│   ├── config.js           # API base URL config
│   └── route.js            # Route API client
├── components/
│   ├── MapView.jsx         # Core map with readiness/hazard/shelter layers
│   ├── LegendPanel.jsx     # Map legend overlay
│   ├── layerController.js  # Map layer toggle logic
│   ├── panels/             # Side panels (ReadinessPanel, AlertPanel, RoutePanel, HazardPanel)
│   └── report/             # Report submission flow components
├── mock/                   # Mock data for development
└── utils/
    └── geojson.js          # GeoJSON feature helpers
```

## Key Components

| Component | Purpose |
| --- | --- |
| `MapView.jsx` | Renders the MapLibre map with readiness choropleth, hazard markers, shelter pins, and route polylines |
| `ReadinessPanel.jsx` | Displays 0 to 100 readiness score with color-coded breakdown bars |
| `AlertPanel.jsx` | Lists active alerts with click-to-zoom interaction |
| `RoutePanel.jsx` | Shelter selection and route computation UI |
| `HazardPanel.jsx` | Hazard details with redacted image preview |
| `ReportFlow` | Camera/file upload + geolocation + pin-drop submission flow |

## Environment

Create `.env.local` in this directory:

```dotenv
VITE_API_BASE_URL=/api/v1
VITE_MAPTILER_KEY=YOUR_MAPTILER_KEY
VITE_USE_MOCK=false
```

## Running

### Development

```bash
cd apps/frontend && npm install && npm run dev
```

The dev server starts on `http://localhost:5173` with hot reload. The Vite config auto-syncs `routing/artifacts/pj_shelters.csv` into `public/` on build/dev start.

### Docker

```bash
docker compose --profile frontend up --build
```

Serves the production build via Nginx at `http://localhost:3000`.

## Data Requirements

| Dataset | Source | Format | Description |
| :--- | :--- | :--- | :--- |
| **Petaling Jaya Neighbourhoods** | [Overpass Turbo](https://overpass-turbo.eu/) | `.geojson` | Used to process Petaling Jaya into smaller sub-areas of neighbourhood cells for the readiness choropleth layer |

## Map Layers

The map renders the following data layers, all fetched from the backend API:

1. **Readiness choropleth** — neighborhood polygons colored by readiness score (0 to 100)
2. **Hazard markers** — reported hazard locations with type icons
3. **Shelter markers** — evacuation shelter points from CSV
4. **Route polyline** — computed evacuation route from pgRouting

See [apps/api/README.md](../api/README.md) for the backend endpoints that supply this data.
