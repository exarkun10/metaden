from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import re
import json
import httpx
from pathlib import Path
from datetime import datetime

app = FastAPI(title="MetaDen Movie Renamer", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "/config/metaden_config.json"))
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "rename_format": "<title> (<year>).<imdb>",
    "rename_aka_format": "<aka> (<title>) (<year>).<imdb>",
    "download_posters": True,
    "create_url_file": True,
    "rename_folder": False,
    "remove_the": False,
    "swap_the": False,
    "replace_spaces_with": "",
    "saved_part_separator": ".",
    "movie_extensions": ["mkv", "avi", "wmv", "mp4", "m4v", "mov", "ts", "m2ts", "ogm", "mpg", "mpeg", "flv", "iso"],
    "subtitle_extensions": ["srt", "sub", "idx"],
    "noise_codecs":  ["H264","H265","X264","X265","HEVC","AVC","XVID","DIVX","AV1","VP9"],
    "noise_sources": ["WEB","WEBDL","WEBRIP","BLURAY","BDRIP","BDREMUX","HDRIP","HDTV","DVDRIP","AMZN","NF","DSNP","HMAX","ATVP","PCOK","STAN","PMTP"],
    "noise_audio":   ["DDP5","DDP","AAC","DTS","AC3","MULTI","ATMOS","TRUEHD","FLAC","MP3","EAC3","DD5","DDPA"],
    "noise_groups":  [],
    "lower_terms": ["a", "an", "the", "and", "but", "or", "for", "nor",
                    "on", "at", "to", "by", "in", "of", "up", "as"],
    "max_undos": 200,
    "subtitle_language": "en",
    "tmdb_api_key": "bb81778a56280ab7f28d2048dfdbec88",
    "undo_list": [],
    "last_folder": "",
    "recently_used_folders": []
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                saved = json.load(f)
            cfg = {**DEFAULT_CONFIG, **saved}
        except Exception:
            cfg = dict(DEFAULT_CONFIG)
    else:
        cfg = dict(DEFAULT_CONFIG)

    # Environment variables always take precedence over saved config
    if os.environ.get("TMDB_API_KEY"):
        cfg["tmdb_api_key"] = os.environ["TMDB_API_KEY"]
    if os.environ.get("OMDB_API_KEY"):
        cfg["omdb_api_key"] = os.environ["OMDB_API_KEY"]
    if os.environ.get("OPENSUBTITLES_API_KEY"):
        cfg["opensubtitles_api_key"] = os.environ["OPENSUBTITLES_API_KEY"]

    return cfg


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ── Models ────────────────────────────────────────────────────────────────────

class FilePart(BaseModel):
    part: str
    state: str  # 'part' | 'remove'


class MovieResult(BaseModel):
    tt: str
    title: str
    year: str
    rating: Optional[str] = ""
    directors: Optional[str] = ""
    director: Optional[str] = ""
    genres: Optional[str] = ""
    genre: Optional[str] = ""
    stars: Optional[str] = ""
    star1: Optional[str] = ""
    duration: Optional[str] = ""
    mpaa: Optional[str] = ""
    aka: List[str] = []
    type: Optional[str] = ""


class RenameRequest(BaseModel):
    original_path: str
    new_name: str
    poster_url: Optional[str] = None
    create_url_file: Optional[bool] = None
    movie_tt: Optional[str] = None
    folder_name: Optional[str] = None
    original_folder_name: Optional[str] = None


class ConfigUpdate(BaseModel):
    config: dict


class UndoAction(BaseModel):
    action: str  # 'rename' | 'delete'
    from_path: Optional[str] = None
    to_path: Optional[str] = None


# ── File Scanning ─────────────────────────────────────────────────────────────

PART_SPLITTER = re.compile(r'[\.\s\-_\[\]\(\)]+')
YEAR_RE = re.compile(r'\b((?:19|20)\d{2})\b')
TT_RE = re.compile(r'tt\d{5,}')
RATING_RE = re.compile(r'^\d\.?\d$')
PART_720 = re.compile(r'(.+)720p*$', re.IGNORECASE)
PART_1080 = re.compile(r'(.+)1080p*$', re.IGNORECASE)


