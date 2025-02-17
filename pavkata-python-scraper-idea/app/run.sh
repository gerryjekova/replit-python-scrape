
#!/bin/bash

# Install required packages if not already installed
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    pip install redis
fi

if ! command -v uvicorn &> /dev/null; then
    echo "Installing FastAPI and Uvicorn..."
    pip install fastapi uvicorn[standard]
fi

# Start Redis server in the background
redis-server --daemonize yes

# Wait and verify Redis is running
for i in {1..5}; do
  if redis-cli ping > /dev/null 2>&1; then
    echo "Redis server started successfully"
    break
  fi
  if [ $i -eq 5 ]; then
    echo "Failed to start Redis server"
    exit 1
  fi
  sleep 1
done
echo "Starting services..."

# Stop any existing Redis server
echo "Checking for existing Redis server..."
if pgrep redis-server > /dev/null; then
    echo "Stopping existing Redis server..."
    pkill redis-server
    sleep 2
fi

# Start Redis with our configuration
echo "Starting Redis server..."
redis-server redis.conf

# Wait for Redis to start
echo "Waiting for Redis to start..."
until redis-cli ping > /dev/null 2>&1; do
    sleep 1
done
echo "Redis is running!"

# Start the FastAPI application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start FastAPI application
cd pavkata-python-scraper-idea && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Start the application
/run.sh

# In another terminal, run the test script
python test_scraper.py

