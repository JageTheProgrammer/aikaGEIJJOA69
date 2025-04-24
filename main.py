from fastapi import FastAPI
from fastapi.responses import FileResponse
import subprocess, os, uuid
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Route to search and download
@app.get("/search_download")
def search_and_download(query: str):
    file_id = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp3")

    # yt-dlp command with cookies-from-browser
    command = [
        "yt-dlp",
        f"ytsearch1:{query}",
        "--cookies-from-browser",  # Automatically uses cookies from browser
        "-x", "--audio-format", "mp3",
        "-o", output_path
    ]
    
    subprocess.run(command, shell=False)

    if os.path.exists(output_path):
        return {"status": "success", "file": f"https://music-t94g.onrender.com/play/{file_id}.mp3"}
    else:
        return {"status": "error", "message": "Download failed"}

# Route to play the file
@app.get("/play/{filename}")
def play_file(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return FileResponse(filepath, media_type="audio/mpeg")
