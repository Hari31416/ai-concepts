---
name: youtube-publish
description: Prepare a Manim topic for YouTube as a voiceless Short or 3-5 minute video. Use for captions and .srt files, sound effects, music, vertical layout, audio mixing, and upload notes.
compatibility: Run from the repository root with uv, ffmpeg and ffprobe on PATH.
---

# YouTube publish (voiceless, captions + light audio)

Captions carry the narration. Audio is a quiet music bed plus a few sound effects
tied to real mechanism events. No recorded voice. Read `STYLE.md` for visuals. Plan scenes with `manim-composer`, write code with
`manimce-best-practices`, and check frames with `manim-visual-review` before this.

## 1. Pick the format

- **Short (9:16):** 30-60 s, one idea, its own scene class (for example
  `PagedAttentionShort`) in `short.py`. Design vertically from the start; never crop a
  16:9 scene.
- **Feature (16:9):** 3-5 min, several scenes plus the consolidated `animation.py`
  scene. Add `CaptionTrack(..., time_offset=...)` per scene if the consolidated video
  must share one `.srt`.

## 2. Write caption beats first

Put the beats in `scenes.md` next to the visuals, then in code. Rules:

- 8-12 words, at most two lines (about 30 characters per line at Shorts size). The
  helper raises if a caption needs a third line.
- Open a Short with a hook in the first two seconds: a question or a number.
- One idea per beat. Order: **show caption -> animate the mechanism -> hold**, so
  viewers never read and track motion at once.
- Keep citations in `publish.md` and `notes.md`; do not include `Source:` text on screen in Shorts unless explicitly requested. Mark illustrative data as illustrative.

```python
from shared.captions import CaptionTrack
from shared.audio import play_sfx
from shared.theme import SHORTS_CAPTION_SIZE, SHORTS_CAPTION_Y, SHORTS_CONTENT_CENTER_X

caps = CaptionTrack(
    self,
    position=(SHORTS_CONTENT_CENTER_X, SHORTS_CAPTION_Y),
    font_size=SHORTS_CAPTION_SIZE,
    max_chars=30,
)
caps.show("Every request reserves memory for its maximum length.")
self.play(...)        # animate what the caption says
caps.hold()           # waits until the reading time (15 chars/s, min READ_PAUSE) is up
caps.finish()         # last line of construct(): writes <Scene>.srt next to the .mp4
```

`hold()` returns at once if the animation already took longer than the reading time.
Add `extra=` seconds after the last change in a beat so viewers see the result.

## 3. Shorts layout

Use the `SHORTS_*` constants in `shared/theme.py`; do not hard-code margins.
YouTube covers about the bottom 20% (title, channel, progress bar) and the right 12%
(buttons). Captions sit just above the bottom band; key content sits above the
captions (`SHORTS_CONTENT_BOTTOM`) and left of `SHORTS_SAFE_RIGHT`. Keep type at or
above the `SHORTS_*_SIZE` values. Reduce content before shrinking text.

## 4. Sound effects and music

- Effects live in `shared/audio/` (`pop`, `tick`, `whoosh`, `deny`, `chime`),
  synthesized by `shared/audio/synth.py` and generated on first use. Play one with
  `play_sfx(self, "tick")` at the moment of the event. Meanings: `tick` = a value is
  written, `pop` = something is allocated, `whoosh` = scene change, `deny` =
  rejection, `chime` = the payoff. Skip a sound that marks no event.
- Add a new effect by writing a generator in `synth.py`, adding it to `GENERATORS`
  and `SFX_NAMES`, and adding a row to `shared/audio/LICENSES.md`.
- The music bed is `music_bed` (a 32 s looping ambient pad, also synthesized).
  `make mix` loops it under the video. To use another track, pass `MUSIC=path`, and
  record its source, license and attribution in `shared/audio/LICENSES.md` first.
  YouTube Audio Library tracks are YouTube-only, CC-BY tracks need credit in the
  description, and a Content ID claim on a Short over one minute can block it.
- Levels (dBFS): effects peak near -7, the bed sits about 10 dB below them. Do not
  normalize to -14 LUFS; with no voice that would lift the bed to full volume.
  Final mixes measure near -28 LUFS integrated, peak about -9 dBFS. Check by ear on a
  phone; adjust with `--music-gain` in `scripts/mix_audio.py`.

## 5. Preview, render, mix

Run from the repository root. `FORMAT=shorts` selects `manim_shorts.cfg` and
`-r 1080,1920` (preview: `-r 480,854`).

```sh
make preview FILE=topics/<y>/<m>/<slug>/short.py SCENE=<Scene> FORMAT=shorts
make render  FILE=... SCENE=<Scene> FORMAT=shorts     # video/<Scene>.mp4 + .srt
make mix     FILE=... SCENE=<Scene>                   # video/<Scene>_final.mp4
```

Upload `<Scene>_final.mp4` and `<Scene>.srt`. Because `render` writes
`video/<Scene>.mp4`, give each Short its own scene class so it never overwrites a
landscape render. Manim also leaves `<Scene>.wav` next to the movie; delete it after
the mix.

## 6. Verify before upload

1. Extract frames with `manim-visual-review` (try `--at` times near caption changes).
   Look at full-resolution frames for clipped text, caption overlap and safe zones.
2. `ffprobe` the final file: 1080x1920 for Shorts, an audio stream present, duration
   as planned.
3. Compare the `.srt` with the on-screen captions: same text, same times.
4. Listen on a phone with the sound on and off. The video must read with sound off.
5. Confirm every audio asset has a row in `shared/audio/LICENSES.md`.

## 7. Package

Keep a `publish.md` in the topic folder with the title (under 70 characters), the
description (what it shows, link to `notes.md` or the repo, chapters for long videos,
music attribution if any), tags, playlist, the caption list, and the upload date.
Thumbnails come from a still frame in `images/` (`make frame`), with a short title
overlay for feature videos. Cut a feature video's best mechanism into a Short that
points to the full video.

## Later

- **Feature video (3-5 min, 16:9):** not built yet. It needs about four times the
  material of the paged-attention Short (new scenes), chapters, an intro and end card,
  and a thumbnail. Validate the 16:9 flow on one topic first.
- **Synthetic voice (optional):** if captions alone are not enough, evaluate
  `manim-voiceover` with a local TTS such as Kokoro or Piper. Keep the same caption
  text and timings for the `.srt`, drive animation timing from clip length, duck the
  music under speech with ffmpeg `sidechaincompress`, and cache clips by hash of text
  and voice. Check each provider's commercial-use terms. No own-voice recording.
- **Phone check still open for the first Short:** listen with sound on and off, and
  confirm caption and title overlay positions on a real phone.
