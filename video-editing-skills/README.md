# Video editing skills

Every video editing skill in this repo, gathered in one folder. Each subfolder is a
Claude skill: a `SKILL.md` with frontmatter (`name`, `description`) and instructions.

| Skill | Use it for |
|---|---|
| [`papercut-stop-motion-reel`](papercut-stop-motion-reel/SKILL.md) | A 9:16 papercut / stop-motion reel built from still artworks (torn paper, tape, captions on paper strips) |
| [`3d-flipbook-reel`](3d-flipbook-reel/SKILL.md) | A 3D sketchbook that floats in a scene (or over your own footage) and flips through the pages |
| [`instagram-reel-export`](instagram-reel-export/SKILL.md) | Encoding settings, cover frame, caption and checks for a finished Instagram Reel |
| [`ffmpeg-video-editing`](ffmpeg-video-editing/SKILL.md) | Everyday edits with ffmpeg: trim, join, crop to 9:16, speed, music, burned-in captions, overlays, GIFs |
| [`connected-video-tools`](connected-video-tools/SKILL.md) | When to hand a job to the connected Adobe, Descript or Canva tools instead of rendering locally |

## Using them

- **In this repo:** Claude Code loads skills from `.claude/skills/`. To turn these on, copy or
  symlink them: `mkdir -p .claude/skills && cp -r video-editing-skills/* .claude/skills/`
  (skip `README.md`).
- **Everywhere:** copy the subfolders into `~/.claude/skills/`.

The two reel skills drive the renderers at the repo root (`make_video.py`, `make_flipbook.py`),
which read `artworks/` and `fonts/` next to them. Keep those scripts where they are, or copy the
`artworks/` and `fonts/` folders along with them.

Requirements for local rendering: `ffmpeg`, Python 3 with `Pillow` and `numpy`.
