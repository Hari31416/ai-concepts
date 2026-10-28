# Visual style

Use a dark background, readable type, and diagrams that explain the mechanism.
Keep the same visual meanings across a topic's animations, figures, and HTML.
Treat these as starting defaults; adapt them when the explanation needs it.

## Shared defaults

`shared/theme.py` is the source of truth for colors, font sizes, spacing, and timing.
`shared/theme.css` provides matching CSS variables and styles for HTML pages.
Import theme constants and helpers in Manim scenes. For HTML or SVG, use the matching
CSS variables or link `shared/theme.css`. Keep intentional topic-specific choices with
that topic. `manim.cfg` repeats the background so unthemed scenes start with the same
color; update it too when changing `BACKGROUND`.

| Token                        | Meaning                                                   |
| ---------------------------- | --------------------------------------------------------- |
| BACKGROUND, SURFACE          | Canvas and occasional grouping panels                     |
| TEXT, MUTED                  | Main content and secondary explanations                   |
| BORDER                       | Structural lines and boundaries                           |
| ACCENT                       | Current step, active equation term, or temporary emphasis |
| SUCCESS, ERROR               | Accepted/correct and rejected/incorrect outcomes          |
| ENTITY_A, ENTITY_B, ENTITY_C | Distinct models, tensors, paths, or other entities        |

Assign entity colors at the start of a topic and retain them across representations.
For example, a target model can use ENTITY_A and a draft model ENTITY_B; both keep
those colors in the page, video, and figures. Use outcome colors only for outcomes.
Pair meaningful color with labels, shapes, or line styles. Heatmaps need a labeled
scale; choose a sequential or diverging palette that matches the quantity.

Use `panel()` and `surrounding_panel()` from `shared.theme` to draw containers and
boundaries, and `title()` to place standardized scene headers.

## Typography and layout

Use Arial for ordinary text and Manim's LaTeX font for equations. HTML uses
`Arial, sans-serif`; browser math can retain its math font. If Arial is unavailable,
choose an installed sans-serif font and record the choice for reproducibility.
Use the shared size constants as defaults for a normal 16:9 scene. Titles are larger
than body text; labels remain readable when the video is embedded in a page.

Keep content inside the shared margin. Align related objects and use the shared gap
as a spacing starting point. Reduce content or split steps before shrinking text.
Use panels only when grouping helps understanding. Keep enough room around equations,
arrow labels, and changing values to avoid overlap during transitions.

## Animation

Use movement to show a change in state, a dependency, or a correspondence. Transform
objects when their identity continues across steps. Introduce complexity gradually
and pause after equations or important results. Shared durations are starting points;
allow more time for reading and dense reasoning. Use emphasis briefly, then return
to the entity's usual color. Prefer simple fades and transforms over decorative motion.

When an animation becomes large or spans several distinct phases, adopt a modular
structure:

- Split separate stages into distinct scene classes or separate files under `scenes/`.
- Extract reusable composite mobjects or diagrams into a topic helper module.
- Keep individual scenes independently renderable for fast preview cycles.

## HTML explanations

Match the palette and entity meanings. Link `shared/theme.css` to adopt default styling,
or use matching CSS variables directly. Use a readable text column around 70ch wide,
body text of at least 18px, and line height around 1.6. Scale diagrams and videos to
the container, keep controls available, and let readers start video playback.
Use meaningful captions and image alternative text. Check narrow screens and avoid
horizontal scrolling except for equations or diagrams that need it. Respect reduced
motion for browser animations. Add interactive controls only when they teach something.

## Verification

Inspect representative frames at the intended viewing size, including transition
states. Check text contrast, clipping, equation readability, and consistent entity
colors. Check HTML asset links and layout in a browser when creating a page.
