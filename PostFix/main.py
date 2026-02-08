#!/usr/bin/env python3
"""
PostFix - Main Application Entry Point
Builds UI directly in Python without .ui files for full control.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QSpacerItem,
                               QSizePolicy, QFrame, QColorDialog)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPalette


class SidebarWidget(QWidget):
    """Base class for sidebars with fade-in/fade-out on hover."""
    
    def __init__(self, title="Sidebar", bg_color="rgba(200, 220, 240, 60)"):
        super().__init__()
        self.base_opacity = 0.2  # Very transparent when idle
        self.hover_opacity = 0.8  # More visible on hover
        
        # Set initial style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 5px;
                border: 1px dashed #aaa;
            }}
            QLabel {{
                color: #333333;
                font-weight: bold;
            }}
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Set opacity
        self.set_opacity(self.base_opacity)
        
    def set_opacity(self, opacity):
        """Set widget opacity."""
        self.setWindowOpacity(opacity)
        
    def enterEvent(self, event):
        """Fade in when mouse enters."""
        self.animate_opacity(self.base_opacity, self.hover_opacity)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Fade out when mouse leaves."""
        self.animate_opacity(self.hover_opacity, self.base_opacity)
        super().leaveEvent(event)
        
    def animate_opacity(self, start, end):
        """Animate opacity change."""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)  # ms
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()


