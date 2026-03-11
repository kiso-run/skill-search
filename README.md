# tool-search

Web search tool for [kiso](https://github.com/kiso-run/core). Supports [Brave Search](https://brave.com/search/api/) and [Serper](https://serper.dev/) as backends.

## Installation

```bash
kiso tool install search
```

This clones the repo to `~/.kiso/tools/search/`, runs `uv sync`, and copies `config.example.toml` → `config.toml`.

## Configuration

### 1. Get an API key

- **Brave Search** — https://api.search.brave.com/ — free tier: 2000 queries/month
- **Serper** — https://serper.dev/ — 2500 free queries (one-time), then ~$1/1000

### 2. Set the key

```bash
kiso env set KISO_SKILL_SEARCH_API_KEY "your-key"
kiso env reload
```

### 3. Choose a backend (optional)

The default backend is Brave. To switch to Serper, edit `~/.kiso/tools/search/config.toml`:

```toml
backend = "serper"
```

## How it works

1. The planner decides a web search is needed and emits a `tool` task with a `query` argument.
2. Kiso runs `run.py` as a subprocess, passing the arguments as JSON on stdin.
3. The tool calls the configured search API and formats the results as plain numbered text.
4. The reviewer evaluates the output; subsequent tasks (msg, exec) can reference the results.

## Backends

| Backend | Results | Free tier | After free tier |
|---------|---------|-----------|-----------------|
| Brave   | Brave index | 2000 queries/month | Paid plans |
| Serper  | Google | 2500 queries (one-time) | ~$1/1000 queries |

## Args reference

| Arg | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `query` | string | yes | — | Search query |
| `max_results` | int | no | 5 | Number of results (1–100) |
| `language` | string | no | — | Language code, e.g. `it`, `en`, `ja` |
| `country` | string | no | — | Country code, e.g. `IT`, `US`, `JP` |

## License

MIT
