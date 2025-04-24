from fastapi import FastAPI
from fastapi.responses import FileResponse
import subprocess, os, uuid
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/search_download")
def search_and_download(query: str):
    file_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp3")

    command = [
        "yt-dlp",
        f"ytsearch1:{query}",
        "-x", "--audio-format", "mp3",
        "-o", output_path
    ]
    subprocess.run(command, shell=False)

    if os.path.exists(output_path):
        return {"status": "success", "file": f"https://88e9-93-106-1-86.ngrok-free.app/play/{file_id}.mp3"}
    else:
        return {"status": "error", "message": "Download failed"}

@app.get("/play/{filename}")
def play_file(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return FileResponse(filepath, media_type="audio/mpeg")
