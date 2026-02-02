┌─────────────────────────────┐
│      User (du)              │
│  ls, touch, cp, mkdir       │ ← Normale Shell Commands
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   FUSE Layer (unsichtbar)   │
│  • Embryo-Erkennung         │
│  • Automatische Material.   │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   Physisches Dateisystem    │
│   • Echte Dateien/Ordner    │
└─────────────────────────────┘