#!/bin/bash

echo "Starting FastAPI application..."

# Install dependencies
pip install -r requirements.txt

# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload