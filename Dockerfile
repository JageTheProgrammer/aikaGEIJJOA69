# Use official Python slim image
FROM python:3.11-slim

# Install ffmpeg (needed for yt-dlp to extract mp3)
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy all files from repo into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (same as your Procfile)
EXPOSE 10000

# Start uvicorn server
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=10000"]
