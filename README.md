# Structure

```Python

patchpilot/
│
├── src/
│   └── patchpilot/
│       │
│       ├── api/
│       │   ├── routes.py
│       │   └── schemas.py
│       │
│       ├── agent/
│       │   ├── graph.py
│       │   ├── state.py
│       │   ├── nodes.py
│       │   └── prompts.py
│       │
│       ├── tools/
│       │   ├── filesystem.py
│       │   ├── search.py
│       │   ├── git.py
│       │   ├── testing.py
│       │   └── patching.py
│       │
│       ├── llm/
│       │   └── model.py
│       │
│       ├── sandbox/
│       │   └── runner.py
│       │
│       ├── indexing/
│       │   └── codebase.py
│       │
│       ├── main.py
│       └── config.py
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── tests/
│
├── pyproject.toml
├── README.md
└── .env
```