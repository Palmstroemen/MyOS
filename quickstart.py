#!/usr/bin/env python3
"""
MyOS Quick Start - Zero-configuration test
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 MyOS Zero-Config Quick Start")
    print("=" * 40)
    
    # Create test directory on Desktop
    test_dir = Path.home() / "Desktop" / "MyOS_Test"
    test_dir.mkdir(exist_ok=True)
    
    (test_dir / "mirror").mkdir(exist_ok=True)
    (test_dir / "mount").mkdir(exist_ok=True)
    
    # Copy minimal test files
    with open(test_dir / "START_HERE.txt", "w") as f:
        f.write("""MyOS Test Environment
====================

1. START MyOS (in this terminal):
   python3 myos_core.py ./mirror ./mount

2. TEST MyOS (in another terminal):
   ls mount/                    # See blueprint folders
   touch mount/test%/hello.txt  # Materialize folder
   ./myls.py mount/ --recent    # Smart file view

3. EXPLORE:
   - Try: cp file.txt mount/docs%/
   - Try: mkdir mount/project%/subdir
   - Try: ./myls.py . --all
""")
    
    print(f"✅ Test environment created at: {test_dir}")
    print("\n📋 Next steps:")
    print(f"   1. cd {test_dir}")
    print("   2. Run the commands in START_HERE.txt")
    print("\n💡 Need help? Visit: https://github.com/Palmstroemen/MyOS")
    
    # Offer to start MyOS immediately
    response = input("\n▶️  Start MyOS now? (y/N): ").lower()
    if response == 'y':
        os.chdir(test_dir)
        subprocess.run([sys.executable, "myos_core.py", "./mirror", "./mount"])

if __name__ == "__main__":
    main()
