#!/bin/bash
# MyOS Quick Installer - v0.1

set -e  # Exit on error

echo "🎯 MyOS Quick Installer"
echo "========================"

# 1. Prüfe Voraussetzungen
echo "📦 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

if ! command -v fuse3 &> /dev/null; then
    echo "⚠️  FUSE3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y fuse3 libfuse3-dev python3-pip
fi

# 2. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user fusepy tabulate pytest

# 3. Frage nach Test-Verzeichnis
echo ""
echo "📁 Where would you like to test MyOS?"
echo "   This will create a 'myos_test' directory there."
read -p "   Enter path [default: ~/Desktop]: " TEST_PATH
TEST_PATH=${TEST_PATH:-"$HOME/Desktop"}

# 4. Test-Verzeichnis erstellen
FULL_PATH="$TEST_PATH/myos_test"
mkdir -p "$FULL_PATH"
mkdir -p "$FULL_PATH/mirror"
mkdir -p "$FULL_PATH/mount"

# 5. Symlinks für CLI-Tools
echo "🔗 Setting up CLI tools..."
chmod +x cli/myls.py
ln -sf "$(pwd)/cli/myls.py" ~/.local/bin/myls 2>/dev/null || true

# 6. Test-Dateien erstellen
echo "📄 Creating test files..."
cat > "$FULL_PATH/test_commands.txt" << 'EOF'
# MyOS Test Commands
# ==================

# Terminal 1: Start MyOS
cd $(dirname "$0")
python3 myos_core.py ./mirror ./mount

# Terminal 2: Test MyOS
cd $(dirname "$0")
ls mount/                          # Shows blueprint folders
touch mount/project%/test.txt      # Materializes project/
./myls.py mount/ --roentgen        # Intelligent view
EOF

# 7. Erfolgsmeldung
echo ""
echo "✅ Installation complete!"
echo "========================"
echo ""
echo "📁 Test directory created at:"
echo "   $FULL_PATH"
echo ""
echo "🚀 To start testing:"
echo "   1. Open Terminal 1: cd $FULL_PATH"
echo "   2. Run: python3 myos_core.py ./mirror ./mount"
echo "   3. Open Terminal 2: cd $FULL_PATH"
echo "   4. Run commands from test_commands.txt"
echo ""
echo "💡 Quick test:"
echo "   ./myls.py . --help"
echo ""
