# AI concepts

A small workspace for coding agents and humans to research, understand, and explain
AI concepts. Use notes, worked examples, implementations, Manim animations, figures,
or HTML pages as needed. Every topic can take a different path.

## Setup

Install [uv](https://docs.astral.sh/uv/) and the native tools Manim needs. On macOS:

```sh
brew install cairo pango pkg-config ffmpeg
```

Install a TeX distribution such as MacTeX for `Tex` and `MathTex`, and make sure
`latex` and `dvisvgm` are available. Then, from this directory:

```sh
make setup
```

Python dependencies are locked in `uv.lock`. `.python-version` selects Python 3.12.
The project uses Manim Community Edition with the Cairo renderer. See the
[official installation guide](https://docs.manim.community/en/stable/installation.html)
for platform-specific details.

## Work on a topic

Ask your coding agent for the output you want, for example:

- "Research attention and save a short explanation with sources."
- "Animate a tiny numerical example of softmax attention."
- "Create an HTML explanation of KV caching with diagrams and an animation."
- "Implement a toy example to verify the values in this animation."

The agent reads `AGENTS.md` and the relevant existing Manim skills. Work goes in
`topics/<year>/<month>/<topic-slug>/`, for example `topics/2026/10/attention/`.
Use the creation year and a two-digit month; keep later updates in the same folder.
Create only useful files. Standard filenames keep topics predictable:
`notes.md`, `scenes.md`, `animation.py` (or a modular `scenes/` folder for large animations),
`toy.py`, and `index.html`.

## Visual style

`STYLE.md` explains palette meanings, typography, layout, animation, and HTML
conventions. `shared/theme.py` holds reusable constants and helpers; `shared/theme.css`
provides matching styles for HTML pages. Run commands from the project root so topic
scenes can import the theme:

```python
from manim import Scene
from shared.theme import ACCENT, TITLE_SIZE, apply_theme, panel, text


class Attention(Scene):
    def construct(self) -> None:
        apply_theme(self)
        self.add(panel(width=8.0, height=4.0))
        self.add(text("Attention", font_size=TITLE_SIZE, color=ACCENT))
```

Use `text()`, `math()`, `panel()`, and `title()` for themed elements, or pass the shared
constants to Manim constructors directly. Helpers leave Manim's global defaults unchanged.

## Render

Once a topic has a scene, run these commands from the project root. Substitute its
file and class name:

```sh
make list FILE=topics/2026/10/attention/animation.py
make preview FILE=topics/2026/10/attention/animation.py SCENE=Attention
make frame FILE=topics/2026/10/attention/animation.py SCENE=Attention
make render FILE=topics/2026/10/attention/animation.py SCENE=Attention
```

Preview renders a 480p video. Render defaults to 1080p; set `QUALITY=m` for 720p.
Final videos and frames are saved beside the scene source as `Attention.mp4` and
`Attention.png`. Set `OUTPUT_DIR=...` to change that location. Preview videos and
render caches stay in `OUTPUT_DIR/media/`; set `MEDIA=...` to override it.
Use `OPEN=1` to open output after rendering and `VERBOSE=1` for debug logs.
These options work with preview, render, and frame. For direct CLI access:

```sh
uv run --locked manim --help
```

For an optional HTML page, embed assets with paths relative to `index.html`. To
preview pages over HTTP, run this from the project root and open the topic URL:

```sh
uv run --locked python -m http.server 8000 --bind 127.0.0.1
```

Videos are generated files;
rerender them on a fresh checkout or include them separately when sharing a page.

## Finish an animation

Iterate with previews while reviewing the explanation. Once you are satisfied, the
agent renders the final video at high quality, checks playback and representative
frames, updates any HTML asset links, and cleans that scene's partial movie caches:

```sh
make render FILE=topics/2026/10/attention/animation.py SCENE=Attention QUALITY=h
make clean FILE=topics/2026/10/attention/animation.py SCENE=Attention
```

Use the same `OUTPUT_DIR` and `MEDIA` overrides for rendering and cleanup. Cleanup
preserves final videos, images, previews, other scenes, and shared TeX caches. Agents
also remove their scratch files and unused previews after checking asset references.
Research-only and still-image tasks use only the relevant parts of this workflow.

## Checks

```sh
make format
make test
make typecheck
make check
```

Checks cover formatting, YAML/TOML/JSON validity, whitespace, private-key detection,
Mypy static type analysis, and pytest unit tests.
Agents also check technical claims and inspect rendered output for animation work.
Add implementation tests when a topic needs them.

## Existing skills

`manim-composer` and `manimce-best-practices`, including references, templates, and
examples, are copied unchanged from the blog project. Existing blog animations stay
there. This project starts with an empty `topics/` directory.

Keep the root `skills-lock.json` with the skills so their source and installation
metadata stay available. Preserve it when working on topics.