def parse_filename(name: str, config: dict) -> tuple[list[FilePart], Optional[str], Optional[str]]:
    """Parse a filename into parts with states. Returns (parts, tt, year)."""


    raw_parts = PART_SPLITTER.split(name)
    # remove empty
    raw_parts = [p for p in raw_parts if p]

    found_tt = None
    found_year = None
    set_rest_remove = False
    parts: list[FilePart] = []

    # Remove the last part only if it matches a known extension
    KNOWN_EXTENSIONS = {
        "mkv","avi","mp4","mov","wmv","ts","m2ts","mpg","mpeg","flv","iso",
        "rmvb","ogm","m4v","srt","sub","idx","nfo","jpg","png","url"
    }
    ext_idx = len(raw_parts)
    if raw_parts and raw_parts[-1].lower() in KNOWN_EXTENSIONS:
        ext_idx = len(raw_parts) - 1

    for i, part in enumerate(raw_parts[:ext_idx]):
        part_lower = part.lower()
        state = "remove" if set_rest_remove else "part"

        if state != "remove":
            # Check year
            year_m = YEAR_RE.match(part)
            if year_m and int(year_m.group(1)) > 1900:
                state = "remove"
                found_year = year_m.group(1)
            # Check tt#####
            tt_m = TT_RE.search(part)
            if tt_m and not found_tt:
                found_tt = tt_m.group(0)
                state = "remove"
            # Remove literal template tokens leftover from previous renames
            if re.match(r'^<[a-z0-9]+>$', part_lower):
                state = "remove"
            # Remove resolution tokens — not useful for IMDB searching
            if re.match(r'^(4k|2160p?|1080p?|720p?|480p?|576p?|8k|uhd|hd|fhd|qhd)$', part_lower):
                state = "remove"
            # Remove noise words from user-configured lists
            part_upper = part.upper()
            all_noise = (
                [t.upper() for t in config.get("noise_codecs",  [])] +
                [t.upper() for t in config.get("noise_sources", [])] +
                [t.upper() for t in config.get("noise_audio",   [])] +
                [t.upper() for t in config.get("noise_groups",  [])]
            )
            if part_upper in all_noise:
                state = "remove"

        parts.append(FilePart(part=part, state=state))

    return parts, found_tt, found_year


TT_IN_FILENAME = re.compile(r'tt\d{5,}', re.IGNORECASE)

EXTRAS_FOLDERS = {
    "extras", "extra", "featurettes", "featurette", "behind the scenes",
    "interviews", "interview", "scenes", "shorts", "trailers", "trailer",
    "specials", "special", "sample", "samples", "bonus", "bonuses",
    "deleted scenes", "deleted", "making of", "bts"
}

