#!/bin/bash
# .devcontainer/post-create.sh
# Post-creation script for AVCS DNA development container

set -e  # Exit on error

echo "🚀 AVCS DNA Post-Creation Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    echo -e "${2}${1}${NC}"
}

# Check Python version
print_color "📊 Checking Python version..." "$BLUE"
python --version
pip --version

# Install dependencies
print_color "📦 Installing Python dependencies..." "$BLUE"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create necessary directories
print_color "📁 Creating project directories..." "$BLUE"
mkdir -p data logs models .streamlit

# Create .env if not exists
if [ ! -f .env ]; then
    print_color "🔧 Creating .env file from example..." "$BLUE"
    cp .env.example .env 2>/dev/null || echo "# Environment variables" > .env
fi

# Create Streamlit config
print_color "⚙️ Configuring Streamlit..." "$BLUE"
cat > .streamlit/config.toml << EOF
[theme]
primaryColor = "#1e3c72"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 10
enableCORS = true
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF

# Initialize git hooks
if [ -d .git ]; then
    print_color "🔄 Setting up git hooks..." "$BLUE"
    
    # Pre-commit hook for Python
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🔍 Running pre-commit checks..."
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
if [ -n "$files" ]; then
    black --check $files || exit 1
    flake8 $files || exit 1
fi
EOF
    chmod +x .git/hooks/pre-commit
fi

# Test the application
print_color "🧪 Testing application import..." "$BLUE"
python -c "
import sys
try:
    from modules import *
    print('✅ Modules imported successfully')
    from utils import *
    print('✅ Utils imported successfully')
    print('🎯 All imports successful!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Check if app.py exists
if [ -f app.py ]; then
    print_color "✅ app.py found" "$GREEN"
else
    print_color "⚠️ app.py not found" "$YELLOW"
fi

# Print summary
print_color "\n📋 Environment Summary:" "$BLUE"
print_color "   Python: $(python --version | cut -d' ' -f2)" "$GREEN"
print_color "   Working Dir: $(pwd)" "$GREEN"
print_color "   User: $(whoami)" "$GREEN"

print_color "\n🎉 Setup complete! Run 'streamlit run app.py' to start" "$GREEN"
print_color "📊 Streamlit will be available at http://localhost:8501" "$GREEN"
