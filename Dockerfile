# Dockerfile

FROM python:3.11-slim

# Install system dependencies for pydub (ffmpeg) and cleanup
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your application files
COPY . .

# Set the port for Render
ENV PORT 8000
EXPOSE 8000

# Start the app with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
