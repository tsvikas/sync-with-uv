"""sync-with-uv: Sync '.pre-commit-config.yaml' from 'uv.lock'.

use `python -m sync_with_uv` to run the cli
"""

from .cli import app

app(prog_name="sync-with-uv")
