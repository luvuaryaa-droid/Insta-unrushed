---
name: connected-video-tools
description: Pick and use the connected cloud video tools - Descript (text-based editing, filler-word removal, captions, publishing, timeline export to Premiere/Resolve/FCP), Adobe (quick cuts, resize, render, speech enhancement, media summaries) and Canva (motion designs, export). Use when a video needs transcript-driven editing, auto captions, cleaner audio, an editable project in one of those apps, or a share link, rather than a local ffmpeg or Python render.
---

# Connected video tools

These are MCP connectors, so they only work in sessions where the connector is attached. Load each tool with ToolSearch (`select:<tool name>`) before calling it.

## Which tool for which job

| Job | Use |
|---|---|
| Edit a talking-head or voice-over video by its transcript; cut filler words and silences; add captions; rearrange | **Descript**: `import_media`, then `prompt_project_agent` (Descript's editor, called Agent Underlord) with plain instructions |
| Share link or download of the edited video | Descript `publish_project` (always show the returned URLs) |
| Hand the edit to Premiere, DaVinci Resolve, Final Cut or Audition | Descript `export_timeline` → `wait_for_job` → show `download_url` |
| Transcript or `.srt` | Descript `export_transcript` |
| Find an existing project | Descript `search_drive` |
| Fast highlight cut from raw footage | Adobe `video_create_quick_cut` |
| Resize or reframe to another aspect ratio | Adobe `video_resize` |
| Clean up noisy speech | Adobe `media_enhance_speech` |
| Summary of what a clip contains | Adobe `media_summarize` |
| Render or export an Adobe video, or a single frame | Adobe `video_render`, `video_export`, `video_render_frame`, `video_metadata` |
| Animated or motion graphic designs, templates, brand kits | Canva `generate-design`, `edit-design`, `export-design` |

## Rules

- **Adobe:** call `adobe_mandatory_init` once, first, before any other Adobe tool in the conversation.
- **Descript:** for files attached in chat, call `import_media` with `content_type` and `file_size`, then PUT the bytes to the returned `upload_url`. Long jobs return a `job_id`; use `wait_for_job`.
- Uploading sends the footage to that service, so confirm with the person before uploading private material.
- For stylised, fully generated reels from stills (papercut, 3D flip-book), render locally with the `papercut-stop-motion-reel` or `3d-flipbook-reel` skill. Then, if needed, import the MP4 into Descript for captions or music.
