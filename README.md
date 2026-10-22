## Cyber Cyclone 3D
## The combination of a 3D-Globe, a 3D-Network topology
Table of Contents
Overview
Features
Architecture
Tech Stack
Project Structure
Getting Started
Configuration
API Reference
WebSocket Events
Roadmap
Contributing
License
Overview

[PROJECT_NAME] gives security teams one place to see what is happening across their network and the wider threat landscape. Instead of jumping between scanners, spreadsheets, and CVE databases, everything is shown visually and updated in real time:

The 3D globe shows where assets, vendors, and vulnerability activity are located around the world.
The 3D topology map shows how devices on the network connect, and highlights nodes affected by known CVEs.
The live monitoring feed streams new and updated CVEs, matches them against the asset inventory, and raises alerts by severity.
Features
🌍 3D Globe
Interactive, rotatable Earth built with Three.js / React Three Fiber
Asset and event markers plotted by location
Animated arcs showing connections between regions
Color-coded markers by CVSS severity (Critical / High / Medium / Low)
Click a marker to open asset or CVE details
🕸️ 3D Network Topology Map
Force-directed 3D graph of hosts, routers, switches, servers, and services
Nodes glow or pulse when tied to an active vulnerability
Filter by subnet, device type, or severity
Click a node to see open CVEs, software versions, and connected neighbors
⚡ Real-Time Security Monitoring
Continuous ingestion of CVE data (NVD / CVE feeds)
Automatic matching of CVEs to assets by vendor, product, and version (CPE)
Live alert stream pushed to the browser over WebSockets
Severity scoring using CVSS v3.x / v4.0
Dashboard stats: total open CVEs, critical count, newly published, recently patched
Architecture
┌──────────────────────┐        ┌───────────────────────────────┐
│   CVE Data Sources    │        │  Hybrid Python + Rust Backend  │
│  (NVD API / CVE feeds)│──────▶│  ┌─────────────┐  ┌──────────┐ │
└──────────────────────┘        │  │  Ingestor   │─▶│ Matcher  │ │
                                │  └─────────────┘  └────┬─────┘ │
┌──────────────────────┐        │         │              │       │
│   Asset Inventory     │──────▶│         ▼              ▼       │
│ (hosts, software, CPE)│        │  ┌─────────────────────────┐   │
└──────────────────────┘        │  │   Database / Cache       │   │
                                │  └───────────┬─────────────┘   │
                                │              ▼                 │
                                │  ┌─────────────────────────┐   │
                                │  │ FastAPI REST + WebSocket │   │
                                │  └───────────┬─────────────┘   │
                                └──────────────┼─────────────────┘
                                               │
                                               ▼
                                ┌─────────────────────────────────┐
                                │   React + React Three Fiber UI   │
                                │  3D Globe │ 3D Topology │ Alerts │
                                └─────────────────────────────────┘

Flow:

The Ingestor polls CVE sources on a schedule and stores new/updated entries.
The Matcher compares CVEs against the asset inventory.
Matches become alerts, saved to the database and broadcast through the WebSocket hub.
The frontend updates the globe, topology map, and alert feed live.
Tech Stack
Layer	Technology
Frontend	React, Three.js, React Three Fiber, @react-three/drei
Backend	Python (FastAPI, Uvicorn, WebSockets) + Rust core (PyO3, built with maturin)
Data	NVD CVE API 2.0 / CVE JSON feeds
Database	[PostgreSQL / SQLite — TBD]
Cache	[Redis — optional, TBD]
DevOps	Docker, Docker Compose
Project Structure
[PROJECT_NAME]/
├── rust_telemetry/              # Rust core (PyO3 extension module)
│   ├── src/lib.rs               # TelemetryFrame + process_raw_packet
│   ├── Cargo.toml
│   └── pyproject.toml
├── main.py                      # FastAPI app + WebSocket broadcaster
├── test_telemetry.py            # Rust/Python boundary tests
├── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Globe/           # 3D globe scene
│   │   │   ├── Topology/        # 3D network graph
│   │   │   └── AlertFeed/       # live alert panel
│   │   ├── hooks/               # useWebSocket, etc.
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
Getting Started
Prerequisites
Python 3.10+
Rust toolchain (stable, via rustup)
Node.js 20+ and npm
(Optional) Docker + Docker Compose
(Recommended) An NVD API key for higher rate limits
1. Clone the repo
bash
git clone https://github.com/[USERNAME]/[PROJECT_NAME].git
cd [PROJECT_NAME]
2. Set up environment variables
bash
cp .env.example .env
# then edit .env and add your values
3. Run the backend
bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd rust_telemetry && maturin develop --release && cd ..
pytest -q test_telemetry.py   # optional: verify Rust boundary safety
python main.py

Backend runs at http://localhost:8000.

4. Run the frontend
bash
cd frontend
npm install
npm run dev

Frontend runs at http://localhost:5173.

Or run everything with Docker
bash
docker compose up --build
Configuration
Variable	Description	Default
PORT	Backend server port	8000
NVD_API_KEY	NVD API key	(none)
CVE_POLL_INTERVAL	How often to pull new CVEs	15m
DATABASE_URL	Database connection string	(required)
ALLOWED_ORIGINS	CORS origins for the frontend	http://localhost:5173
VITE_API_URL	Backend URL used by the frontend	http://localhost:8000
VITE_WS_URL	WebSocket URL used by the frontend	ws://localhost:8000/v1/telemetry/stream
API Reference
Method	Endpoint	Description
GET	/api/health	Health check
GET	/api/cves	List CVEs (filter by severity/date)
GET	/api/cves/{id}	Get one CVE by ID
GET	/api/assets	List assets in inventory
GET	/api/topology	Nodes + edges for the 3D map
GET	/api/alerts	List recent alerts
GET	/api/stats	Dashboard summary numbers
WebSocket Events

Connect to ws://localhost:8000/v1/telemetry/stream.

Event	Direction	Payload (example)
cve.new	server → client	{ "id": "CVE-2026-12345", "cvss": 9.8, "severity": "CRITICAL" }
alert.new	server → client	{ "assetId": "srv-01", "cveId": "CVE-2026-12345", "severity": "CRITICAL" }
topology.update	server → client	{ "nodes": [...], "edges": [...] }
stats.update	server → client	{ "openCves": 142, "critical": 7 }
Roadmap
 CVE ingestion from NVD API 2.0
 Asset inventory import (CSV / JSON)
 CPE-based CVE ↔ asset matching
 3D globe with severity markers
 3D network topology graph
 Live WebSocket alert feed
 CISA KEV (Known Exploited Vulnerabilities) flagging
 EPSS exploit-probability scores
 User auth and role-based access
 Export reports (PDF / CSV)
Contributing
Fork the repo
Create a branch: git checkout -b feature/your-feature
Commit changes: git commit -m "Add your feature"
Push: git push origin feature/your-feature
Open a Pull Request
License

This project is licensed under the MIT License. See LICENSE for details.



# FOUNDERS:

- TOUFIC MAJDALANI
- CHAUNTE STERLING