@app.get("/api/files")
async def list_files(folder: str, recursive: bool = True, hide_renamed: bool = False, hide_extras: bool = False):
    """List movie files grouped by parent folder."""
    cfg = load_config()
    extensions = set(cfg.get("movie_extensions", []))
    path = Path(folder)
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail="Folder not found")

    # Collect all matching files
    raw_files = []
    for f in sorted(path.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lstrip(".").lower() not in extensions:
            continue
        # Check if any part of the path (relative to root) is an extras folder
        rel = f.relative_to(path)
        parts = rel.parts
        is_extras = any(p.lower().strip() in EXTRAS_FOLDERS for p in parts[:-1])
        if hide_extras and is_extras:
            continue
        raw_files.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "extension": f.suffix.lstrip(".").lower(),
            "already_renamed": bool(TT_IN_FILENAME.search(f.stem)),
            "is_extras": is_extras,
            "parent": str(f.parent),
            "parent_name": f.parent.name if f.parent != path else "",
        })

    # Build a nested tree: top-level group -> movie subfolders -> files
    from collections import defaultdict

    # Each file gets a movie_folder key = its direct parent if that parent
    # is not an extras folder, otherwise its grandparent
    def get_movie_folder(f):
        rel = Path(f["path"]).relative_to(path)
        parts = rel.parts
        if len(parts) == 1:
            return ("", "")  # root level file
        # top_group = first dir component
        top = parts[0]
        if len(parts) == 2:
            # directly inside top group, not in a movie subfolder
            return (top, "")
        # parts[1] might be a movie folder or an extras folder
        if parts[1].lower().strip() in EXTRAS_FOLDERS:
            return (top, "")
        # parts[1] is a movie folder
        movie = parts[1]
        return (top, movie)

    # group_key -> movie_key -> [files]
    tree = defaultdict(lambda: defaultdict(list))
    for f in raw_files:
        top, movie = get_movie_folder(f)
        tree[top][movie].append(f)

    result_groups = []
    for top_name in sorted(tree.keys()):
        movie_map = tree[top_name]
        top_movies = []

        for movie_name in sorted(movie_map.keys()):
            files = movie_map[movie_name]
            main_files = [f for f in files if not f["is_extras"]]
            extras_files = [f for f in files if f["is_extras"]]
            main_feature = max(main_files, key=lambda f: f["size"]) if main_files else None

            if hide_renamed and main_files and all(f["already_renamed"] for f in main_files):
                continue
            if hide_renamed:
                files = [f for f in files if f["is_extras"] or not f["already_renamed"]]
                main_files = [f for f in files if not f["is_extras"]]
                if not main_files and not files:
                    continue

            top_movies.append({
                "movie": movie_name,
                "path": str(path / top_name / movie_name) if movie_name else str(path / top_name),
                "files": files,
                "main_feature": main_feature,
                "has_extras": len(extras_files) > 0,
                "file_count": len(main_files),
            })

        if not top_movies:
            continue

        result_groups.append({
            "group": top_name,
            "path": str(path / top_name) if top_name else str(path),
            "movies": top_movies,
            # flat files list for compatibility
            "files": [f for m in top_movies for f in m["files"]],
            "main_feature": top_movies[0]["main_feature"] if top_movies else None,
            "has_extras": any(m["has_extras"] for m in top_movies),
            "file_count": sum(m["file_count"] for m in top_movies),
        })

    return {"groups": result_groups, "folder": str(path), "total_files": len(raw_files)}


@app.get("/api/parse")
async def parse_file(path: str):
    """Parse a filename into searchable parts."""
    cfg = load_config()
    f = Path(path)
    stem = f.stem
    parts, tt, year = parse_filename(stem, cfg)
    return {
        "parts": [p.dict() for p in parts],
        "tt": tt,
        "year": year,
        "filename": f.name,
    }


# ── IMDB / TMDB Search ────────────────────────────────────────────────────────

async def search_imdb(query: str, year: str = "") -> List[dict]:
    """Search IMDB for movies matching query using OMDB API. Handles tt IDs directly."""
    cfg = load_config()
    omdb_key = cfg.get("omdb_api_key", "trilogy")
    results = []

    # If query looks like a tt ID, fetch directly instead of searching
    tt_match = re.match(r'^(tt\d+)$', query.strip(), re.IGNORECASE)
    if tt_match:
        details = await get_movie_details(tt_match.group(1).lower())
        if details:
            results.append({
                "tt": details.get("tt", ""),
                "title": details.get("title", ""),
                "year": str(details.get("year", "")),
                "aka": [],
                "type": "Direct",
            })
        return results

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            url = f"https://www.omdbapi.com/?s={query}&type=movie&apikey={omdb_key}"
            if year:
                url += f"&y={year}"
            r = await client.get(url)
            data = r.json()
            if data.get("Search"):
                for item in data["Search"][:8]:
                    results.append({
                        "tt": item.get("imdbID", ""),
                        "title": item.get("Title", ""),
                        "year": item.get("Year", ""),
                        "aka": [],
                        "type": "Search",
                    })
        except Exception:
            pass

    # If year provided, re-rank: exact year matches first, then others
    if year and results:
        results.sort(key=lambda r: (0 if str(r.get("year", "")).startswith(year) else 1))

    return results


