FROM python:3.11.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files into container
COPY . .

# Expose port
EXPOSE 8000

# Start app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
