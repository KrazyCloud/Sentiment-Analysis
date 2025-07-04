# Dockerfile
FROM python:3.12.3-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose FastAPI port (5011)
EXPOSE 5011

# Start FastAPI server on port 5011
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5011"]
