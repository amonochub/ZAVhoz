#!/bin/bash

# ZAVhoz Bot - Local Development Runner
# This script sets up and runs the bot locally

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║         🚀 ZAVhoz Bot - Local Development Startup 🚀          ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check virtual environment
echo "📦 Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3.11 -m venv venv || python3 -m venv venv
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

# Step 2: Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -q -e ".[dev]" 2>/dev/null || pip install -q -e .

# Step 3: Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Step 4: Initialize database
echo ""
echo "🗄️  Initializing database..."
python -c "
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
print(f'✅ Database URL: {db_url}')

# Create tables
try:
    from database.migrations import create_tables
    create_tables()
    print('✅ Database tables created successfully!')
except Exception as e:
    print(f'⚠️  Database setup: {e}')
"

# Step 5: Verify configuration
echo ""
echo "🔧 Verifying configuration..."
python -c "
import os
from dotenv import load_dotenv

load_dotenv()
bot_token = os.getenv('BOT_TOKEN', '')
admin_id = os.getenv('ADMIN_USER_ID', '')

if not bot_token or bot_token.startswith('YOUR_'):
    print('❌ BOT_TOKEN not configured in .env')
    exit(1)

print(f'✅ BOT_TOKEN: {bot_token[:20]}...')
print(f'✅ ADMIN_USER_ID: {admin_id}')
"

# Step 6: Run tests
echo ""
echo "🧪 Running quick tests..."
pytest tests/ -q --tb=no 2>/dev/null | tail -3 || echo "⚠️  Tests: run manually with 'pytest'"

# Step 7: Start bot
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🤖 Starting ZAVhoz Bot..."
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Logging output:"
echo ""

python bot/main.py
