# Dockerfile

FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app files
COPY . .

# Expose the port Render uses
ENV PORT 8000
EXPOSE 8000

# Run the app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
