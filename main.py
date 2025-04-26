from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid
import threading
import time

# 1. Create your download folder up front
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 2. Background cleanup thread
def cleanup_downloads():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > 600:  # older than 10 minutes
                    print(f"Deleting old file: {filename}")
                    os.remove(filepath)
        time.sleep(300)  # run every 5 minutes

threading.Thread(target=cleanup_downloads, daemon=True).start()

# 3. FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/download")
def download_audio(query: str = Query(..., description="Search term for YouTube")):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filepath,
        'quiet': False,
        'noplaylist': True,
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'verbose': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Searching for: {query}")
            result = ydl.download([f"ytsearch1:{query}"])
            if result != 0:
                return {"status": "error", "message": "No results found for the song."}
    except Exception as e:
        print(f"Download failed: {str(e)}")
        return {"status": "error", "message": f"Download failed: {str(e)}"}

    if os.path.exists(filepath):
        print(f"File downloaded: {filepath}")
        return {"status": "success", "url": f"/file/{filename}"}
    else:
        print("File not found after download.")
        return {"status": "error", "message": "Music not found or failed to download."}

@app.get("/file/{filename}")
def serve_file(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    else:
        return {"error": "File not found"}