async def get_movie_details(tt: str) -> Optional[dict]:
    """Get full movie details from OMDb by tt ID."""
    cfg = load_config()
    omdb_key = cfg.get("omdb_api_key", "trilogy")
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            url = f"https://www.omdbapi.com/?i={tt}&plot=short&apikey={omdb_key}"
            r = await client.get(url)
            data = r.json()
            if data.get("Response") == "True":
                rating_str = data.get("imdbRating", "0")
                try:
                    rating = str(int(float(rating_str) * 10))
                except Exception:
                    rating = "0"
                return {
                    "tt": data.get("imdbID", tt),
                    "title": data.get("Title", ""),
                    "year": data.get("Year", ""),
                    "rating": rating,
                    "directors": data.get("Director", ""),
                    "director": data.get("Director", "").split(",")[0].strip() if data.get("Director") else "",
                    "genres": data.get("Genre", ""),
                    "genre": data.get("Genre", "").split(",")[0].strip() if data.get("Genre") else "",
                    "stars": data.get("Actors", ""),
                    "star1": data.get("Actors", "").split(",")[0].strip() if data.get("Actors") else "",
                    "duration": data.get("Runtime", "").replace(" min", ""),
                    "mpaa": data.get("Rated", "NR"),
                    "aka": [],
                    "type": "Exact",
                }
        except Exception:
            pass
    return None


@app.get("/api/probe")
async def probe_file(path: str):
    """Run ffprobe on a file to get resolution."""
    import subprocess
    f = Path(path)
    if not f.exists():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                str(f)
            ],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        if output:
            parts = output.split(",")
            if len(parts) >= 2:
                width = int(parts[0])
                height = int(parts[1])
                # Map to standard resolution labels using width as primary
                # indicator to handle widescreen crops (e.g. 1920x800 = 1080p)
                if width >= 7680 or height >= 4320:
                    label = "4320p"
                elif width >= 3840 or height >= 2160:
                    label = "2160p"
                elif width >= 1800 or height >= 1080:
                    label = "1080p"
                elif width >= 1100 or height >= 720:
                    label = "720p"
                elif width >= 720 or height >= 480:
                    label = "480p"
                else:
                    label = f"{height}p"
                return {"width": width, "height": height, "label": label}
    except Exception as e:
        pass
    return {"width": None, "height": None, "label": ""}


@app.get("/api/search")
async def search_movies(query: str, year: str = ""):
    results = await search_imdb(query, year)
    return {"results": results}


@app.get("/api/movie/{tt}")
async def get_movie(tt: str):
    movie = await get_movie_details(tt)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.get("/api/posters/{tt}")
async def get_posters(tt: str):
    """Get poster images from TMDB."""
    cfg = load_config()
    api_key = cfg.get("tmdb_api_key", "bb81778a56280ab7f28d2048dfdbec88")
    posters = []

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Get TMDB config
            cfg_url = f"https://api.themoviedb.org/3/configuration?api_key={api_key}"
            cfg_r = await client.get(cfg_url)
            tmdb_cfg = cfg_r.json()
            base_url = tmdb_cfg.get("images", {}).get("base_url", "https://image.tmdb.org/t/p/")

            # Get images by IMDB ID
            url = f"https://api.themoviedb.org/3/movie/{tt}/images?api_key={api_key}"
            r = await client.get(url)
            data = r.json()

            all_posters = data.get("posters") or []
            # Sort: English first, then by vote count descending
            def poster_sort_key(p):
                lang = p.get("iso_639_1", "")
                vote = p.get("vote_count", 0)
                return (0 if lang == "en" else 1 if lang else 2, -vote)
            all_posters.sort(key=poster_sort_key)

            for poster in all_posters[:12]:
                file_path = poster.get("file_path", "")
                if file_path:
                    posters.append({
                        "thumb": base_url + "w185" + file_path,
                        "full": base_url + "w500" + file_path,
                        "original": base_url + "original" + file_path,
                        "file_path": file_path,
                        "width": poster.get("width"),
                        "height": poster.get("height"),
                        "lang": poster.get("iso_639_1", ""),
                    })
        except Exception as e:
            pass

    return {"posters": posters}


# ── Rename Engine ─────────────────────────────────────────────────────────────

def clean_title(title: str, allow_slashes: bool = False) -> str:
    title = title.strip()
    title = re.sub(r': ?', ' - ', title)
    title = title.replace('?', '')
    title = title.replace('*', '')
    if not allow_slashes:
        title = title.replace('/', ' - ')
        title = title.replace('\\', ' - ')
    title = title.replace('"', '')
    title = re.sub(r'  +', ' ', title)
    title = re.sub(r'\.$', '', title)
    return title.strip()


