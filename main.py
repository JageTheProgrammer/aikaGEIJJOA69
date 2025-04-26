from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid
import threading
import time

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def cleanup_downloads():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > 600:  # 10 minutes
                    print(f"Deleting old file: {filename}")
                    os.remove(filepath)
        time.sleep(300)  # every 5 minutes

threading.Thread(target=cleanup_downloads, daemon=True).start()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later tighten to your frontend URL
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
        'quiet': True,  # Set to True for less logs, remove 'verbose'
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Searching and downloading: {query}")
            result = ydl.download([f"ytsearch1:{query}"])
            if result != 0:
                return {"status": "error", "message": "No results found for the song."}

        if os.path.exists(filepath):
            print(f"File ready: {filepath}")
            return {"status": "success", "url": f"/file/{filename}"}
        else:
            print("File missing after download attempt.")
            return {"status": "error", "message": "Music not found or failed to download."}

    except Exception as e:
        print(f"Download error: {str(e)}")
        return {"status": "error", "message": f"Download failed: {str(e)}"}

@app.get("/file/{filename}")
def serve_file(filename: str):
    filename = os.path.basename(filename)  # sanitize filename
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    else:
        return {"error": "File not found"}
