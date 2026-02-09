#!/usr/bin/env python3
# dolphin-md-actions.py
import os
import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class MDActionsMenu(QMenu):
    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths
        self.setTitle("MD Workflow Actions")
        
        # Nur für .md Dateien
        md_files = [f for f in file_paths if f.endswith('.md')]
        
        if md_files:
            pdf_action = self.addAction("Export to PDF")
            pdf_action.triggered.connect(lambda: self.export_files(md_files, 'pdf'))
            
            pptx_action = self.addAction("Export to PowerPoint")
            pptx_action.triggered.connect(lambda: self.export_files(md_files, 'pptx'))
            
            self.addSeparator()
            
            email_action = self.addAction("Send as Email")
            email_action.triggered.connect(lambda: self.open_with(md_files, 'email'))
            
            print_action = self.addAction("Print")
            print_action.triggered.connect(lambda: self.open_with(md_files, 'print'))
    
    def export_files(self, files, format):
        for file in files:
            cmd = f"python3 /path/to/folder_tags.py export --file '{os.path.basename(file)}' --format {format}"
            os.system(f"cd '{os.path.dirname(file)}' && {cmd}")
    
    def open_with(self, files, app):
        for file in files:
            cmd = f"python3 /path/to/folder_tags.py open --file '{os.path.basename(file)}' --app {app}"
            os.system(f"cd '{os.path.dirname(file)}' && {cmd}")

# Dolphin Service Menu Integration
if __name__ == "__main__":
    # Dolphin übergibt Dateien als Argumente
    files = sys.argv[1:]
    
    app = QApplication(sys.argv)
    menu = MDActionsMenu(files)
    menu.exec_(QCursor.pos())