class TagSidebar(SidebarWidget):
    """Right sidebar for tags with interactive tag buttons."""
    
    def __init__(self):
        super().__init__("Tags", "rgba(220, 240, 200, 60)")
        self.tags = []
        self.setup_ui()
        
    def setup_ui(self):
        # Get the layout from parent
        layout = self.layout()
        
        # Clear placeholder widgets
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add tag buttons (example tags)
        self.tag_buttons = []
        example_tags = [
            ("important", "#ff6b6b"),
            ("urgent", "#ffa726"),
            ("in process", "#ffd93d"),
            ("done", "#6bcf7f"),
            ("waiting", "#4d96ff")
        ]
        
        for tag_text, color in example_tags:
            btn = QPushButton(tag_text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 5px 10px;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    border: 1px solid white;
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
            self.tag_buttons.append(btn)
        
        # Add Tag button (always visible)
        self.add_tag_btn = QPushButton("+ Add Tag")
        self.add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 100);
                color: white;
                border: 1px dashed white;
                border-radius: 10px;
                padding: 5px 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 150);
            }
        """)
        self.add_tag_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.add_tag_btn)
        
        # Add stretch at the bottom
        layout.addStretch()


class ACLSidebar(SidebarWidget):
    """Left sidebar for ACLs (fake implementation)."""
    
    def __init__(self):
        super().__init__("ACLs", "rgba(200, 220, 240, 60)")
        self.setup_ui()
        
    def setup_ui(self):
        layout = self.layout()
        
        # Clear placeholder widgets
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add ACL checkboxes (fake implementation)
        acl_items = ["Alfred", "Bertha", "Christian", "Doris", 
                    "Buchhaltung", "Entwicklung", "Dokumentation"]
        
        for item in acl_items:
            # Using buttons for now, could be checkboxes
            btn = QPushButton(f"○ {item}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #333333;
                    border: none;
                    text-align: left;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 50);
                    border-radius: 3px;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
        
        layout.addStretch()


class BottomToolbar(QWidget):
    """Two-level bottom toolbar with hover effect."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)  # Only primary level visible initially
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Secondary toolbar (hidden initially)
        self.secondary_toolbar = QWidget()
        self.secondary_toolbar.setStyleSheet("""
            QWidget {
                background-color: rgba(220, 220, 220, 220);
                border-bottom: 1px solid #bbbbbb;
            }
        """)
        self.secondary_layout = QHBoxLayout(self.secondary_toolbar)
        self.secondary_layout.setSpacing(15)
        
        # Primary toolbar (always visible)
        self.primary_toolbar = QWidget()
        self.primary_toolbar.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 240, 240, 180);
                border-top: 1px solid #cccccc;
            }
        """)
        self.primary_layout = QHBoxLayout(self.primary_toolbar)
        self.primary_layout.setSpacing(15)
        
        # Add toolbars to main layout
        self.main_layout.addWidget(self.secondary_toolbar)
        self.main_layout.addWidget(self.primary_toolbar)
        
        # Initially hide secondary toolbar
        self.secondary_toolbar.hide()
        
        # Setup content
        self.setup_primary_toolbar()
        self.setup_secondary_toolbar()
        
    def setup_primary_toolbar(self):
        """Setup the always-visible primary toolbar."""
        # Primary action buttons
        actions = ["Send To", "Open In", "Print"]
        
        for action in actions:
            btn = QPushButton(action)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #333333;
                    border: none;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: rgba(200, 200, 200, 100);
                    border-radius: 3px;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Connect hover to show secondary toolbar
            btn.enterEvent = lambda e, a=action: self.show_secondary(a)
            btn.leaveEvent = lambda e: self.start_hide_timer()
            
            self.primary_layout.addWidget(btn)
        
        # Add stretch
        self.primary_layout.addStretch()
        
    def setup_secondary_toolbar(self):
        """Setup the secondary toolbar that appears on hover."""
        # Clear any existing widgets
        while self.secondary_layout.count():
            item = self.secondary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add some example secondary actions
        # In real implementation, this would change based on primary selection
        example_actions = ["Email", "WhatsApp", "Telegram", "Obsidian", 
                          "LibreOffice", "PDF Printer", "Network Printer"]
        
        for action in example_actions:
            btn = QPushButton(action)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 100, 100, 100);
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: rgba(150, 150, 150, 150);
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            self.secondary_layout.addWidget(btn)
        
        self.secondary_layout.addStretch()
        
    def show_secondary(self, primary_action):
        """Show secondary toolbar for the given primary action."""
        # Update secondary toolbar based on primary action
        self.setup_secondary_toolbar()  # Recreate with appropriate actions
        
        # Animate show
        if not self.secondary_toolbar.isVisible():
            self.secondary_toolbar.show()
            self.setMaximumHeight(60)  # Expand to show both levels
            
    def start_hide_timer(self):
        """Start timer to hide secondary toolbar (simplified)."""
        # For simplicity, we hide immediately when mouse leaves
        # In production, you'd use a QTimer with short delay
        self.hide_secondary()
        
    def hide_secondary(self):
        """Hide secondary toolbar."""
        if self.secondary_toolbar.isVisible():
            self.secondary_toolbar.hide()
            self.setMaximumHeight(30)  # Back to primary only


class SmartEditor(QWidget):
    """Smart editor widget with placeholder for now."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder for now - will be replaced with actual editor
        placeholder = QLabel("Smart Editor Area\n\n"
                           "• Dual-pane Markdown editor\n"
                           "• Live preview\n"
                           "• Split view mode\n"
                           "• Syntax highlighting")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 247, 64, 30);
                border-radius: 5px;
                padding: 20px;
                color: #333333;
                font-size: 14px;
            }
        """)
        layout.addWidget(placeholder)


class PostFixWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PostFix")
        self.setGeometry(100, 100, 900, 650)
        
        # Set application styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                font-size: 12px;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Create and add top toolbar
        self.create_top_toolbar()
        main_layout.addWidget(self.top_toolbar)
        
        # Create center area (editor + sidebars)
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setSpacing(4)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add sidebars and editor
        self.left_sidebar = ACLSidebar()
        self.editor = SmartEditor()
        self.right_sidebar = TagSidebar()
        
        center_layout.addWidget(self.left_sidebar, 1)  # stretch factor 1
        center_layout.addWidget(self.editor, 5)        # stretch factor 5
        center_layout.addWidget(self.right_sidebar, 1) # stretch factor 1
        
        main_layout.addWidget(center_widget)
        
        # Add bottom toolbar
        self.bottom_toolbar = BottomToolbar()
        main_layout.addWidget(self.bottom_toolbar)
        
        # Connect signals
        self.connect_signals()
        
    def create_top_toolbar(self):
        """Create the top toolbar with all controls."""
        self.top_toolbar = QWidget()
        self.top_toolbar.setMinimumHeight(40)
        self.top_toolbar.setMaximumHeight(40)
        self.top_toolbar.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 240, 240, 200);
                border-bottom: 1px solid #cccccc;
            }
        """)
        
        layout = QHBoxLayout(self.top_toolbar)
        layout.setSpacing(10)
        
        # Burger menu button
        self.btn_menu = QPushButton("☰")
        self.btn_menu.setMinimumSize(30, 30)
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        
        # Background color button
        self.btn_bg_color = QPushButton()
        self.btn_bg_color.setMinimumSize(30, 30)
        self.btn_bg_color.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #FFF740;
                border: 1px solid #d4c600;
            }
            QPushButton:hover {
                border: 2px solid #b3a500;
            }
        """)
        self.btn_bg_color.setCursor(Qt.PointingHandCursor)
        
        # Spacer
        layout.addWidget(self.btn_menu)
        layout.addWidget(self.btn_bg_color)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        # View mode button
        self.btn_view_mode = QPushButton("Live Preview")
        self.btn_view_mode.setCursor(Qt.PointingHandCursor)
        
        # Expanding spacer
        layout.addWidget(self.btn_view_mode)
        layout.addStretch()
        
        # Window control buttons
        self.btn_minimize = QPushButton("−")
        self.btn_minimize.setMinimumSize(30, 30)
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        
        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setMinimumSize(30, 30)
        self.btn_maximize.setCursor(Qt.PointingHandCursor)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setMinimumSize(30, 30)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                color: white;
                font-weight: bold;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #ff7777;
            }
        """)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        
        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)
        
    def connect_signals(self):
        """Connect all button signals."""
        # Window controls
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_close.clicked.connect(self.close)
        
        # Background color picker
        self.btn_bg_color.clicked.connect(self.pick_background_color)
        
        # View mode toggle
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        
        # Menu button (placeholder)
        self.btn_menu.clicked.connect(self.show_menu)
        
    def toggle_maximize(self):
        """Toggle between normal and maximized window state."""
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            self.btn_maximize.setText("❐")
            
    def pick_background_color(self):
        """Open color dialog to pick background color."""
        color = QColorDialog.getColor(
            QColor("#FFF740"), 
            self, 
            "Pick Post-It Color"
        )
        
        if color.isValid():
            # Update button color
            self.btn_bg_color.setStyleSheet(f"""
                QPushButton {{
                    border-radius: 15px;
                    background-color: {color.name()};
                    border: 1px solid {color.darker(120).name()};
                }}
                QPushButton:hover {{
                    border: 2px solid {color.darker(150).name()};
                }}
            """)
            
            # Update editor background (placeholder)
            print(f"Selected color: {color.name()}")
            # TODO: Update actual editor background and metadata
            
    def toggle_view_mode(self):
        """Toggle between view modes."""
        current_text = self.btn_view_mode.text()
        modes = ["Live Preview", "Edit Source", "Split View"]
        
        try:
            current_index = modes.index(current_text)
            next_index = (current_index + 1) % len(modes)
        except ValueError:
            next_index = 0
            
        self.btn_view_mode.setText(modes[next_index])
        print(f"Switched to {modes[next_index]} mode")
        
        # TODO: Implement actual view mode switching
        
    def show_menu(self):
        """Show menu (placeholder)."""
        print("Menu clicked - will show settings/options")
        # TODO: Implement menu functionality


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PostFix")
    app.setOrganizationName("PostFixDev")
    
    window = PostFixWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
