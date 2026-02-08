Project: PostFix - Intelligent Post-It Editor with Metadata
Goal: Phase 1 & 2 MVP (Minimal Viable Product)
Core Tech Stack: Python, PySide6 (Qt for Python), PyYAML, markdown2
Target OS: Linux Mint (Primary), cross-platform compatible where possible

A) Core Architectural Decisions
Window Management: Start with a standard decorated window. Track moveEvent and resizeEvent. Save geometry (x, y, width, height) to YAML frontmatter on mouse release.

Document Modes: Implement three toggleable modes for the central editor via topbar button or shortcut (Ctrl+M):

LIVE_PREVIEW: Rendered HTML (default).

EDIT_SOURCE: Pure Markdown source.

SPLIT_VIEW: Vertical split between source and preview.

Metadata Flow: A single MetadataManager class handles all YAML frontmatter operations (load, update, save) for the current document. It ensures atomic writes.

B) Component Specifications
1. MainWindow (PostFixWindow)

Inherits from QMainWindow.

Manages the overall layout and all child widgets.

Connects UI signals to the MetadataManager and core logic slots.

2. CentralEditor (SmartMarkdownEditor)

A QTabWidget or QStackedWidget to switch between the three view modes.

MarkdownSourceWidget: A QPlainTextEdit for raw Markdown.

HtmlPreviewWidget: A QTextBrowser to display HTML rendered via markdown2. Links are made clickable (open with QDesktopServices).

Synchronizes scroll positions in SPLIT_VIEW.

3. SidebarWidgets (TagSidebar, ACLSidebar)

Inherit from QWidget. Use QVBoxLayout with a QScrollArea.

TagSidebar: Dynamically creates QPushButton for each tag. Includes an "Add Tag" button that opens a QMenu with predefined tags (important, urgent, etc.).

ACLSidebar: A static list of checkboxes or buttons for Alfred, Bertha, Christian, Doris, Accounting, Development, Documentation. This is a fake implementation for Phase 1.

Visual Design: Opacity controlled via setStyleSheet. Use enterEvent and leaveEvent to animate opacity for a "fade-in on hover" effect.

4. TopToolbar & BottomToolbar

TopToolbar: A QWidget with QHBoxLayout. Contains:

Burger QPushButton (for future menu).

Color picker QPushButton with a QColorDialog.

Text format QPushButtons (color, background) that wrap selected text in HTML <span>.

Table QPushButton that inserts Markdown table snippet.

View mode toggle QPushButton (icon changes).

Window control buttons (min, max, close).

BottomToolbar: A two-layer system. A thin, always-visible QWidget (BottomBarLayer1) with action category buttons ("Send To", "Open In", "Print"). On hover, a second QWidget (BottomBarLayer2) slides up with the specific sub-actions as buttons.

5. MetadataManager

Single Source of Truth for the document's YAML frontmatter.

Methods: load(filepath), update_field(key, value), save().

Handles the logic for choosing between embedded frontmatter (for .md) and sidecar files (for others) as per our previous discussion.
