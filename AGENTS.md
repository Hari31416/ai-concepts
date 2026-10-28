# Working in this project

This is a growing collection for understanding AI concepts. Work directly in the
repository. Keep each request as small as its learning goal allows.

## Start with the request

- Read the existing topic before editing. Create only the files the task needs.
- Research, notes, implementations, figures, animations, and HTML explanations are
  independent options. Implementation is optional. A diagram may need only a
  checked illustrative example.
- Keep topic work in `topics/<year>/<month>/<topic-slug>/`, using a four-digit year
  and two-digit month, such as `topics/2026/10/attention/`. Date new topics by their
  creation month; continue existing topics in their original folder. Use descriptive
  filenames. Add shared helpers only after actual reuse appears. Leave unrelated
  blog work in its repository.
- Use uv and Black. Use standard logging for Python utilities. Introduce Pydantic
  when structured validation is needed, and tests when there is behavior to verify.

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
and a requested still figure needs no video. An implementation is always optional.

## Optional HTML explanations

When the user requests a topic page, create `index.html` inside that topic. Explain
with readable prose and whichever equations, images, diagrams, videos, or small
interactions help. Use Manim or another suitable technique for individual visuals.
Keep assets beside the page with relative links; Manim media can stay in the topic's
`media/` directory. Prefer plain HTML, CSS, SVG, and JavaScript. Introduce a frontend
build only when a concrete need justifies it. Check the page in a browser and verify
asset loading, narrow-screen layout, and interactions.

## Completion and maintenance

- Run relevant checks and summarize what changed, how to use it, and any unverified
  parts. Use `make help` for rendering and repository commands.
- Keep generated media and temporary experiments out of Git. Keep source assets
  needed to reproduce explanations. Store source links and assumptions in the
  topic's notes when the task involves research.
- Add dependencies and conventions as needs appear. Voiceover and presentation
  infrastructure are outside the initial scope.
- When committing, use `<type>(<scope>): <subject>` with a subject of at most 50
  characters. Types: chore, docs, feat, fix, refactor, style, test. Scopes: backend,
  frontend, infra, general. Optional body uses bullet points; optional footer records
  issues or breaking changes.
