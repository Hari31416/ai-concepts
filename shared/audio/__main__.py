"""Generate every audio asset: `uv run --locked python -m shared.audio`."""

from shared.audio import asset_path
from shared.audio.synth import GENERATORS

for asset in GENERATORS:
    print(asset_path(asset))
