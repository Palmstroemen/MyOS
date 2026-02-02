# MyOS Project Details & Technical Notes

## Design Docs

- `core/Dokumentation/Designdocument Projects.md`
- `core/Dokumentation/Designdocument BlueprintLayer.md`
- `core/Dokumentation/Designdocument ACLs.md`

## Repository Structure

MyOS/  
├── prototype/ # Main prototype  
│ ├── myos_core.py # FUSE implementation  
│ ├── myls.py # Intelligent file lister  
│ ├── mirror/ # Physical files (BACKUP!)  
│ └── mount/ # MyOS view (virtual - DO NOT BACKUP!)  
├── docs/ # Documentation  
├── tests/ # Test suite (future)  
└── LICENSE # MIT License

text

## Development Environment Setup

### Option 1: System-wide Installation
```bash
sudo apt-get install fuse3 libfuse3-dev python3-pip
pip3 install fuse-py

### Option 2: User Installation (no sudo needed)

bash

pip3 install --user fuse-py
export PATH="$HOME/.local/bin:$PATH"  # For myls symlink

### Option 3: Installation Script

bash

# install.sh
#!/bin/bash
echo "Installing MyOS Prototype..."
pip3 install --user fuse-py
chmod +x myos_core.py myls.py

echo "Creating symlinks..."
ln -sf "$(pwd)/myls.py" ~/.local/bin/myls 2>/dev/null

echo "Installation complete!"
echo "Usage: python3 myos_core.py ./mirror ./mount"
echo "       myls mount/ --roentgen"

## Development Tests

### Standard Test Run

bash

# Prepare directories
mkdir -p mirror mount

# Start FUSE (debug mode)
python3 myos_core.py ./mirror ./mount

# Test in another terminal
./myls.py mount/ --roentgen
touch mount/test%/file.txt
ls mount/

### Advanced Tests

bash

# Blueprint folder tests
mkdir mount/project%/subfolder
touch mount/finance%/budget.xlsx
cp existing.pdf mount/docs%/

# myls tests
./myls.py . --recent=5
./myls.py . --all
./myls.py . --blueprints

## Technical Architecture

### FUSE Layer (myos_core.py)

- Translates virtual paths to physical paths
    
- Implements %-folder materialization
    
- Manages file operations (create, read, write, mkdir, etc.)
    

### Tools Layer (myls.py)

- Provides project-centered views of files
    
- Implements intelligent filtering and grouping
    
- Supports multiple display modes
    

### File Structure

- **mirror/**: Physical files - ALWAYS BACKUP!
    
- **mount/**: Virtual MyOS view - DO NOT BACKUP!
    

## Security Details

### Current Implementation

1. **Path Traversal Protection**: Prevents `../` attacks
    
2. **Permission Model**: Uses underlying filesystem permissions
    
3. **Error Handling**: Safe error handling without crashes
    

### Known Limitations

- No filesystem-level encryption
    
- Performance not optimized for large file collections
    
- No integrated version control
    

### Best Practices for Developers

1. Always test in user space
    
2. Regularly backup `mirror/` directory
    
3. Don't run FUSE as root
    
4. Enable debug mode when troubleshooting
    

## Roadmap Details

### Phase 2 Priorities

1. Template system (`.myproject` files)
    
2. Configurable blueprint folders
    
3. Project type detection
    
4. Advanced myls filters
    

### Phase 3 Concepts

- **Rooms**: Virtual workspaces
    
- **Contexts**: Context-sensitive desktop adaptation
    
- **Spatial Navigation**: Spatial navigation between workspaces
    

## Contribution Guidelines

### Bug Reports

1. Specify operating system and version
    
2. Provide concrete reproduction steps
    
3. Describe expected vs. actual behavior
    
4. Include full error messages
    

### Feature Requests

1. Describe the use case
    
2. Consider alternatives
    
3. Consider impact on existing features
    

### Code Contributions

1. Discuss issue first
    
2. Small, focused pull requests
    
3. Tests for new features
    
4. Update documentation
    

## Performance Considerations

### Current Limits

- ~1000 files per directory recommended
    
- Recursive operations not optimized
    
- Minimal in-memory caching
    

### Future Optimizations

- LRU cache for frequent operations
    
- Asynchronous file operations
    
- Indexing for fast search
    

---

_Last updated: MyOS Prototype v0.2.0_