# Component Demo Packages

Each component has a self-contained demo/doc package for testing and reference.

## Structure

```
components/
├── tapo/           # Tapo P125M smart plugs
│   ├── README.md   # Quick start
│   ├── demo.py     # Interactive demos
│   ├── test.py     # Quick connection test
│   ├── GUIDE.md    # User guide
│   └── API.md      # API reference
│
├── nest/           # Nest thermostat
│   ├── README.md
│   ├── demo.py
│   ├── test.py
│   ├── GUIDE.md
│   └── API.md
│
├── sensibo/        # Sensibo mini-split AC
│   ├── README.md
│   ├── demo.py
│   ├── test.py
│   ├── GUIDE.md
│   └── API.md
│
└── [other components...]
```

## Quick Test All Components

```bash
# Test individual component
cd components/tapo && python test.py

# Test all
for dir in components/*/; do
    echo "Testing $dir..."
    (cd "$dir" && python test.py)
done
```

## Purpose

Each component package:
- ✓ Demonstrates all capabilities
- ✓ Provides quick connection test
- ✓ Serves as reference documentation
- ✓ Can verify functionality anytime
- ✓ Self-contained (includes all docs)

## Available Components

- **tapo**: ✓ Complete (Tapo P125M smart plugs)
- **nest**: Pending (Nest thermostat)
- **sensibo**: Pending (Sensibo mini-split AC)
- **google_maps**: Pending (Travel time/traffic)
- **notifications**: Pending (Pushover/ntfy)