def parse_format(fmt: str, movie: dict, ext: str, cfg: dict) -> str:
    title = movie.get("title", "")
    cfg_remove_the = cfg.get("remove_the", False)
    cfg_swap_the = cfg.get("swap_the", False)
    the = cfg.get("the", "The")
    replace_spaces = cfg.get("replace_spaces_with", "")

    if (cfg_remove_the or cfg_swap_the) and title.lower().startswith(the.lower() + " "):
        title = title[len(the) + 1:]
        if cfg_swap_the:
            title += f", {the}"

    if replace_spaces and replace_spaces != " ":
        title = re.sub(r'\s', replace_spaces, title)

    aka = ""
    if movie.get("aka") and ("<a>" in fmt or "<aka>" in fmt):
        aka = movie["aka"][0] if isinstance(movie["aka"], list) and movie["aka"] else str(movie.get("aka", ""))
        fmt = fmt.replace("<a>", aka).replace("<aka>", aka)

    fmt = fmt.replace("<t>", title).replace("<title>", title)
    fmt = fmt.replace("<y>", movie.get("year", "")).replace("<year>", movie.get("year", ""))
    fmt = fmt.replace("<tt>", movie.get("tt", "")).replace("<imdb>", movie.get("tt", ""))
    rating100 = movie.get("rating", "0")
    try:
        rating_decimal = f"{int(rating100) / 10:.1f}"
    except Exception:
        rating_decimal = "0.0"
    fmt = fmt.replace("<r100>", rating100).replace("<rating100>", rating100)
    fmt = fmt.replace("<rating>", rating_decimal).replace("<r>", rating_decimal)
    fmt = fmt.replace("<d>", movie.get("directors", "")).replace("<directors>", movie.get("directors", ""))
    fmt = fmt.replace("<d1>", movie.get("director", "")).replace("<director>", movie.get("director", ""))
    fmt = fmt.replace("<g>", movie.get("genres", "")).replace("<genres>", movie.get("genres", ""))
    fmt = fmt.replace("<g1>", movie.get("genre", "")).replace("<genre>", movie.get("genre", ""))
    fmt = fmt.replace("<stars>", movie.get("stars", ""))
    fmt = fmt.replace("<star1>", movie.get("star1", ""))
    fmt = fmt.replace("<duration>", movie.get("duration", "")).replace("<time>", movie.get("duration", ""))
    fmt = fmt.replace("<c>", movie.get("mpaa", "")).replace("<mpaa>", movie.get("mpaa", ""))

    fmt = fmt.replace("<saved>", "").replace("<s>", "")
    # Only substitute scanres if it was actually scanned, otherwise remove the token
    scanres_val = movie.get("scanres", "")
    fmt = fmt.replace("<scanres>", scanres_val)

    # Clean up artifacts from empty token substitutions (double dots, trailing dots, double spaces)
    fmt = re.sub(r'\.{2,}', '.', fmt)
    fmt = re.sub(r'\s{2,}', ' ', fmt)
    fmt = re.sub(r'\.\s|\s\.', '.', fmt)
    fmt = fmt.strip('.')

    if ext:
        if not fmt.endswith("."):
            fmt += "."
        fmt += ext.lower()
    else:
        fmt = re.sub(r'\.+$', '', fmt)

    return clean_title(fmt, allow_slashes=bool(ext))


@app.post("/api/preview-rename")
async def preview_rename(body: dict):
    """Preview what the new filename will be."""
    cfg = load_config()
    movie = body.get("movie", {})
    parts = body.get("parts", [])
    original_path = body.get("original_path", "")
    use_aka = body.get("use_aka", False)

    f = Path(original_path)
    ext = f.suffix.lstrip(".")
    fmt = cfg.get("rename_aka_format" if use_aka else "rename_format",
                  "<title> (<year>).<imdb>(<rating>).<saved>")

    new_name = parse_format(fmt, movie, ext, cfg)
    return {"new_name": new_name}


