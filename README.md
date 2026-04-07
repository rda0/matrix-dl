# matrix-dl

Download Matrix room history as raw text.

This is a modernized version of the [original tool](https://github.com/rubo77/matrix-dl).
It now uses [`mautrix`](https://github.com/mautrix/python) instead of the outdated `matrix-client` library.

## Features

- Download room history from a Matrix homeserver
- Output plain text logs
- Filter by start and end date
- Accept room IDs, room aliases, or simple alias names
- Output one line per message in this format: `YYYY-MM-DD HH:MM:SS - user: message`

## Installation with `uv`

First install [`uv`](https://github.com/astral-sh/uv).

For example on Linux/macOS:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or see the official installation instructions:
https://github.com/astral-sh/uv

## Clone and install

```sh
git clone https://github.com/rda0/matrix-dl
cd matrix-dl
uv venv
source .venv/bin/activate
uv pip install -e .
```

You can then run:

```sh
matrix-dl --help
```

## Usage

```sh
matrix-dl [-h] [--password PASSWORD] [--matrix-url MATRIX_URL]
          [--start-date START_DATE] [--end-date END_DATE]
          username room
```

## Examples

### Download from a room ID

```sh
matrix-dl --matrix-url https://matrix.example.com \
  --start-date 2026-01-01 \
  --end-date 2026-04-07 \
  @alice:matrix.example.com \
  '!abcdef123456:matrix.example.com' > room.log
```

### Download from a full room alias

```sh
matrix-dl --matrix-url https://matrix.example.com \
  --start-date 2026-01-01 \
  @alice:matrix.example.com \
  '#general:matrix.example.com' > general.log
```
