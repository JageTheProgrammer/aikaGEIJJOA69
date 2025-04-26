from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid
import threading
import time

def cleanup_downloads():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > 600:  # 600 seconds = 10 minutes
                    print(f"Deleting old file: {filename}")
                    os.remove(filepath)
        time.sleep(300)  # Check every 5 minutes

# Start the cleanup thread when app starts
threading.Thread(target=cleanup_downloads, daemon=True).start()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/download")
def download_audio(query: str):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filepath,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{query}"])

    return {"url": f"/file/{filename}"}

@app.get("/file/{filename}")
def serve_file(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(path=filepath, filename=filename, media_type='audio/mpeg')
    return {"error": "File not found"}