@app.post("/api/rename")
async def rename_file(req: RenameRequest):
    """Perform the actual file rename + optional poster download + url file."""
    cfg = load_config()
    orig = Path(req.original_path)
    if not orig.exists():
        raise HTTPException(status_code=404, detail="Original file not found")

    new_path = orig.parent / req.new_name
    undo_actions = []

    # Rename the main file
    if new_path != orig:
        if new_path.exists():
            raise HTTPException(status_code=409, detail=f"File already exists: {req.new_name}")
        orig.rename(new_path)
        undo_actions.append({"action": "rename", "from_path": str(new_path), "to_path": str(orig)})

    # Rename containing folder if enabled
    if cfg.get("rename_folder", False) and req.folder_name:
        parent = new_path.parent
        # Only rename if parent is not /media or root mount
        if parent.parent != Path("/") and parent.name != "media":
            new_folder = parent.parent / req.folder_name
            if not new_folder.exists():
                parent.rename(new_folder)
                undo_actions.append({"action": "rename", "from_path": str(new_folder), "to_path": str(parent)})
                new_path = new_folder / new_path.name

    # Write release info file
    if req.original_folder_name:
        info_path = new_path.parent / "release_info.txt"
        try:
            # Preserve any subtitle lines already written (e.g. sub downloaded before rename)
            existing_subtitle_lines = []
            if info_path.exists():
                for line in info_path.read_text().splitlines():
                    if line.startswith("Subtitles:"):
                        existing_subtitle_lines.append(line)
            info_lines = [
                f"Original folder: {req.original_folder_name}",
                f"Original filename: {orig.name}",
                f"Renamed to: {req.new_name}",
                f"Renamed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            if req.movie_tt:
                info_lines.append(f"IMDB: https://www.imdb.com/title/{req.movie_tt}/")
            info_lines.extend(existing_subtitle_lines)
            info_path.write_text("\n".join(info_lines) + "\n")
            undo_actions.append({"action": "delete", "to_path": str(info_path)})
        except Exception:
            pass

    # Download poster
    if req.poster_url and cfg.get("download_posters"):
        poster_path = new_path.parent / (new_path.stem + ".jpg")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(req.poster_url)
                if r.status_code == 200:
                    poster_path.write_bytes(r.content)
                    undo_actions.append({"action": "delete", "to_path": str(poster_path)})
        except Exception:
            pass

    # Create .url file
    create_url = req.create_url_file if req.create_url_file is not None else cfg.get("create_url_file", True)
    if create_url and req.movie_tt:
        url_path = new_path.parent / (new_path.stem + ".url")
        try:
            url_content = f"[InternetShortcut]\nURL=https://www.imdb.com/title/{req.movie_tt}/\n"
            url_path.write_text(url_content)
            undo_actions.append({"action": "delete", "to_path": str(url_path)})
        except Exception:
            pass

    # Rename any MetaDen-downloaded subtitle files that match the original stem
    orig_stem = orig.stem
    new_stem = new_path.stem
    if orig_stem != new_stem:
        for srt in new_path.parent.glob("*.srt"):
            if srt.name.startswith(orig_stem + "."):
                # e.g. OldName.en.srt → NewName.en.srt
                #      OldName.en.generic.srt → NewName.en.generic.srt
                suffix = srt.name[len(orig_stem):]  # e.g. ".en.srt" or ".en.generic.srt"
                new_srt = new_path.parent / (new_stem + suffix)
                try:
                    srt.rename(new_srt)
                    undo_actions.append({"action": "rename", "from_path": str(new_srt), "to_path": str(srt)})
                except Exception:
                    pass

    # Record undo
    undo_list: list = cfg.get("undo_list", [])
    undo_list.append({
        "timestamp": datetime.now().isoformat(),
        "actions": undo_actions,
        "description": f"Renamed {orig.name} → {req.new_name}"
    })
    max_undos = cfg.get("max_undos", 200)
    if len(undo_list) > max_undos:
        undo_list = undo_list[-max_undos:]
    cfg["undo_list"] = undo_list
    save_config(cfg)

    return {"success": True, "new_path": str(new_path)}


@app.post("/api/undo")
async def undo_last():
    """Undo the last rename operation."""
    cfg = load_config()
    undo_list: list = cfg.get("undo_list", [])
    if not undo_list:
        raise HTTPException(status_code=400, detail="Nothing to undo")

    transaction = undo_list.pop()
    errors = []

    for action in reversed(transaction.get("actions", [])):
        try:
            if action["action"] == "rename":
                src = Path(action["from_path"])
                dst = Path(action["to_path"])
                if src.exists():
                    src.rename(dst)
            elif action["action"] == "delete":
                p = Path(action["to_path"])
                if p.exists():
                    p.unlink()
        except Exception as e:
            errors.append(str(e))

    cfg["undo_list"] = undo_list
    save_config(cfg)

    return {"success": True, "errors": errors, "description": transaction.get("description")}


# ── Config API ────────────────────────────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    cfg = load_config()
    # don't send undo_list or raw api keys in config response
    safe = {k: v for k, v in cfg.items() if k not in ("undo_list", "opensubtitles_api_key")}
    safe["has_opensubtitles_key"] = bool(cfg.get("opensubtitles_api_key", ""))
    return safe


@app.post("/api/config")
async def update_config(body: ConfigUpdate):
    cfg = load_config()
    cfg.update(body.config)
    save_config(cfg)
    return {"success": True}


@app.get("/api/undo-history")
async def get_undo_history():
    cfg = load_config()
    undo_list = cfg.get("undo_list", [])
    return {"history": [{"timestamp": u["timestamp"], "description": u["description"]} for u in undo_list[-20:]]}


@app.get("/api/folders")
async def list_folders(path: str):
    """List subdirectories at a given path for folder browsing."""
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail="Path not found")

    folders = []
    try:
        for item in sorted(p.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                # Count video files inside (non-recursive) to give a hint
                try:
                    cfg = load_config()
                    extensions = set(cfg.get("movie_extensions", []))
                    file_count = sum(1 for f in item.rglob("*")
                                     if f.is_file() and f.suffix.lstrip(".").lower() in extensions)
                except Exception:
                    file_count = 0
                folders.append({
                    "name": item.name,
                    "path": str(item),
                    "file_count": file_count,
                })
    except PermissionError:
        pass
    return {"folders": folders, "path": str(p), "parent": str(p.parent) if p.parent != p else None}


@app.get("/api/media-path")
async def get_media_path():
    """Return the MEDIA_PATH env var and mount hint for the frontend."""
    return {"media_path": os.environ.get("MEDIA_PATH", "/media")}


class SubtitleDownloadRequest(BaseModel):
    folder: str
    file_id: int
    movie_stem: str          # e.g. "Alien Romulus (2024).tt18412256"
    language: str            # e.g. "en"
    match_type: str          # "release" or "generic"
    release_name: str        # original release name for release_info.txt


# ── Subtitle Support ──────────────────────────────────────────────────────────

OPENSUBTITLES_API_URL = "https://api.opensubtitles.com/api/v1"
OPENSUBTITLES_APP_NAME = "MetaDen/1.1"


def read_release_info(folder: str) -> dict:
    """Parse release_info.txt from a folder. Returns dict with available fields."""
    info = {}
    info_path = Path(folder) / "release_info.txt"
    if not info_path.exists():
        return info
    try:
        for line in info_path.read_text().splitlines():
            if line.startswith("Original folder:"):
                info["original_folder"] = line.split(":", 1)[1].strip()
            elif line.startswith("Original filename:"):
                info["original_filename"] = line.split(":", 1)[1].strip()
            elif line.startswith("Renamed to:"):
                info["renamed_to"] = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return info


def append_release_info(folder: str, line: str):
    """Append a line to release_info.txt."""
    info_path = Path(folder) / "release_info.txt"
    try:
        with open(info_path, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


@app.get("/api/subtitles/search")
async def search_subtitles(folder: str, language: str = "en"):
    """Search OpenSubtitles for subtitles matching this movie folder."""
    cfg = load_config()
    api_key = cfg.get("opensubtitles_api_key", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenSubtitles API key not configured")

    # Try release_info.txt first, fall back to folder name
    info = read_release_info(folder)
    release_name = info.get("original_folder") or info.get("original_filename", "")

    # Fall back: use folder name itself (for Zeeb-renamed or hand-renamed files)
    if not release_name:
        release_name = Path(folder).name

    # Strip extension from release_name if present
    release_stem = Path(release_name).stem if "." in release_name else release_name

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": OPENSUBTITLES_APP_NAME,
    }

    results = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            params = {
                "query": release_stem,
                "languages": language,
                "type": "movie",
            }
            r = await client.get(f"{OPENSUBTITLES_API_URL}/subtitles", headers=headers, params=params)
            if r.status_code != 200:
                raise HTTPException(status_code=500, detail=f"OpenSubtitles API error {r.status_code}: {r.text[:200]}")
            data = r.json()

            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                files = attrs.get("files", [])
                if not files:
                    continue

                # Determine match type — exact release name match = "release", else "generic"
                sub_release = attrs.get("release", "")
                is_release_match = (
                    release_stem.lower().strip() == sub_release.lower().strip()
                    if sub_release else False
                )

                results.append({
                    "id": item.get("id"),
                    "file_id": files[0].get("file_id"),
                    "release": sub_release,
                    "language": attrs.get("language", language),
                    "match_type": "release" if is_release_match else "generic",
                    "download_count": attrs.get("download_count", 0),
                    "ratings": attrs.get("ratings", 0),
                    "hearing_impaired": attrs.get("hearing_impaired", False),
                    "fps": attrs.get("fps"),
                    "uploader": attrs.get("uploader", {}).get("name", ""),
                })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenSubtitles search failed: {str(e)}")

    # Score results: release match first, then by token overlap with search term, then download count
    search_tokens = set(re.split(r'[\.\-_\s]+', release_stem.upper()))
    for item in results:
        sub_tokens = set(re.split(r'[\.\-_\s]+', item.get("release", "").upper()))
        item["_score"] = len(search_tokens & sub_tokens)
    results.sort(key=lambda x: (
        0 if x["match_type"] == "release" else 1,
        -x["_score"],
        -x["download_count"]
    ))

    return {
        "results": results,
        "search_term": release_stem,
        "source": "release_info" if info.get("original_folder") else "folder_name",
    }


@app.post("/api/subtitles/download")
async def download_subtitle(req: SubtitleDownloadRequest):
    """Download a subtitle file and place it next to the movie."""
    cfg = load_config()
    api_key = cfg.get("opensubtitles_api_key", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenSubtitles API key not configured")

    folder = Path(req.folder)
    if not folder.exists():
        raise HTTPException(status_code=404, detail="Folder not found")

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": OPENSUBTITLES_APP_NAME,
    }

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # Step 1: Request download link from OpenSubtitles
            r = await client.post(
                f"{OPENSUBTITLES_API_URL}/download",
                headers=headers,
                json={"file_id": req.file_id}
            )
            dl_data = r.json()
            download_link = dl_data.get("link")
            if not download_link:
                raise HTTPException(status_code=500, detail="No download link returned")

            # Step 2: Download the actual .srt content
            srt_r = await client.get(download_link)
            if srt_r.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to download subtitle file")

            # Step 3: Build filename
            # e.g. "Alien Romulus (2024).tt18412256.en.srt"
            #   or "Alien Romulus (2024).tt18412256.en.generic.srt"
            if req.match_type == "release":
                sub_filename = f"{req.movie_stem}.{req.language}.srt"
            else:
                sub_filename = f"{req.movie_stem}.{req.language}.generic.srt"

            sub_path = folder / sub_filename
            sub_path.write_bytes(srt_r.content)

            # Step 4: Append to release_info.txt
            today = datetime.now().strftime("%Y-%m-%d")
            append_release_info(
                str(folder),
                f"Subtitles: {req.release_name}.{req.language}.srt (downloaded {today}, {req.match_type} match)"
            )

            # Step 5: Record undo transaction
            undo_list: list = cfg.get("undo_list", [])
            undo_list.append({
                "timestamp": datetime.now().isoformat(),
                "actions": [{"action": "delete", "to_path": str(sub_path)}],
                "description": f"Downloaded subtitle {sub_filename}",
            })
            max_undos = cfg.get("max_undos", 200)
            if len(undo_list) > max_undos:
                undo_list = undo_list[-max_undos:]
            cfg["undo_list"] = undo_list
            save_config(cfg)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle download failed: {str(e)}")

    return {"success": True, "filename": sub_filename, "full_path": str(sub_path)}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
