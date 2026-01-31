#!/bin/bash
# Setup script for Assura backend

echo "Setting up Assura backend..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate encryption key if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Generating encryption key..."
    python3 scripts/generate_key.py >> .env
    echo ""
    echo "Please complete your .env file with:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_KEY"
    echo "  - SUPABASE_SERVICE_ROLE_KEY"
    echo "  - SUPABASE_DB_URL"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - REDIS_URL (optional, defaults to redis://localhost:6379/0)"
else
    echo ".env file already exists"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Complete your .env file with all required variables"
echo "2. Run the database migration: migrations/schema.sql in Supabase SQL Editor"
echo "3. Start Redis: redis-server"
echo "4. Start the API: uvicorn app.main:app --reload"
echo "5. Start the worker: celery -A app.celery_app worker --loglevel=info"
