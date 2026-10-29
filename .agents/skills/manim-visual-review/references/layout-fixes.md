# Diagnose from the frame, fix the relationship

## Text escapes a box

Create the text first and wrap it with `SurroundingRectangle` or the project's
equivalent helper. Match its center and keep both in a `VGroup`. For equal-sized
comparison panels, size all panels to accommodate the largest content, then align
them. A fixed-width diagram may need wrapping or fewer words, not smaller type.

```python
label = Text("Target model", font_size=30)
box = SurroundingRectangle(label, buff=0.25)
card = VGroup(box, label)
```

If values change, reserve space for the widest expected value or resize the box
deliberately. Check that labels fit during the transform, not just at its end.

## Related objects drift or misalign

Use `VGroup(...).arrange(RIGHT, buff=...)`, `arrange_in_grid`, `align_to`, or
`next_to`. Position the completed group in its allotted region. Include labels and
backgrounds in the moving group. Avoid independent shifts that lose the relationship.
Recompute layout after adding longer text or changing font metrics.

## Frame clipping or unreadable fonts

Inspect `get_left`, `get_right`, `get_top`, `get_bottom`, `width`, and `height` against
the intended content area. In an ordinary fixed 2D camera, frame dimensions and
safe margins give useful bounds. With camera zoom/pan or 3D, validate projected
positions in rendered pixels instead. Split dense content across steps when it
cannot fit at the shared readable font size. Scaling a whole group also scales text;
the original `font_size` argument no longer describes the final on-screen size.

## Labels collide during motion

Read the trajectory and `run_time`, including `lag_ratio` and `rate_func`. Move a
container and label together. For labels that must track another moving object,
use a scoped updater such as `label.add_updater(lambda m: m.next_to(node, UP))`;
remove it when the tracking is finished. Check the midpoint and neighboring frames.
Use separate lanes or move one item at a time when crossing paths is confusing.

## Arrows detach or cover labels

Connect to object boundaries using `get_left`/`get_right` and suitable `buff`.
Refresh endpoints while their objects move, then remove temporary updaters.
Route arrows around text and check head direction. Distinguish deliberate visual
layering from accidental occlusion; changing `z_index` alone can hide a deeper
layout problem.

## Useful evidence

Record observations such as “at 2.4s the label exceeds the card's right edge”
with a frame path and source location. After repair, show the corresponding frame
and verify the size/padding relationship. A source-code assertion supplements the
rendered evidence; it does not replace it.

## References

- [FFmpeg frame filters](https://ffmpeg.org/ffmpeg-filters.html)
- [Manim mobject positioning and dimensions](https://docs.manim.community/en/stable/reference/manim.mobject.mobject.Mobject.html)
- [Manim surrounding rectangles](https://docs.manim.community/en/stable/reference/manim.mobject.geometry.shape_matchers.SurroundingRectangle.html)
