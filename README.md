# MetaDen v1.40 — Movie File Renamer

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-exarkun10%2Fmetaden-blue)](https://hub.docker.com/r/exarkun10/metaden)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## About

**Zeeb** was originally created by **slaingod** as a desktop application built on **Adobe AIR** and **ActionScript/MXML** — a technology stack from the late 2000s that allowed Flash-based apps to run on the desktop. Zeeb was a clever, lightweight tool that parsed movie filenames, searched IMDB, pulled posters from TMDB, and renamed files using a configurable template system. It was genuinely ahead of its time.

**MetaDen** is a ground-up rebuild of Zeeb for the modern homelab era. Nothing from the original codebase was reused — every line was rewritten using current technologies while preserving the spirit and workflow of the original:

| Layer | Original (Zeeb) | MetaDen |
|---|---|---|
| Runtime | Adobe AIR | Docker |
| Language | ActionScript 3 / MXML | Python 3.12 + JavaScript (ES2024) |
| Backend | n/a (desktop app) | FastAPI |
| Frontend | Adobe Flex / MXML | Vue 3 + Tailwind CSS |
| Build | Adobe Flex SDK | Vite |
| State | ActionScript bindings | Pinia |
| API (IMDB data) | Custom scraper | OMDb REST API |
| API (Posters) | TMDB | TMDB (same) |
| Resolution | Filename parsing only | ffprobe (actual file metadata) |
| Deployment | Windows/Mac installer | Single Docker container |

---

## Features

- **Folder browser** — navigate your media library with a clickable folder tree, back button included
- **3-level file tree** — library → movie folder → files, with extras nested under their parent movie
- **Resizable file panel** — drag to resize the file list to your preference
- **Filename parser** — intelligently splits filenames into searchable parts; click parts to cycle search → keep → remove
- **IMDB search** — searches via OMDb API, auto-selects best match
- **Movie details** — rating, director, genre, cast, runtime, MPAA rating
- **Poster browser** — English posters prioritized, language badges on foreign posters, downloads alongside film
- **Configurable rename format** — token-based with clickable token insertion:
  - `<title>` `<year>` `<imdb>` `<rating>` `<rating100>` `<scanres>` `<directors>` `<genres>` `<stars>` `<duration>` `<mpaa>`
- **Resolution scanning** — uses ffprobe to detect actual video resolution (`720p`, `1080p`, `2160p`) — opt-in, on-demand
- **Folder rename** — optionally renames the containing folder to match
- **Release info file** — writes `release_info.txt` with original folder/filename for subtitle tracking
- **URL file** — creates `.url` shortcut to IMDB page
- **Hide renamed** — filters already-renamed files and folders from the list
- **Extras filtering** — auto-detects extras/featurettes/bonus subfolders, nested under their parent movie
- **Undo** — full undo history with per-operation rollback
- **Auto-scan** — automatically scans `/media` on startup
- **Recent folders** — quick access to previously opened paths, clearable in Settings
- **Settings** — auto-saves on close with unsaved changes prompt, restore to defaults option
- **About** — version info, links, license, and origins

---

## Quick Start — Unraid

### Option A — Manual Docker install

In Unraid **Docker** tab → **Add Container** → Advanced View:

| Field | Value |
|---|---|
| Repository | `exarkun10/metaden:latest` |
| Network | your docker network |
| WebUI | `http://[IP]:[PORT:8265]` |

**Ports:**
- Container `8265` → Host `8265` (TCP)

**Paths:**
- Container `/config` → Host `/mnt/user/appdata/metaden` (RW)
- Container `/media` → Host `/mnt/user/data/movies` (RW) — point this at your movies folder

**Variables:**
| Variable | Value |
|---|---|
| `TMDB_API_KEY` | Your TMDB key |
| `OMDB_API_KEY` | Your OMDb key |
| `PUID` | `99` |
| `PGID` | `100` |

### Option B — Import CA template

Copy `metaden-template.xml` to `/boot/config/plugins/dockerMan/templates-user/` on your Unraid server. It will appear in the Add Container template list immediately.

---

## API Keys

Both are free:
- **TMDB** — https://www.themoviedb.org/settings/api (use the API Key, not the read access token)
- **OMDb** — https://www.omdbapi.com/apikey.aspx

---

## Building

```bash
# Multi-platform build (amd64 for Unraid + arm64 for Apple Silicon)
docker buildx create --use --name multibuilder
docker buildx build --platform linux/amd64,linux/arm64 -t exarkun10/metaden:latest --push .

# Run locally for testing
docker run -d \
  -p 8265:8265 \
  -v ~/metaden-config:/config \
  -v ~/Movies:/media \
  -e TMDB_API_KEY=yourkey \
  -e OMDB_API_KEY=yourkey \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  --name metaden \
  exarkun10/metaden:latest
```

## Local Development

```bash
# Backend (hot reload)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (hot reload, separate terminal)
cd frontend
npm install
npm run dev
# http://localhost:5173 (proxies /api to localhost:8000)
# API docs: http://localhost:8000/docs
```

---

## Rename Format Tokens

| Token | Description | Example |
|---|---|---|
| `<title>` | Movie title | `Jaws` |
| `<year>` | Release year | `1975` |
| `<imdb>` | IMDB ID | `tt0073195` |
| `<rating>` | IMDB rating (decimal) | `8.1` |
| `<rating100>` | IMDB rating (×10 integer) | `81` |
| `<scanres>` | Detected resolution (ffprobe) | `1080p` |
| `<directors>` | Director(s) | `Steven Spielberg` |
| `<genres>` | Genres | `Adventure, Horror` |
| `<stars>` | Top cast | `Roy Scheider, Robert Shaw` |
| `<duration>` | Runtime in minutes | `124` |
| `<mpaa>` | MPAA rating | `PG` |

**Default format:** `<title> (<year>).<imdb>`

---

## Credits

Original **Zeeb** concept and implementation by **slaingod**, built with Adobe AIR / ActionScript 3.
MetaDen is an independent reimplementation — all credit for the original idea goes to the original author.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
