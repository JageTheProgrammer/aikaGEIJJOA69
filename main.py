from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os, uuid, threading, time

# ——————— Configuration ———————
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——————— Cleanup thread ———————
def cleanup_downloads():
    while True:
        now = time.time()
        for fn in os.listdir(DOWNLOAD_DIR):
            fp = os.path.join(DOWNLOAD_DIR, fn)
            if os.path.isfile(fp) and now - os.path.getmtime(fp) > 600:
                os.remove(fp)
        time.sleep(300)

threading.Thread(target=cleanup_downloads, daemon=True).start()

# ——————— Download endpoint ———————
@app.get("/download")
def download_audio(query: str = Query(..., description="Search term for YouTube")):
    # 1) sanity check the cookies file
    if not os.path.isfile(COOKIES_FILE):
        raise RuntimeError(f"cookies.txt not found at {COOKIES_FILE!r}")
    with open(COOKIES_FILE) as f:
        yt_lines = [l.strip() for l in f if "youtube.com" in l]
    print("▶️ YouTube cookies in file:", yt_lines)

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filepath,
        "quiet": True,
        "noplaylist": True,
        "cookiefile": COOKIES_FILE,
        "http_headers": {
            # A modern desktop Chrome UA—feel free to update to whatever your browser sends
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            ),
            # This helps too
            "Referer": "https://www.youtube.com/"
        },
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])
    except Exception as e:
        return {"status": "error", "message": f"Download failed: {str(e)}"}

    if os.path.exists(filepath):
        return {"status": "success", "url": f"/file/{filename}"}
    return {"status": "error", "message": "File not found after download"}

@app.get("/file/{filename}")
def serve_file(filename: str):
    safe = os.path.basename(filename)
    fp   = os.path.join(DOWNLOAD_DIR, safe)
    if os.path.exists(fp):
        return FileResponse(fp, media_type="audio/mpeg")
    return {"error": "File not found"}
