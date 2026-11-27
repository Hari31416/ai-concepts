---
name: youtube-publish
description: Prepare a Manim topic for YouTube as a voiceless Short, captioned main animation, or 3-5 minute video. Use for captions and .srt files, sound effects, music, vertical layout, audio mixing, and upload notes.
compatibility: Run from the repository root with uv, ffmpeg and ffprobe on PATH.
---

# YouTube publish (voiceless, captions + light audio)

Captions carry the narration, in every format: the vertical Short **and** the main
16:9 animation (`animation.py`, its scenes, and the consolidated scene). Audio is
optional and quiet: a Short gets a music bed plus a few sound effects tied to real
mechanism events; the main 16:9 animation is captions only unless the user asks for
audio. No recorded voice anywhere. Read `STYLE.md` for visuals. Plan scenes with `manim-composer`, write code with
`manimce-best-practices`, and check frames with `manim-visual-review` before this.

## 1. Pick the format

- **Short (9:16):** 30-60 s, one idea, its own scene class (for example
  `PagedAttentionShort`) in `short.py`. Design vertically from the start; never crop a
  16:9 scene.
- **Main animation (16:9):** the topic's `animation.py` scenes and the consolidated
  scene. Every scene carries captions (section 3), including the consolidated one,
  which is what gets uploaded. Captions are added in the scene code itself, so the
  individual scene videos and the consolidated video each get their own `.srt`.
  If a consolidated scene is built by playing other scenes' code in one `construct`,
  create one `CaptionTrack` and share it. If it replays scenes as separate renders,
  pass `time_offset=` per scene so cues line up in a single `.srt`.
- **Feature (16:9):** 3-5 min, several scenes plus the consolidated `animation.py`
  scene, with the same captions rules as the main animation.

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

