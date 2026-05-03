#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z $POSTGRESQL_HOST $POSTGRESQL_PORT; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI server
echo "Starting FastAPI server..."
uvicorn main:app --host $WEB_SERVER_HOST --port $WEB_SERVER_PORT
