#!/bin/bash

# Fidelity Agent Assistant - Initial Setup Script

set -e

echo "========================================="
echo "Fidelity Agent Assistant - Setup"
echo "========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3.11+ is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo "✓ Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js 18+ is required but not installed."
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Node.js $NODE_VERSION found"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "WARNING: PostgreSQL not found in PATH. Make sure it's installed."
else
    echo "✓ PostgreSQL found"
fi

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    echo "WARNING: Redis not found in PATH. Make sure it's installed."
else
    echo "✓ Redis found"
fi

echo ""
echo "========================================="
echo "Setting up Backend"
echo "========================================="
echo ""

cd backend

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✓ Using uv for fast installation (10x faster than pip)..."

    # Create virtual environment with uv
    echo "Creating Python virtual environment with uv..."
    uv venv

    # Activate virtual environment
    echo "Activating virtual environment..."
    . .venv/bin/activate

    # Install dependencies with uv
    echo "Installing Python dependencies with uv..."
    uv pip install -r requirements.txt
else
    echo "⚠️  uv not found, using pip (consider installing uv for 10x speed)"
    echo "   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"

    # Create virtual environment
    echo "Creating Python virtual environment..."
    python3 -m venv venv

    # Activate virtual environment
    echo "Activating virtual environment..."
    . venv/bin/activate

    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your configuration!"
else
    echo ".env file already exists, skipping..."
fi

echo "✓ Backend setup complete"

cd ..

echo ""
echo "========================================="
echo "Setting up Frontend"
echo "========================================="
echo ""

cd frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install

# Copy environment file
if [ ! -f .env.local ]; then
    echo "Creating .env.local file from template..."
    cp .env.local.example .env.local
    echo "⚠️  Please edit frontend/.env.local if needed!"
else
    echo ".env.local file already exists, skipping..."
fi

echo "✓ Frontend setup complete"

cd ..

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment variables:"
echo "   - Edit backend/.env with Azure OpenAI credentials"
echo "   - Edit backend/.env with database connection string"
echo ""
echo "2. Start PostgreSQL and Redis:"
echo "   - PostgreSQL: brew services start postgresql (macOS)"
echo "   - Redis: brew services start redis (macOS)"
echo ""
echo "3. Create database:"
echo "   createdb faa_db"
echo ""
echo "4. Run database migrations:"
echo "   cd backend && source venv/bin/activate"
echo "   alembic upgrade head"
echo ""
echo "5. Start the backend:"
echo "   cd backend && source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "6. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "7. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "For more information, see README.md"
echo ""
