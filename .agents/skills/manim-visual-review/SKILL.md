---
name: manim-visual-review
description: Inspect and fix Manim layout and transition defects using FFmpeg frames and visual review. Use for overlapping text, misaligned boxes, clipping, unreadable labels, and final visual checks.
compatibility: Python 3.12+, Pillow, ffmpeg and ffprobe on PATH, and an agent image-viewing tool. Manim is needed to rerender source changes.
---

# Manim visual review

Review the rendered evidence, identify the layout cause, repair it, and inspect the
result again. A successful render proves execution, not visual quality.

## 1. Establish the scope

Read project guidance and style conventions, the affected scene, and relevant
Manim implementation references. Identify the exact video and source revision.
Use project render commands from the repository root. If no video exists, render
the affected scene at 720p for typography review. Reuse a current video when useful.
For a still image, open it directly and continue with diagnosis and verification.
If source is unavailable, inspect the video and report timestamped findings without
claiming a repair. Preserve the user's files and any existing review evidence.

## 2. Extract and look

Run the bundled script with the project's Python environment. Resolve `<skill-dir>`
to this skill's actual directory; it is not relative to the topic.

```sh
uv run --locked python <skill-dir>/scripts/inspect_frames.py path/to/video.mp4 \
  --output work/review-before
```

The default samples about 12 positions across the whole video, including its ending.
It writes full-resolution PNGs, contact sheets of up to 12 thumbnails each, and a
manifest containing requested seek positions. These are approximate frame times,
not exact decoded presentation timestamps. Variable-frame-rate video may vary more.
An existing nonempty output directory is refused; choose a fresh one for each pass.

Open every contact sheet with the agent's image-viewing tool. Then open individual
frames at full resolution for typography, padding, and suspected defects. Extracting
files or reading the manifest alone does not count as visual inspection. Check:

- Text fits its container, stays readable at the intended display size, and follows
  the style hierarchy. Inspect both full resolution and an embedded-size view.
- Related elements align; spacing and box padding stay consistent.
- Equations, labels, arrows, and legends remain inside the visible camera frame.
- Entity colors remain consistent and key labels are not obscured.
- Beginning and ending states contain the intended content.

## 3. Inspect movement

Coarse sampling can miss a brief collision. Read the scene's `play`, `wait`, timing,
and updater logic to locate major transitions. Inspect before, during, and after
them, especially when labels, boxes, or camera positions change. Do this even if
the contact sheet's settled states look clean. Sample a suspected range densely:

```sh
uv run --locked python <skill-dir>/scripts/inspect_frames.py path/to/video.mp4 \
  --output work/review-transition --start 4.0 --end 5.0 --every 0.1
```

Or inspect exact requested moments with `--at 4.2 4.4 4.6`. For shorter defects,
reduce the interval toward the video's frame duration. The script limits extraction
to 120 frames per invocation; narrow the range before raising `--max-frames`.
For long videos, review each scene or section instead of trusting 12 overview frames.
Frame samples cannot prove all motion is clean. Watch a clip when a video viewing
tool is available; otherwise report motion coverage and any remaining uncertainty.

## 4. Diagnose and repair

Record each material finding with a timestamp, visible symptom, and source cause.
Read `references/layout-fixes.md` for concrete Manim repair patterns. Use geometry
to explain observed defects: widths, heights, edge positions, relative arrangement,
padding, group membership, and updater behavior. Check the installed API when unsure.

Prefer fixes that preserve relationships: arrange groups, align edges, size containers
around content, attach labels to their objects, and route arrows consistently.
Reduce content or split steps before shrinking readable text. Preserve the concept,
entity identities, style, and unrelated source. Intentional containment, occlusion,
and emphasis are not automatically defects; explain their meaning before changing.

Optional geometry assertions should encode declared relationships, such as a label
fitting its box. World-coordinate bounds alone are insufficient for moving cameras
and 3D projections. Avoid generic pairwise-overlap rules and blanket auto-scaling.

## 5. Verify and hand off

Rerender changed scenes. Extract to a fresh output directory and visually inspect
the same problem moments plus neighboring transition states. If timing changed,
locate the same semantic event at its new time. Recheck the overview for regressions.
Inspect final-quality frames when final rendering is authorized by the user or
project workflow. Keep useful review evidence until the user is satisfied, then use
project cleanup conventions. Never delete final assets as part of frame inspection.

Finish with a concise report containing the reviewed video, time ranges and frames
actually inspected, findings and fixes with before/after evidence paths, and any
unresolved issues. Distinguish visual checks from geometry checks. If image tools or
rendering fail, report that limit instead of claiming the animation passed.
