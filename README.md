# matrix-dl

Download backlogs from Matrix as raw text.

This is a modernized version of the original tool. It now uses
[`mautrix`](https://github.com/mautrix/python) instead of the outdated
`matrix-client` library.

## Features

- Download room history from a Matrix homeserver
- Output plain text logs
- Filter by start and end date
- Accept room IDs, room aliases, or simple alias names

## Installation with `uv`

First install [`uv`](https://github.com/astral-sh/uv).

For example on Linux/macOS:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
