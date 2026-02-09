# 1. Ordner erstellen
mkdir mein-projekt
cd mein-projekt

# 2. Tags setzen
md-workflow tags --add-tag "dringend"
md-workflow tags --add-tag "kundenprojekt"

# 3. Markdown schreiben
cat > konzept.md << 'EOF'
# Projekt Konzept

## Idee
Das ist ein #wichtiges Projekt für #kunde-acme.

## Timeline
- [ ] Phase 1 #todo
- [x] Phase 0 #done
EOF

# 4. Export zu PowerPoint
md-workflow export --file konzept.md --format pptx

# 5. In LibreOffice öffnen
md-workflow open --file konzept.md --app libreoffice

# 6. Als Email vorbereiten
md-workflow open --file konzept.md --app email