# Working in this project

This is a growing collection for understanding AI concepts. Work directly in the
repository. Keep each request as small as its learning goal allows.

## Pedagogical purpose and depth

Every animation, diagram, toy implementation, or page exists to unlock genuine understanding
of a concept. Never build artifacts for the sake of creating them.

- **Mechanism over ornament:** Choose visuals, motion, and structure that illuminate
  how the concept works—its intuition, data flow, and mathematical heart—rather than
  decorative flourishes.
- **Calibrated depth:** Go deep enough to reveal the core machinery and design rationale,
  without drowning in tangential rabbit holes, exhaustive survey literature, or pedantic
  edge cases.
- **Creative explanatory framing:** Favor tactile metaphors, minimal worked examples with
  real numbers, and side-by-side correspondences that make abstract math concrete.

## Start with the request

- Read the existing topic before editing. Create only the files the task needs.
- Research, notes, implementations, figures, animations, and HTML explanations are
  independent options. Implementation is optional. A diagram may need only a
  checked illustrative example.
- Keep topic work in `topics/<year>/<month>/<topic-slug>/`, using a four-digit year
  and two-digit month, such as `topics/2026/10/attention/`. Date new topics by their
  creation month; continue existing topics in their original folder.
- Use standardized filenames when creating topic artifacts:
  - `notes.md` for background research, formulations, and references.
  - `scenes.md` for storyboard plans and scene scripts.
  - `animation.py` for Manim scenes.
  - `toy.py` for minimal reference implementations.
  - `index.html` for topic web pages.
- Add shared helpers only after actual reuse appears. Introduce Pydantic when
  structured validation is needed, and tests when there is behavior to verify.

## Visual style

Before creating or changing animation, figure, or HTML visuals, read `STYLE.md`.
Use `shared/theme.py` for Manim defaults and `shared/theme.css` for HTML pages.
Run render commands from the repository root so topic scenes can import `shared.theme`.

## Animation skills

- When planning an animation, read `.agents/skills/manim-composer/SKILL.md`.
  Scale its plan to the request: a single figure or short clip can use a few notes.
  Infer routine choices from the request and existing topic; ask only for material
  missing information. A full video plan and clarification round are optional.
- When writing or reviewing Manim code, read
  `.agents/skills/manimce-best-practices/SKILL.md` and relevant linked references.
- Preserve these skills, their supporting files, and the root `skills-lock.json`.
  Keep lock metadata in sync when deliberately installing or updating skills.
  Prefer Manim Community Edition.

## Animation workflow

1. Establish the learning question and check claims, equations, and numerical
   examples. Mark illustrative data and assumptions. Save sources when researching.
2. Build a low-quality preview. Inspect representative frames and watch transitions
   and pacing. Fix clipping, unreadable labels, and incorrect values before sharing.
3. Share the preview for feedback and iterate. When the user is satisfied, render
   the final animation with `make render FILE=... SCENE=... QUALITY=h`, or the
   higher quality they requested. Existing instructions to finalize count as approval;
   avoid asking again. During feedback, retain caches for quick revisions.
4. Verify the final video plays, has the requested resolution, and contains the
   intended ending. Inspect representative frames from the final render. If there
   is an HTML page, point it at the final assets and verify those links in a browser.
5. After the final output passes review, run `make clean FILE=... SCENE=...` with
   the same output/media overrides used for rendering. It removes only that scene's
   partial movie caches; shared TeX caches, previews, and final assets stay intact.
   Remove task-created scratch files and obsolete previews only after checking that
   no page or explanation uses them. Preserve source files and unrelated topic work.
6. Report final artifact paths, verification, and cleanup. If waiting for feedback
   or blocked on a render, state what remains; keep useful intermediate work.

Apply only the steps relevant to the request. A notes-only task needs no rendering,
and a requested still figure needs no video.

### Modular animation structure

When animation code becomes large or spans several distinct phases, adopt a modular layout:

- Split separate stages into distinct scene classes or individual files under a topic `scenes/` directory (for example `scenes/mechanism.py`).
- Extract composite mobjects, reusable diagrams, or visual helpers into a topic helper module, or import shared primitives from `shared.theme`.
- Keep individual scenes independently renderable with `make preview FILE=... SCENE=...` so iteration stays fast.
- Use a root `animation.py` to import or coordinate the full sequence if a combined render is required.

## Topic modalities and completion criteria

- **Research and notes:** Save in `notes.md`. Must include concept definitions, mathematical formulations, primary source links, and checked numerical toy examples.
- **Implementations:** Save in `toy.py`. Must provide typed, runnable Python code with assertions or pytest tests verifying values against theoretical math.
- **Animations:** Preview with `make preview`, fix transitions and layout, render final output at target quality with `make render`, and clean scene caches with `make clean`.
- **HTML explanations:** Save in `index.html`. Link `shared/theme.css` or use theme tokens, keep assets relative, ensure responsive narrow-screen layout, and verify via `python -m http.server 8000`.

## Completion and maintenance

- Run `make check` (formatting, hooks, mypy, and pytest) and summarize what changed, how to use it, and any unverified parts. Use `make help` for command options.
- Keep generated media and temporary experiments out of Git. Keep source assets needed to reproduce explanations.
