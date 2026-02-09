#!/bin/bash
# install-md-workflow.sh

echo "=== MD-First Workflow Installation ==="

# 1. Abhängigkeiten
echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3-pip pandoc texlive-xetex
pip3 install pyyaml python-docx python-pptx

# 2. Hauptskript
echo "Installing workflow scripts..."
sudo cp folder_tags.py /usr/local/bin/md-workflow
sudo chmod +x /usr/local/bin/md-workflow

# 3. Dolphin Service Menu
echo "Setting up Dolphin integration..."
mkdir -p ~/.local/share/kservices5/ServiceMenus/
cp dolphin-md-actions.py ~/.local/share/kservices5/ServiceMenus/

# 4. Obsidian Plugin (manuell)
echo "=== Obsidian Plugin ==="
echo "1. Create folder: .obsidian/plugins/md-workflow"
echo "2. Copy main.js, manifest.json"
echo "3. Enable plugin in Obsidian"

# 5. Beispiel-Vorlage
echo "Creating example template..."
mkdir -p ~/Templates/MD-Workflow
cat > ~/Templates/MD-Workflow/_folder.tags.md << 'EOF'
---
folder-tags: [template, example]
file-tags: {}
export-defaults:
  pdf:
    template: default
  pptx:
    theme: light
---
# Project Folder

Start your MD-first workflow here.
EOF

echo "Installation complete!"
echo "Usage: md-workflow export --file README.md --format pdf"