# Short (9:16)
caps = CaptionTrack(
    self,
    position=(SHORTS_CONTENT_CENTER_X, SHORTS_CAPTION_Y),
    font_size=SHORTS_CAPTION_SIZE,
    max_chars=30,
)
# Main animation (16:9): defaults are CAPTION_Y, BODY_SIZE and CAPTION_MAX_CHARS (56)
caps = CaptionTrack(self)
caps.show("Every request reserves memory for its maximum length.")
self.play(...)        # animate what the caption says
caps.hold()           # waits until the reading time (15 chars/s, min READ_PAUSE) is up
caps.finish()         # last line of construct(): writes <Scene>.srt next to the .mp4
```

`hold()` returns at once if the animation already took longer than the reading time.
Add `extra=` seconds after the last change in a beat so viewers see the result.

## 3. Captions in the main animation (16:9)

Same helper, same rules, landscape defaults. Add captions to existing scenes without
redesigning them:

- Create the track right after `apply_theme(self)`; call `caps.finish()` last.
- Wrap each existing step in the beat order: `caps.show(...)`, the animations that
  already exist, `caps.hold()`. Do not rewrite the visuals to suit the captions.
- The caption pill is centred at `CAPTION_Y` (-3.05; the 8-unit frame ends at -4, and
  a two-line pill is about 1.2 tall). Keep diagrams, labels and callouts above
  `CONTENT_BOTTOM` (-2.3) from `shared/theme.py`; move content up or shrink it slightly
  rather than letting it touch the caption. Do not overlap the scene title or a persistent
  takeaway box. A bottom banner must end above `CONTENT_BOTTOM`: use a height of 0.6
  or less centred at about `y = -1.95`. A banner at `y = -2.6` collides with the
  caption. Otherwise clear the caption (`caps.clear()`) while the banner is shown.
- Captions replace text-only takeaway banners ("Insight: ...", "Outcome: ..."). Delete
  a banner that restates its caption; keep only callouts that show a number or a
  diagram the caption does not.
- Quick geometry check: the caption pill top is `CAPTION_Y` plus half the pill height
  (0.43 for one line, 0.6 for two). Content bottom must be at least 0.15 above that.
- Replace the `self.wait()` that follows a captioned step with `caps.hold()` or
  `caps.hold(extra=...)`; a leftover wait doubles the pause. Keep a plain `wait` only
  for a pause with no caption.
- Keep the default size (`BODY_SIZE`) and at most `CAPTION_MAX_CHARS` (56) characters
  per line, two lines.
  Aim for 56 characters or fewer so each caption is one line. If a caption needs two
  lines, reword it until the lines are balanced; never leave a one-word second line.
  One idea per beat. Do not repeat on-screen labels word for word; say why they matter.
- Captions replace voice-over, so write the beats as the narration a voice would
  have said. Pacing follows reading time (`hold()`), not an audio track.
- Open the video, and each act or section title, with a question or a claim (the
  Shorts hook rule applies in 16:9 too).
- Add the beats to `scenes.md` next to the visuals they accompany. If only the
  consolidated scene is captioned, put one table of beats under it, grouped by act,
  and say so.

## 4. Shorts layout

Use the `SHORTS_*` constants in `shared/theme.py`; do not hard-code margins.
YouTube covers about the bottom 20% (title, channel, progress bar) and the right 12%
(buttons). Captions sit just above the bottom band; key content sits above the
captions (`SHORTS_CONTENT_BOTTOM`) and left of `SHORTS_SAFE_RIGHT`. Keep type at or
above the `SHORTS_*_SIZE` values. Reduce content before shrinking text.

## 5. Sound effects and music

- Effects live in `shared/audio/`, synthesized in stereo by `shared/audio/synth.py`
  and regenerated whenever `synth.py` changes. Play one with
  `play_sfx(self, "tick")` at the moment of the event; `delay=` offsets it in seconds
  so one animation can carry a sequence. Choose sounds by mechanism, not decoration:
  - `blip_0`-`blip_3`: light plucked notes for the small or cheap model (rising,
    panned left to right like tokens on screen);
  - `ping_0`-`ping_3`: bells for a verified or accepted item, rising in step;
  - `thump`: a heavy hit for the big model or a big memory read;
  - `stream`: fast clicks for data crossing a bus; `riser`: build-up before a big
    step (follow with `thump` at `delay=0.85`);
  - `tick` = a small value written, `pop` = something allocated, `whoosh` = scene
    change (sweeps left to right), `deny` = rejection, `chime` = the payoff.
  Skip a sound that marks no event, and keep a family consistent (all draft tokens
  use `blip`, all accepted ones use `ping`).
- Add a new effect by writing a generator in `synth.py` (stereo `(n, 2)` array; keep
  energy above about 150 Hz because phone speakers cannot play lower), adding it to
  `GENERATORS` and `SFX_NAMES`, and adding a row to `shared/audio/LICENSES.md`.
- The music bed is `music_bed` (a 32 s looping stereo pad with bass, air and echoing
  plucks, also synthesized). `make mix` loops it under the video and ducks it a few
  dB under each effect (sidechain), so effects stay clear. To use another track, pass `MUSIC=path`, and
  record its source, license and attribution in `shared/audio/LICENSES.md` first.
  YouTube Audio Library tracks are YouTube-only, CC-BY tracks need credit in the
  description, and a Content ID claim on a Short over one minute can block it.
- Levels (dBFS): effects peak near -10, the bed sits about 10 dB below them. Do not
  normalize to -14 LUFS; with no voice that would lift the bed to full volume.
  Final mixes measure near -24 LUFS integrated. Check by ear on a
  phone; adjust with `--music-gain` in `scripts/mix_audio.py`.

## 6. Preview, render, mix

Run from the repository root. `FORMAT=shorts` selects `manim_shorts.cfg` and
`-r 1080,1920` (preview: `-r 480,854`).

```sh
make preview FILE=topics/<y>/<m>/<slug>/short.py SCENE=<Scene> FORMAT=shorts
make render  FILE=... SCENE=<Scene> FORMAT=shorts     # video/<Scene>.mp4 + .srt
make mix     FILE=... SCENE=<Scene>                   # video/<Scene>_final.mp4
```

The main animation uses the same commands without `FORMAT` (landscape is the default):
`make render FILE=topics/<y>/<m>/<slug>/animation.py SCENE=<ConsolidatedScene>`, then
`make mix` only if the video should have the music bed or sound effects (skip it for
a captions-only main animation and upload `<Scene>.mp4`). Captions are burned in at
render time, so no extra step is needed to get them into the video; the `.srt` is
written next to the `.mp4` for upload.

`make preview` writes its `.mp4` and `.srt` to `<topic>/media/videos/<file>/<res>/`,
not `video/`. Delete previews when done.

Upload `<Scene>_final.mp4` (or `<Scene>.mp4` when not mixed) and `<Scene>.srt`. Because `render` writes
`video/<Scene>.mp4`, give each Short its own scene class so it never overwrites a
landscape render. Manim also leaves `<Scene>.wav` next to the movie; delete it after
the mix.

## 7. Verify before upload

1. Extract frames with `manim-visual-review`. Read the `.srt` and use `--at` with
   each cue's start plus 0.5 s (the caption is fully faded in), plus a frame while
   each banner is up. Check the worst
   case: a two-line caption together with a banner.
   Look at full-resolution frames for clipped text, caption overlap and safe zones.
   For the main animation, check that the caption never covers a diagram, label or
   takeaway, especially in scenes that were laid out before captions existed.
2. `ffprobe` the final file: 1080x1920 for Shorts, 1920x1080 for the main animation,
   an audio stream present, duration as planned.
3. Compare the `.srt` with the on-screen captions: same text, same times.
4. Listen on a phone with the sound on and off. The video must read with sound off.
5. Confirm every audio asset has a row in `shared/audio/LICENSES.md`.

## 8. Package

Keep a `publish.md` in the topic folder with the title (under 70 characters), the
description (what it shows, link to `notes.md` or the repo, chapters for long videos,
music attribution if any), tags, playlist, the caption list, and the upload date.
Thumbnails come from a still frame in `images/` (`make frame`), with a short title
overlay for feature videos. Cut a feature video's best mechanism into a Short that
points to the full video.

## Later

- **Feature video (3-5 min, 16:9):** the main animation with captions covers the
  caption and audio flow. A full feature still needs chapters, an intro and end card,
  and a thumbnail. Validate the 16:9 flow on one topic first.
- **Synthetic voice (optional):** if captions alone are not enough, evaluate
  `manim-voiceover` with a local TTS such as Kokoro or Piper. Keep the same caption
  text and timings for the `.srt`, drive animation timing from clip length, duck the
  music under speech with ffmpeg `sidechaincompress`, and cache clips by hash of text
  and voice. Check each provider's commercial-use terms. No own-voice recording.
- **Phone check still open for the first Short:** listen with sound on and off, and
  confirm caption and title overlay positions on a real phone.
