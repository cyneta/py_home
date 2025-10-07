# py_home - Python-Based Home Automation

Code-first home automation system using Python + REST APIs instead of n8n visual workflows.

## Project Structure

```
py_home/
├── scripts/          # Automation scripts (leaving_home.py, tesla_preheat.py, etc.)
├── utils/            # Reusable API clients (tesla_api.py, nest_api.py, etc.)
├── server/           # Flask webhook server
├── config/           # Configuration files (config.yaml, .env.example)
├── tests/            # Unit and integration tests
├── docs/             # Design documents and documentation
├── plans/            # Implementation plans and task tracking
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Documentation

- **[System Design](docs/SYSTEM_DESIGN.md)** - Complete system architecture and design decisions

## Getting Started

See `docs/SYSTEM_DESIGN.md` for full details on architecture, components, and workflows.

### Development (Laptop)

```bash
cd py_home
pip install -r requirements.txt
cp config/.env.example config/.env
# Edit config/.env with your API credentials
python scripts/leaving_home.py  # Test individual scripts
```

### Production (Raspberry Pi)

```bash
git clone <repo-url>
cd py_home
pip3 install -r requirements.txt
# Copy .env file with credentials
python3 server/webhook_server.py  # Start webhook server
```

## Quick Links

- Design: `docs/SYSTEM_DESIGN.md`
- Plans: `plans/` (implementation plans, task tracking)
- Scripts: `scripts/` (automation workflows)
- APIs: `utils/` (reusable API clients)
