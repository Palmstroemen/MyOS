import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.folderlistmodel 2.15
import "Theme/tag_chips.js" as TagChips
import "js/PathUtils.js" as PathUtils
import "js/ListSort.js" as ListSort
import "js/FormatUtils.js" as FormatUtils
import "./Dialogs" 1.0

ApplicationWindow {
    id: window
    width: 1400
    height: 900
    visible: true
    title: "Scope - MyOS GUI Stub"

    property int baseFont: Qt.application.font.pixelSize
    property bool darkTheme: true
    // Kept in the settings file (core/settings.py) once read at the start.
    property bool settingsRead: false
    // How pale embryos are: set on the back (General), followed at once.
    readonly property real embryoOpacity: setupPage.embryoOpacity
    readonly property real embryoBadgeOpacity: setupPage.embryoBadgeOpacity
    onDarkThemeChanged: if (settingsRead && hasBackend() && typeof backend.setSetting === "function") backend.setSetting("General/darkTheme", darkTheme)

    // --- The back: Setup (Scope/Designdocument Setup.md) ------------------------------------
    // ⚙ turns the window about its vertical axis; at a quarter turn the back takes over.
    property bool setupShown: false
    Rotation {
        id: setupFlip
        origin.x: window.width / 2
        origin.y: window.height / 2
        axis { x: 0; y: 1; z: 0 }
        angle: 0
    }
    SequentialAnimation {
        id: setupFlipAnimation
        property bool toBack: true
        // Both ways the same sense: one swing, and the panel turns through.
        NumberAnimation { target: setupFlip; property: "angle"; from: 0; to: -90; duration: 450; easing.type: Easing.InQuad }
        ScriptAction { script: window.setupShown = setupFlipAnimation.toBack }
        NumberAnimation { target: setupFlip; property: "angle"; from: 90; to: 0; duration: 450; easing.type: Easing.OutQuad }
    }
    function flipSetup(toBack) {
        if (setupFlipAnimation.running || setupShown === toBack) return
        setupFlipAnimation.toBack = toBack
        setupFlipAnimation.start()
    }
    property string iconFolder: "image://theme/folder-open"
    property string iconFolderOff: "image://theme/folder"
    property string iconProjectFallback: Qt.resolvedUrl("Theme/icons/project.svg")
    property string iconSearch: "image://theme/system-search"
    property string iconFile: "image://theme/text-x-generic"
    property string iconGear: "image://theme/preferences-system"
    property string folderItemStyle: "text" // text | smallIcon | largeIcon
    property int iconSizeSmall: Math.round(baseFont * 1.08)
    property int iconSizeLarge: Math.round(64 * 0.8)
    property int compactButtonHeight: 24
    property int largeButtonPadding: 8
    property int largeButtonHeight: iconSizeLarge + baseFont + (largeButtonPadding * 2) + 2
    property int searchPathPrefixDepth: 2
    property bool verticalProjectView: false
    property bool level2VerticalView: false
    // Minimal view (M, prototype for E4): one line - the CWD as a button (the path above it
    // drops down on hover, each level's children open to the right), then the MyOS folders
    // with the lens' frame. H and V stay as they are.
    property bool minimalView: false
    property var searchInputRef: null
    property string standardButtonStyle: "text"
    property string userButtonStyle: "text"
    property string uiLanguage: "de"
    property string userPath: "/Eigene"
    property string level2ButtonStyle: "smallIcon"
    // Browser visibility
    property bool projectsBrowserVisible: true
    property bool templatesBrowserVisible: true
    // Edge-Dock mode (projects-only, X11-first): collapsed | expanded | expandedWithFiles
    property bool edgeDockEnabled: false
    property string edgeDockState: "expanded"
    /// When false, FilesPanel is hidden and gets no layout space; only single-click shows it.
    property bool filesPaneVisible: true
    /// Max height for FilesPanel slot (0 = no cap). Used when edge dock or layout should limit panel growth.
    property int filesPanelMaxHeight: 720
    /// Stored window size when leaving expandedWithFiles; restored when entering expandedWithFiles again.
    property int edgeDockStoredWidth: 0
    property int edgeDockStoredHeight: 0
    /// Stored size when entering collapsed; restored when expanding from collapsed.
    property int edgeDockStoredExpandedWidth: 0
    property int edgeDockStoredExpandedHeight: 0
    property string _previousEdgeDockState: edgeDockState
    readonly property bool edgeDockCollapsed: edgeDockEnabled && (edgeDockState === "collapsed")
    readonly property int edgeDockTriggerBarHeight: (hasBackend() && typeof backend.platformName === "function" && backend.platformName() === "xcb") ? 4 : 24
    // Positive value lets FilesPanel overlap a bit to the left.
    property int filesPanelOverlapPx: 8
    // Zentrale Pfad-/Ordnernamen (Magic Values vermeiden)
    readonly property string myosDirName: ".MyOS"
    readonly property string pathSegmentClipboard: "Clipboard"
    readonly property string pathSegmentProjekte: "Projekte"
    readonly property string pathSegmentTemplates: "Templates"
    readonly property string pathSegmentMyosTest: "MyOS_Test"
    readonly property string pathSegmentMyOS: "MyOS"
    property color dialogPanelBg: darkTheme ? "#f4f7ff" : "#141823"
    property color dialogPanelBorder: darkTheme ? "#1b2438" : "#d5ddf2"
    property color dialogTextStrong: darkTheme ? "#1a2233" : "#edf2ff"
    property color dialogTextMuted: darkTheme ? "#34405a" : "#c6d2ee"
    property color dialogInputBg: darkTheme ? "#ffffff" : "#0f1320"
    property color dialogInputBorder: darkTheme ? "#2f3d5f" : "#8ca0cf"
    property color dialogInputText: darkTheme ? "#111827" : "#f5f7ff"
    property color dialogInputPlaceholder: darkTheme ? "#526280" : "#9fb0d6"

    QtObject {
        id: theme
        property color bg: darkTheme ? "#0f1014" : "#f3f4f8"
        property color panel: darkTheme ? "#1b1d26" : "#e6e8f0"
        property color panelAlt: darkTheme ? "#151821" : "#e9ecf5"
        property color panelAlt2: darkTheme ? "#12141b" : "#eef1f8"
        property color card: darkTheme ? "#0f1117" : "#ffffff"
        property color pill: darkTheme ? "#2a2f40" : "#dfe3f0"
        property color pillBorder: darkTheme ? "#3a4158" : "#c6ccdf"
        property color smallButtonBg: darkTheme ? "#3a4258" : "#e5e9f3"
        property color smallButtonBorder: darkTheme ? "#505a74" : "#c2c9db"
        property color smallButtonActiveBg: darkTheme ? "#4a5675" : "#c5d2ef"
        property color smallButtonActiveBorder: darkTheme ? "#6a779a" : "#9fb1dd"
        property color smallButtonText: darkTheme ? "#b4bac6" : "#4a5163"
        // Fixed gray palette for folder rows (theme mirrored).
        // Dark: P~20%, CWD~30%, U~40%; Light: P~60%, CWD~70%, U~80%.
        property color folderPathTint: darkTheme ? "#333333" : "#999999"
        property color folderCwpTint: darkTheme ? "#4D4D4D" : "#B3B3B3"
        property color folderULineTint: darkTheme ? "#666666" : "#CCCCCC"
        function darkerByTenPoints(value) {
            return Qt.rgba(
                Math.max(0, value.r - 0.10),
                Math.max(0, value.g - 0.10),
                Math.max(0, value.b - 0.10),
                value.a
            )
        }
        property color folderPathBorder: darkerByTenPoints(folderPathTint)
        property color folderULineBorder: darkerByTenPoints(folderULineTint)
        property color accentPrimary: folderCwpTint
        property color accentPrimaryText: "#ffffff"
        property color accentSecondary: darkTheme ? "#3b476b" : "#b8c8ee"
        property color accentSecondaryBorder: darkTheme ? "#58648a" : "#9fb1dd"
        property color projectFolderTint: darkTheme ? "#bb00aa" : "#6a5cff"
        property color embryoFolderTint: darkTheme ? "#7b5bd6" : "#6a5cff"
        property color action: darkTheme ? "#39456b" : "#c8d2f0"
        property color actionBorder: darkTheme ? "#56618a" : "#9aa7cf"
        property color text: darkTheme ? "#e6e6e6" : "#1f2433"
        property color textMuted: darkTheme ? "#c9ccd7" : "#3b4152"
        property color textSoft: darkTheme ? "#cfd3df" : "#2b3140"
        property color filesPaneBackground: darkTheme ? "#404040" : "#b0b0b0"
        property color highlight: accentPrimary
    }

    property color currentProjectTint: theme.folderCwpTint
    property string defaultProjectTint: ""
    /// Eine gebundene Farbe für den FilesPanel-Rahmen: Projekt → Projektfarbe, sonst Default-Folder (wie CWD-Dropdowns).
    /// Follows the folder the panel shows (committed CTD), so a hover preview is tinted
    /// like a double-click into that folder.
    readonly property color filesPanelTintColor: hasProjectInFilesPath && projectsBrowser
        ? projectsBrowser.pathFillColor(currentFilesPath())
        : theme.folderPathTint
    /// The folder shown in the FilesPanel (currentFilesPath) is a project; set by updateFiles.
    property bool hasProjectInFilesPath: false

    // --- Pfadkonzepte CWD / CWP / CTD (Begriffe: siehe Vision/GUI Filebrowser.md, Abschnitt Begriffe) ---
    // CWD (Current Working Directory): Im Scope durch die Property cwp repräsentiert; der „Arbeitspfad“
    //     ist hier das aktuelle Projektverzeichnis.
    // CWP (Current Working Project): Im Code die Property cwp (Pfad zum aktuellen Projektordner, z. B. /Projekte/Haus/Dach).
    // CTD (Current Target Directory): Zielordner für Datei-Operationen (z. B. Verschieben, Vorschau).
    //     Properties: previewCTDPath (Vorschau beim Navigieren), committedCTDPath (bestätigter Zielpfad).
    //     Verweilt der Zeiger filesPreviewDelayMs auf einem Ordner, spätestens aber beim Hineinfahren ins
    //     FilesPanel, wird der hervorgehobene Vorschau-Ordner committet; das FilesPanel zeigt ihn, und ein
    //     Drop auf die freie Fläche landet dort.
    //     Funktionen: previewCTD(path), commitCTD(path). Welcher Pfad für die Dateiliste gilt: currentFilesPath()
    //     (Fallback auf cwp, wenn kein CTD gesetzt).

    property string cwp: "/Projekte/Haus/Dach"
    property var subProjects: []
    property string standardPath: "/"
    property string templatesCtdPath: ""
    property string previewCTDPath: ""
    property string committedCTDPath: ""
    property string clipboardPath: ""
    property bool clipboardHasItems: false
    property var standardFolders: []
    property var standardFoldersFiltered: []
    property var userFolders: ["myFolder", "myOtherFolder"]
    property var files: ["Rechnung_001.pdf", "Angebot_Alpha.docx", "Note.md"]
    property var fileItemsAll: []
    property var fileItemsRaw: []
    property var selectedEntryPaths: []
    property int fileItemsOffset: 0
    property int fileItemsChunk: 160
    property bool hasMyosInCwp: false
    /// Folder the P-Button turns into a project: the one folder selected in the FilesPanel,
    /// else the folder it shows; "" when neither can become one (see updateProjectCreateTarget).
    property string projectCreateTarget: ""
    /// Project the crossed-out P-Button turns back into an ordinary folder (same choice:
    /// the one entry selected, else the folder shown); "" when none.
    property string projectRemoveTarget: ""
    /// X-ray view (core/xray.py): small folders seen through while the list fits the
    /// FilesPanel without scrolling. On by default; remembered.
    property bool xrayEnabled: true

    function applyXrayView() {
        if (!hasBackend() || typeof backend.setXrayView !== "function") return
        backend.setXrayView(xrayEnabled ? filesPane.visibleCapacity : 0, filesPane.showFolders)
        updateFiles()
    }

    // Recomputed when the size has settled, not while dragging the window edge.
    Timer {
        id: xrayLayoutTimer
        interval: 400
        repeat: false
        onTriggered: window.applyXrayView()
    }
    property string tagFilterSource: "visible" // legacy
    property var availableTags: []
    property var folderTags: []
    property var subfolderTags: []
    property var fileTags: []
    property var folderTagColors: ({})
    property var subfolderTagColors: ({})
    property var fileTagColors: ({})
    property var tagSuggestions: []
    property var selectedTags: []
    property bool tagsIndexing: false
    /// Live-measured size of the listed folder (< 0 while unknown); lower bound until complete.
    property real currentFolderSizeBytes: -1
    property bool currentFolderSizeComplete: false
    /// Folder sizes are measured on demand only (hover/click on the size column or the
    /// sidebar total) and only for the listed folder; leaving the folder switches them off.
    property bool folderSizesActive: false
    property bool folderSizesMeasuring: false
    /// ACL filter panel data of the listed folder (backend.aclSummaryReady, computed in the
    /// background); hasAcls is false without an ACLs.md, and the panel stays hidden.
    property var aclSummary: ({ hasAcls: false, principals: [], access: ({}) })
    /// Principal id ("role:team", "user:anna") the list is filtered by; "" = no filter.
    property string selectedAclPrincipal: ""

    function requestAclSummary() {
        if (!hasBackend() || typeof backend.requestAclSummary !== "function") return
        var paths = []
        var source = fileItemsAll || []
        for (var i = 0; i < source.length; i++) {
            // Hidden entries do not count, as in filterEntries (counts and "*" match the list).
            var name = String(source[i].name || "")
            if (!projectsShowHiddenFolders && name.indexOf(".") === 0) continue
            // Embryos are not entries yet: their (template folder) roles would crowd the
            // exceptions. Not in the summary, they are also hidden while an ACL filter is on.
            if (source[i].isEmbryo) continue
            var p = entryPath(source[i])
            if (p.length > 0) paths.push(p)
        }
        backend.requestAclSummary(currentFilesPath(), paths)
    }

    function applyAclSummary(listingPath, summary) {
        if (PathUtils.normalizeFsPath(listingPath) !== PathUtils.normalizeFsPath(currentFilesPath())) return
        aclSummary = summary && summary.hasAcls ? summary : ({ hasAcls: false, principals: [], access: ({}) })
        // A filter by someone who no longer appears here ends (e.g. ACLs.md was edited).
        if (selectedAclPrincipal.length > 0) {
            var still = false
            var principals = aclSummary.principals || []
            for (var i = 0; i < principals.length; i++) {
                if (principals[i].id === selectedAclPrincipal) still = true
            }
            if (!still) selectedAclPrincipal = ""
            else filterEntries()
        }
    }

    function toggleAclPrincipal(id) {
        selectedAclPrincipal = selectedAclPrincipal === id ? "" : id
    }

    function activateFolderSizes() {
        if (folderSizesActive) return
        folderSizesActive = true
        folderSizesMeasuring = true
        if (hasBackend() && typeof backend.requestFolderSizes === "function") {
            backend.requestFolderSizes(currentFilesPath())
        }
    }
    /// FilesPanel view: "largeIcon" (tiles) or "smallIcon" (list); persisted per user by the backend.
    property string filesItemStyle: "largeIcon"
    /// Visible list view columns (ids, see Scope/js/FormatUtils.js); persisted per user by the backend.
    property var filesListColumns: ["modified", "size"]
    /// FilesPanel sort (header click): key "name" | "modified" | "size".
    property string filesSortKey: "name"
    property bool filesSortAscending: true
    /// Sort to return to when leaving a folder sorted by size. Only name/modified are
    /// persisted: sorting by size belongs to the on-demand measurement of one folder.
    property string filesBaseSortKey: "name"
    property bool filesBaseSortAscending: true

    function setFilesSort(key) {
        // Same column again flips the direction. A new column starts ascending, except
        // dates and size, which start with the newest / largest entries on top.
        filesSortAscending = (key === filesSortKey) ? !filesSortAscending : ListSort.defaultAscending(key)
        filesSortKey = key
        if (key !== "size") {
            filesBaseSortKey = key
            filesBaseSortAscending = filesSortAscending
            if (hasBackend() && typeof backend.setFilesSort === "function") {
                backend.setFilesSort(filesSortKey, filesSortAscending)
            }
        }
        filterEntries()
    }
    property string tagMatchMode: "or" // or | and
    property bool projectsShowEmbryos: false
    property bool projectsShowHiddenFolders: false
    property bool templatesShowEmbryos: true
    property var pendingMoveSources: []
    property string pendingMoveTargetDir: ""
    property string pendingMoveMessage: ""
    property string moveReportMessage: ""
    property var pendingFolderBatchSources: []
    property string pendingFolderBatchName: qsTr("New Folder")
    property string pendingCreateFolderTargetPath: ""
    property string pendingCreateFolderName: qsTr("New Folder")
    property string pendingRenamePath: ""
    property string pendingRenameName: ""
    property var pendingDeletePaths: []
    /// The pending deletion includes folders (deleted with their contents).
    property bool pendingDeleteHasFolders: false
    property var pendingBatchRenamePaths: []
    property string pendingBatchReplaceFrom: ""
    property string pendingBatchReplaceTo: ""
    property string pendingOpenWithPath: ""
    property string pendingOpenWithCommand: "xdg-open"
    property var openWithQuickCommands: ["xdg-open", "code", "libreoffice"]
    // The lens as the session describes it (see lensRequest); off: { active: false }.
    property var lensState: ({ active: false })
    // The projects root ("Projekte"): the minimal view's dropdown ends there.
    readonly property string projectsRootPath: (hasBackend() && typeof backend.projectsRoot === "function") ? String(backend.projectsRoot() || "") : ""
    readonly property bool lensOn: !!(lensState && lensState.active)
    // The lens looks into a project (not on the shelf, which comes with the right menu, E4).
    readonly property bool lensInProject: lensOn && !!lensState.project
    property string selectionAnchorPath: ""
    property int maxVerticalParents: 4
    property int verticalParentSpacing: 6
    ListModel {
        id: filesModel
        dynamicRoles: true
    }

    FolderListModel {
        id: fsModel
        showDirs: true
        showFiles: true
        showHidden: false
        showDotAndDotDot: false
        nameFilters: ["*"]
        folder: PathUtils.toFileUrl(cwp)
        onCountChanged: {
            if (hasBackend()) {
                // Backend-driven mode already updates via onCwpChanged and explicit actions.
                // Skip duplicate refresh work triggered by FolderListModel count churn.
                return
            }
            updateFiles()
            updateSubProjects()
        }
    }

    FolderListModel {
        id: fsHiddenModel
        showDirs: true
        showFiles: false
        showHidden: true
        showDotAndDotDot: false
        nameFilters: [myosDirName]
        folder: PathUtils.toFileUrl(cwp)
        onCountChanged: {
            if (!hasBackend()) {
                hasMyosInCwp = fsHiddenModel.count > 0
            }
        }
    }

    function updateProjectCreateTarget() {
        var create = ""
        var remove = ""
        if (hasBackend() && typeof backend.canCreateProject === "function") {
            var selected = selectedEntryPaths || []
            // Something selected: only that. Falling back to the folder shown would make the
            // button switch its target silently (a second click hit the parent folder).
            var candidate = selected.length === 1 ? selected[0] : (selected.length === 0 ? currentFilesPath() : "")
            if (candidate.length > 0) {
                if (backend.canCreateProject(candidate)) create = candidate
                else if (typeof backend.canRemoveProject === "function" && backend.canRemoveProject(candidate)) remove = candidate
            }
        }
        projectCreateTarget = create
        projectRemoveTarget = remove
    }

    /// Turn projectRemoveTarget back into an ordinary folder; with settings of its own,
    /// ask first (projectRemoveDialog), then they go into the parent project's trash.
    function removeProjectAt(target, keepOwn) {
        if (target.length === 0 || !hasBackend() || typeof backend.removeProject !== "function") return
        var result = backend.removeProject(target, keepOwn) || ({})
        if (result.reason === "own") {
            projectRemoveDialog.openFor(target, result.own || [])
            return
        }
        if (!result.ok) {
            moveReportMessage = result.reason === "permission"
                ? qsTr("You may not turn \"%1\" back into a folder: it has rights of its own that you may not change.").arg(PathUtils.basename(target))
                : qsTr("\"%1\" could not be turned back into a folder.").arg(PathUtils.basename(target))
            moveReportDialog.open()
            return
        }
        // The selection stays on the folder: the button now offers to make it a project again.
        updateSubProjects()
        if (typeof backend.setContext === "function") backend.setContext(cwp)
        updateFiles()
        updateTemplates()
        standardFolders = listTemplates(templatesListingPath())
        updateStandardFolders()
    }

    onSelectedEntryPathsChanged: updateProjectCreateTarget()

    function setCwp(path, reason) {
        var nextPath = PathUtils.normalizeFsPath(path)
        var currentPath = PathUtils.normalizeFsPath(cwp)
        if (nextPath.length === 0 || nextPath === currentPath) {
            return
        }
        cwp = nextPath
    }

    function currentFilesPath() {
        var committed = String(committedCTDPath || "").trim()
        if (committed.length > 0) {
            return committed
        }
        return String(cwp || "")
    }

    /// Hover preview: the FilesPanel follows after the pointer rests for
    /// filesPreviewDelayMs, or at the latest when the pointer enters the FilesPanel.
    property int filesPreviewDelayMs: 700
    /// FolderBrowser that emitted the pending hover preview (null when nothing is pending).
    property var filesPreviewBrowser: null

    Timer {
        id: filesPreviewTimer
        interval: window.filesPreviewDelayMs
        repeat: false
        onTriggered: window.flushFilesPreview()
    }

    function previewCTD(path) {
        previewCTDPath = String(path || "").trim()
        if (previewCTDPath.length === 0) {
            filesPreviewTimer.stop()
            filesPreviewBrowser = null
            return
        }
        filesPreviewTimer.restart()
    }

    /// Commit the pending hover preview now. Uses the folder the browser visibly
    /// highlights, not the last tab crossed on the way (e.g. into the FilesPanel).
    function flushFilesPreview() {
        var browser = filesPreviewBrowser
        filesPreviewTimer.stop()
        filesPreviewBrowser = null
        if (!browser) {
            return
        }
        // No highlight means the browser reset its preview: nothing to show.
        var target = browser.highlightedPreviewPath()
        if (target.length === 0) {
            return
        }
        commitCTD(browser.resolvePath ? browser.resolvePath(target) : target)
    }

    function commitCTD(path) {
        filesPreviewTimer.stop()
        filesPreviewBrowser = null
        var nextPath = PathUtils.normalizeFsPath(path)
        if (nextPath.length === 0) {
            return false
        }
        previewCTDPath = nextPath
        templatesCtdPath = nextPath
        if (nextPath === PathUtils.normalizeFsPath(committedCTDPath)) {
            return false
        }
        committedCTDPath = nextPath
        return true
    }

    /// Apply CTD for path and refresh file list if path unchanged (e.g. re-click on current folder).
    function applyFolderActivation(path) {
        if (!commitCTD(path)) {
            updateFiles()
        }
    }

    /// Parent directory of path (for "cd .."). Returns "/" if path is root or single segment.
    function parentOfPath(path) {
        var p = String(path || "").trim()
        if (p.length === 0) return "/"
        var norm = p.endsWith("/") ? p.slice(0, -1) : p
        var idx = norm.lastIndexOf("/")
        if (idx <= 0) return "/"
        return norm.slice(0, idx) || "/"
    }

    readonly property bool isInsideMyosFolder: {
        var p = String(currentFilesPath() || "").trim()
        if (p.length === 0) return false
        var norm = p.endsWith("/") ? p.slice(0, -1) : p
        var segment = "/" + myosDirName
        return norm.endsWith(segment) || norm.indexOf(segment + "/") >= 0
    }

    function handlePreviewPath(browser, path) {
        var p = (browser.resolvePath ? browser.resolvePath(path) : path)
        filesPreviewBrowser = browser
        previewCTD(p)
    }
    function handleMoveEntry(browser, sourcePath, targetDir) {
        var dir = (browser.resolvePath ? browser.resolvePath(targetDir) : targetDir)
        moveEntry(sourcePath, dir)
    }
    function handleCreateFolder(browser, basePath) {
        var p = (browser.resolvePath ? browser.resolvePath(basePath || "") : (basePath || ""))
        if (p.length === 0 && browser === projectsBrowser) p = cwp
        requestCreateFolderAt(p)
    }

    function show_FilesPanel() {
        filesPaneVisible = true
        if (edgeDockEnabled) edgeDockState = "expandedWithFiles"
    }
    function hide_FilesPanel() {
        filesPaneVisible = false
        if (edgeDockEnabled) edgeDockState = "expanded"
    }

    function hasBackend() {
        return typeof backend !== "undefined" && backend !== null
    }

    function nameForItem(item) {
        return (item && item.name) ? item.name : item
    }

    function normalizeProjectIconSource(rawIcon) {
        var value = String(rawIcon || "").trim()
        if (value.length === 0) {
            return ""
        }
        if (value.indexOf("://") > 0) {
            return value
        }
        if (value.indexOf("/") === 0) {
            return PathUtils.toFileUrl(value)
        }
        return "image://theme/" + value
    }

    function projectIconForPath(path) {
        if (!hasBackend() || typeof backend.projectIcon !== "function") {
            return iconProjectFallback
        }
        var resolved = normalizeProjectIconSource(backend.projectIcon(path))
        return resolved.length > 0 ? resolved : iconProjectFallback
    }

    // --- The lens (Designdocument Perspective Resolver MVP.md, Part A) -------------------
    // The lens lives in one session (the perspective daemon); Scope only asks it and shows
    // what it answers - it builds no lens paths. With a lens on, the MyOS-folder row shows
    // the lens' folder in its project, and the FilesPanel what the lens shows.

    /// Ask the session (put_on, look_at, take_off, ...) and show the lens afterwards.
    function lensRequest(method, params) {
        if (!hasBackend() || typeof backend.lens !== "function") return false
        var reply = backend.lens(method, params || ({}))
        if (!reply || !reply.ok) {
            console.log("lens", method, "failed:", reply ? reply.error : "no reply")
            return false
        }
        showLens(reply.result)
        return true
    }

    /// Show the lens as the session describes it (active, target, shown, fallback, ...).
    function showLens(state) {
        var wasOn = lensOn
        lensState = state || ({ active: false })
        if (lensOn || wasOn) {
            commitCTD(filesPathWithLens())  // taken off: back in the CWD
        }
        standardFolders = listTemplates(templatesListingPath())
        updateStandardFolders()
    }

    /// Show the lens as the session has it now (changed by a filter, or another program).
    function showLensOfSession() {
        if (!hasBackend() || typeof backend.lens !== "function") return
        var reply = backend.lens("state", {})
        if (reply && reply.ok) showLens(reply.result)
    }

    /// Turned to (the window active, or the mouse in it): Scope and SunTree always share the
    /// place, so go where SunTree went and show the lens as the session has it. Unchanged,
    /// nothing moves - a folder browsed in the FilesPanel stays.
    function turnedTo() {
        if (!hasBackend() || typeof backend.followPlace !== "function") return
        var place = String(backend.followPlace() || "")
        if (place.length > 0) setCwp(place, "session.follow")
        var reply = backend.lens("state", {})
        if (reply && reply.ok && JSON.stringify(reply.result) !== JSON.stringify(lensState)) {
            showLens(reply.result)
        }
    }

    /// What the FilesPanel shows: what the lens shows - in a project. On the shelf (the CWD
    /// is a folder of projects) the CWD for now; the shelf itself comes with the right menu.
    function filesPathWithLens() {
        return lensInProject ? String(lensState.shown || "") : cwp
    }

    /// The CWD changed: tell the session where one is (a lens on stays where it is, A3).
    function lensSetCwd() {
        if (!hasBackend() || typeof backend.lens !== "function") return
        var reply = backend.lens("set_cwd", { "path": cwp })
        if (reply && reply.ok) {
            lensState = reply.result
        } else if (lensOn) {
            lensState = ({ active: false })  // outside the projects there is no lens
        }
    }

    /// Where something new in the shown folder goes: with the lens' folder missing in its
    /// project (the fallback shows a parent), the lens' folder - born now.
    function filesCreateTarget(path) {
        var p = String(path || "")
        if (!lensOn || !lensState.fallback
                || PathUtils.normalizeFsPath(p) !== PathUtils.normalizeFsPath(lensState.shown)) {
            return p
        }
        var born = backend.lensBear()
        if (!born || !born.ok) {
            console.log("lens: could not bear", lensState.target, born ? born.error : "")
            return ""
        }
        showLens(born.result)
        return String(born.result.target || "")
    }

    function templatesListingPath() {
        return lensInProject ? String(lensState.target || "") : standardPath
    }

    function resolveProjectRootPath() {
        if (hasBackend() && typeof backend.getProjectRoot === "function") {
            return PathUtils.trimTrailingSlash(String(backend.getProjectRoot() || ""))
        }
        return ""
    }

    function resolveTemplatesRootPathFromProjectRoot(projectRoot) {
        var root = PathUtils.trimTrailingSlash(projectRoot)
        if (root.length === 0) return ""
        if (root.endsWith("/Projekte")) {
            return root.slice(0, root.length - "/Projekte".length) + "/Templates"
        }
        return root + "/Templates"
    }

    function resolveTemplatesRootPath() {
        var fromProjectRoot = resolveTemplatesRootPathFromProjectRoot(resolveProjectRootPath())
        if (fromProjectRoot.length > 0) {
            return fromProjectRoot
        }
        var cwdParts = String(cwp || "").split("/").filter(function(p) { return p.length > 0 })
        var idx = -1
        for (var i = 0; i < cwdParts.length; i++) {
            if (cwdParts[i] === "Projekte") {
                idx = i
                break
            }
        }
        if (idx <= 0) return ""
        var base = "/" + cwdParts.slice(0, idx).join("/")
        return base + "/Templates"
    }

    function folderTypeFromMeta(folderMeta) {
        if (folderMeta && folderMeta.folderType !== undefined) {
            var parsed = Number(folderMeta.folderType)
            if (!isNaN(parsed)) {
                return parsed
            }
        }
        if (folderMeta && folderMeta.isEmbryo === true) {
            return 2
        }
        return 0
    }

    /// A MyOS folder (born or embryo): a double click on it puts on its lens.
    function isMyosFolder(folderMeta) {
        return folderTypeFromMeta(folderMeta) > 0
    }

    /// ✕ on the lens' frame (A3): only the frame goes, one stays where the lens looked -
    /// its folder in its project becomes the CWD (an embryo stays one); the FilesPanel keeps
    /// what it shows. On the shelf (no project yet, E4) one is back in the CWD.
    function takeOffLens() {
        if (!lensOn) return
        var projectDir = String(lensState.project_dir || "")
        var target = String(lensState.target || "")
        var shown = String(lensState.shown || "")
        if (!lensRequest("take_off") || projectDir.length === 0) return
        setCwp(projectDir, "lens.takeOff")
        standardPath = target
        standardFolders = listTemplates(target)
        updateStandardFolders()
        commitCTD(shown)
    }

    function _isMyOSFolderTrace(pathOrName) {
        var s = String(pathOrName || "")
        return s.indexOf("/" + pathSegmentMyosTest) >= 0 || s.indexOf("/" + pathSegmentMyOS + "/") >= 0 || s.endsWith("/" + pathSegmentMyOS) || s === pathSegmentMyOS
    }
    function listChildren(path, options) {
        var showHidden = (options && options.showHidden !== undefined) ? options.showHidden : projectsShowHiddenFolders
        if (hasBackend()) {
            var result = backend.listChildren(path, projectsShowEmbryos, showHidden)
            return result
        }
        if (path === cwp) {
            var dirs = []
            for (var i = 0; i < fsModel.count; i++) {
                var isDir = fsModel.get(i, "fileIsDir")
                if (isDir) {
                    var name = fsModel.get(i, "fileName")
                    if (!showHidden && (name || "").indexOf(".") === 0) continue
                    dirs.push(name)
                }
            }
            return dirs
        }
        return []
    }

    /// The projects row (right): folders that are no MyOS folder - those, born or not, are
    /// shown in the MyOS-folder row only.
    function listRightFolders(path, options) {
        return listChildren(path, options).filter(function(item) { return !isMyosFolder(item) })
    }

    function listTemplates(path) {
        if (hasBackend() && typeof backend.listTemplates === "function") {
            return backend.listTemplates(path, templatesShowEmbryos, projectsShowHiddenFolders)
        }
        return []
    }

    function updateCurrentProjectTint() {
        var cwpIsProject = hasBackend() && typeof backend.isProject === "function"
            ? backend.isProject(cwp)
            : false
        if (hasBackend() && typeof backend.effectiveProjectColor === "function") {
            var color = cwpIsProject ? backend.effectiveProjectColor(cwp) : ""
            currentProjectTint = (cwpIsProject && color && color.length > 0)
                ? color
                : theme.folderCwpTint
            return
        }
        if (hasBackend() && typeof backend.projectColor === "function") {
            var legacyColor = cwpIsProject ? backend.projectColor(cwp) : ""
            currentProjectTint = (cwpIsProject && legacyColor && legacyColor.length > 0)
                ? legacyColor
                : theme.folderCwpTint
            return
        }
        currentProjectTint = theme.folderCwpTint
    }

    function updateDefaultProjectTint() {
        if (hasBackend() && typeof backend.defaultProjectColor === "function") {
            var color = backend.defaultProjectColor()
            defaultProjectTint = (color && color.length > 0) ? color : ""
            return
        }
        defaultProjectTint = ""
    }

    function _decodeDragPayload(payload) {
        var text = String(payload || "").trim()
        if (text.length === 0) {
            return []
        }
        function normalizeDragPath(raw) {
            return PathUtils.normalizeFsPath(raw)
        }
        function decodeUriList(textValue) {
            var lines = String(textValue || "").split(/\r?\n/)
            var out = []
            for (var i = 0; i < lines.length; i++) {
                var line = String(lines[i] || "").trim()
                if (line.length === 0 || line.indexOf("#") === 0) {
                    continue
                }
                var normalized = normalizeDragPath(line)
                if (normalized.length > 0) {
                    out.push(normalized)
                }
            }
            return out
        }
        if (text.indexOf("__MYOS_PATHS__") === 0) {
            var raw = text.slice("__MYOS_PATHS__".length)
            try {
                var arr = JSON.parse(raw)
                if (!(arr && arr.length)) {
                    return []
                }
                var normalizedBatch = []
                for (var j = 0; j < arr.length; j++) {
                    var normalizedPath = normalizeDragPath(arr[j])
                    if (normalizedPath.length > 0) {
                        normalizedBatch.push(normalizedPath)
                    }
                }
                return normalizedBatch
            } catch (e) {
                return []
            }
        }
        if (text.indexOf("file://") === 0 || text.indexOf("\n") !== -1) {
            var listDecoded = decodeUriList(text)
            if (listDecoded.length > 0) {
                return listDecoded
            }
        }
        var normalizedSingle = normalizeDragPath(text)
        return normalizedSingle.length > 0 ? [normalizedSingle] : []
    }

    function _containsDirectory(paths) {
        if (!paths || paths.length === 0) {
            return false
        }
        if (!hasBackend() || typeof backend.isDir !== "function") {
            return false
        }
        for (var i = 0; i < paths.length; i++) {
            var p = String(paths[i] || "").trim()
            if (!p) {
                continue
            }
            if (backend.isDir(p)) {
                return true
            }
        }
        return false
    }

    function _setDialogButtonText(dialogRef, which, text) {
        if (!dialogRef || !dialogRef.standardButton) {
            return
        }
        var button = dialogRef.standardButton(which)
        if (button) {
            button.text = text
        }
    }

    function toggleUiLanguage() {
        var next = uiLanguage === "de" ? "en" : "de"
        if (hasBackend() && typeof backend.setLanguage === "function") {
            backend.setLanguage(next)
            if (typeof backend.currentLanguage === "function") next = backend.currentLanguage()
        }
        uiLanguage = next
        if (hasBackend() && typeof backend.setSetting === "function") backend.setSetting("General/language", uiLanguage)
    }

    function _moveReasonText(code) {
        switch (String(code || "")) {
        case "target_not_directory":
            return qsTr("Target is not a folder.")
        case "source_missing":
            return qsTr("Entry no longer exists.")
        case "target_inside_source":
            return qsTr("A folder cannot be moved into itself.")
        case "destination_exists":
            return qsTr("An entry with this name already exists at the destination.")
        case "move_failed":
            return qsTr("Move failed.")
        case "same_as_target":
            return qsTr("Entry is already in the target folder.")
        case "duplicate_source":
            return qsTr("Entry was selected multiple times.")
        case "acl_rules_conflict":
            return qsTr("Access rules are already waiting for this place; ask whoever manages the rights.")
        default:
            return qsTr("Operation skipped.")
        }
    }

    function _performMove(sources, targetDir) {
        if (!hasBackend()) {
            return
        }
        if (!sources || sources.length === 0 || !targetDir) {
            return
        }
        if (typeof backend.moveEntries === "function") {
            var batch = backend.moveEntries(sources, targetDir)
            // Dropping an entry back into its own folder is a silent no-op, not worth a report.
            var skipped = ((batch && batch.skipped) ? batch.skipped : []).filter(function(skip) {
                return !(skip && skip.reason === "already_in_target")
            })
            var errors = (batch && batch.errors) ? batch.errors : []
            if (batch && batch.moved && batch.moved.length > 0) {
                refreshAfterStructureChange()
            }
            if (errors.length > 0 || skipped.length > 0) {
                var lines = []
                var movedCount = (batch && batch.moved) ? batch.moved.length : 0
                if (movedCount > 0) {
                    lines.push(qsTr("Moved: %1").arg(movedCount))
                }
                if (errors.length > 0) {
                    if (lines.length > 0) {
                        lines.push("")
                    }
                    lines.push(qsTr("Could not move:"))
                    for (var e = 0; e < errors.length; e++) {
                        var err = errors[e]
                        var errSource = PathUtils.basename(err && err.source ? err.source : "")
                        var errReason = err && err.reason ? err.reason : "error"
                        lines.push("- " + errSource + ": " + _moveReasonText(errReason))
                    }
                }
                if (skipped.length > 0) {
                    if (lines.length > 0) {
                        lines.push("")
                    }
                    lines.push(qsTr("Skipped:"))
                    for (var s = 0; s < skipped.length; s++) {
                        var skip = skipped[s]
                        var skipSource = PathUtils.basename(skip && skip.source ? skip.source : "")
                        var skipReason = skip && skip.reason ? skip.reason : "skipped"
                        lines.push("- " + skipSource + ": " + _moveReasonText(skipReason))
                    }
                }
                moveReportMessage = lines.join("\n")
                moveReportDialog.open()
            }
            return
        }
        if (typeof backend.moveEntry !== "function") {
            return
        }
        var movedAny = false
        var seen = {}
        for (var i = 0; i < sources.length; i++) {
            var src = String(sources[i] || "").trim()
            if (!src || seen[src]) {
                continue
            }
            seen[src] = true
            if (src === targetDir) {
                continue
            }
            var ok = backend.moveEntry(src, targetDir)
            if (ok) {
                movedAny = true
            }
        }
        if (movedAny) {
            selectedEntryPaths = []
            updateSubProjects()
            updateFiles()
            updateTemplates()
            var listingPathSingle = templatesListingPath()
            standardFolders = listTemplates(listingPathSingle)
            updateStandardFolders()
        }
    }

    function moveEntry(sourcePath, targetDir) {
        if (!sourcePath) {
            return
        }
        // Drop semantics: support both uncommitted and committed CTD targets.
        // Prefer the explicit drop target (can be uncommitted), then fall back
        // to committed CTD when no concrete drop target is available.
        var resolvedTarget = PathUtils.normalizeFsPath(targetDir)
        if (resolvedTarget.length === 0) {
            resolvedTarget = PathUtils.normalizeFsPath(committedCTDPath)
        }
        if (resolvedTarget.length === 0) {
            return
        }
        var sources = _decodeDragPayload(sourcePath)
        if (!sources || sources.length === 0) {
            return
        }
        if (_containsDirectory(sources)) {
            pendingMoveSources = sources
            pendingMoveTargetDir = resolvedTarget
            var count = sources.length
            pendingMoveMessage = qsTr("Really move %1 folder(s) to \"%2\"?")
                .arg(count)
                .arg(resolvedTarget)
            folderMoveConfirmDialog.open()
            return
        }
        if (sources.length === 1 && hasBackend() && typeof backend.previewSortTargetForMove === "function") {
            var preview = backend.previewSortTargetForMove(String(sources[0] || ""), resolvedTarget)
            if (preview && preview.ok && preview.target) {
                moveReportMessage = qsTr("After moving, it will be sorted into:\n%1").arg(String(preview.target))
                moveReportDialog.open()
            }
        }
        _performMove(sources, resolvedTarget)
    }

    function createNewNote() {
        if (!hasBackend() || typeof backend.createNote !== "function") {
            return
        }
        var targetDir = filesCreateTarget(currentFilesPath())
        if (targetDir.length === 0) return
        var createdPath = backend.createNote(targetDir, "New Note")
        if (!createdPath || createdPath.length === 0) {
            moveReportMessage = qsTr("Could not create a note in this folder.")
            moveReportDialog.open()
            return
        }
        updateFiles()
        if (typeof backend.openMarkdown === "function") {
            if (!backend.openMarkdown(createdPath)) {
                openFileEntry(createdPath)
            }
        } else {
            openFileEntry(createdPath)
        }
    }

    function promptMoveSelectedIntoNewFolder(sourcePaths) {
        var incoming = sourcePaths || []
        var cleaned = []
        var seen = {}
        for (var i = 0; i < incoming.length; i++) {
            var value = String(incoming[i] || "").trim()
            if (!value || seen[value]) {
                continue
            }
            seen[value] = true
            cleaned.push(value)
        }
        if (cleaned.length < 2) {
            return
        }
        pendingFolderBatchSources = cleaned
        pendingFolderBatchName = qsTr("New Folder")
        moveSelectedFoldersDialog.open()
    }

    function requestCreateFolderAt(targetPath) {
        var target = String(targetPath || "").trim()
        if (target.length === 0) {
            return
        }
        pendingCreateFolderTargetPath = target
        pendingCreateFolderName = qsTr("New Folder")
        createFolderDialog.open()
    }

    /** Clipboard-Pfad für einen beliebigen Pfad (z. B. Quellordner). Verhindert, dass Drop auf Panel in „falsches“ Projekt-Clipboard geht. */
    function resolveClipboardPathForPath(anyPath) {
        var norm = PathUtils.normalizeFsPath(anyPath)
        if (norm.length === 0) return ""
        var marker = "/" + pathSegmentProjekte + "/"
        var idx = norm.indexOf(marker)
        if (idx >= 0) {
            return norm.slice(0, idx) + "/" + pathSegmentClipboard
        }
        return PathUtils.trimTrailingSlash(norm) + "/" + pathSegmentClipboard
    }

    function resolveClipboardPath() {
        var templatesRoot = PathUtils.trimTrailingSlash(resolveTemplatesRootPath())
        var templatesSuffix = "/" + pathSegmentTemplates
        if (templatesRoot.length > 0 && templatesRoot.indexOf(templatesSuffix) === (templatesRoot.length - templatesSuffix.length)) {
            return templatesRoot.slice(0, templatesRoot.length - templatesSuffix.length) + "/" + pathSegmentClipboard
        }
        var projectSuffix = "/" + pathSegmentProjekte
        var projectRoot = PathUtils.trimTrailingSlash(resolveProjectRootPath())
        if (projectRoot.length > 0 && projectRoot.indexOf(projectSuffix) === (projectRoot.length - projectSuffix.length)) {
            return projectRoot.slice(0, projectRoot.length - projectSuffix.length) + "/" + pathSegmentClipboard
        }
        var cwdNorm = PathUtils.normalizeFsPath(cwp)
        var marker = "/" + pathSegmentProjekte + "/"
        var markerIndex = cwdNorm.indexOf(marker)
        if (markerIndex >= 0) {
            return cwdNorm.slice(0, markerIndex) + "/" + pathSegmentClipboard
        }
        return PathUtils.trimTrailingSlash(cwdNorm) + "/" + pathSegmentClipboard
    }

    function ensureClipboardDirectory(targetPath) {
        var target = PathUtils.normalizeFsPath(targetPath)
        if (target.length === 0 || !hasBackend()) {
            return false
        }
        if (typeof backend.isDir === "function" && backend.isDir(target)) {
            return true
        }
        if (typeof backend.createFolder !== "function") {
            return false
        }
        var idx = target.lastIndexOf("/")
        var parentPath = idx > 0 ? target.slice(0, idx) : "/"
        var folderName = idx >= 0 ? target.slice(idx + 1) : target
        if (!folderName || folderName.length === 0) {
            return false
        }
        var createdPath = String(backend.createFolder(parentPath, folderName) || "")
        return createdPath.length > 0
    }

    function updateClipboardState() {
        var target = resolveClipboardPath()
        clipboardPath = target
        if (!hasBackend() || target.length === 0 || typeof backend.isDir !== "function" || !backend.isDir(target)) {
            clipboardHasItems = false
            return
        }
        var entries = listChildren(target)
        clipboardHasItems = entries && entries.length > 0
    }

    function openClipboard() {
        var target = resolveClipboardPath()
        if (target.length === 0) {
            return
        }
        ensureClipboardDirectory(target)
        setCwp(target, "folderBrowser.clipboard")
        commitCTD(target)
    }

    function dropToClipboard(payload) {
        var sourcePayload = String(payload || "")
        if (sourcePayload.length === 0) {
            return
        }
        // Ziel-Clipboard aus Quellpfad ableiten, damit Drop (z. B. auf ProjectsBrowser-Panel) im richtigen Projekt landet
        var sources = _decodeDragPayload(sourcePayload)
        var target = ""
        if (sources && sources.length > 0) {
            var firstPath = String(sources[0] || "").trim()
            var slash = firstPath.lastIndexOf("/")
            var parentDir = slash > 0 ? firstPath.slice(0, slash) : firstPath
            target = resolveClipboardPathForPath(parentDir)
        }
        if (target.length === 0) {
            target = resolveClipboardPath()
        }
        if (target.length === 0) {
            return
        }
        ensureClipboardDirectory(target)
        moveEntry(sourcePayload, target)
    }

    function requestRenameEntry(path) {
        var source = String(path || "").trim()
        if (!source || !hasBackend() || typeof backend.renameEntry !== "function") {
            return
        }
        var parts = source.split("/")
        var name = parts.length > 0 ? parts[parts.length - 1] : source
        pendingRenamePath = source
        pendingRenameName = name
        renameEntryDialog.open()
    }

    function requestRenameEntries(paths) {
        var incoming = paths || []
        var cleaned = []
        var seen = {}
        for (var i = 0; i < incoming.length; i++) {
            var value = String(incoming[i] || "").trim()
            if (!value || seen[value]) {
                continue
            }
            seen[value] = true
            cleaned.push(value)
        }
        if (cleaned.length === 0 || !hasBackend() || typeof backend.renameEntry !== "function") {
            return
        }
        if (cleaned.length === 1) {
            requestRenameEntry(cleaned[0])
            return
        }

        var filesOnly = []
        for (var j = 0; j < cleaned.length; j++) {
            var p = cleaned[j]
            if (typeof backend.isDir === "function" && backend.isDir(p)) {
                continue
            }
            filesOnly.push(p)
        }
        if (filesOnly.length === 1) {
            requestRenameEntry(filesOnly[0])
            return
        }
        if (filesOnly.length < 2) {
            moveReportMessage = qsTr("Batch rename currently works for files only.")
            moveReportDialog.open()
            return
        }

        pendingBatchRenamePaths = filesOnly
        if (typeof backend.suggestBatchRenameToken === "function") {
            pendingBatchReplaceFrom = backend.suggestBatchRenameToken(filesOnly)
        } else {
            pendingBatchReplaceFrom = ""
        }
        pendingBatchReplaceTo = pendingBatchReplaceFrom
        batchRenameDialog.open()
    }

    function requestDeleteEntries(paths) {
        var incoming = paths || []
        var cleaned = []
        var seen = {}
        for (var i = 0; i < incoming.length; i++) {
            var value = String(incoming[i] || "").trim()
            if (!value || seen[value]) {
                continue
            }
            seen[value] = true
            cleaned.push(value)
        }
        if (cleaned.length === 0 || !hasBackend() || typeof backend.deleteEntries !== "function") {
            return
        }
        var visibleEntries = listEntries(currentFilesPath())
        var embryoBlocked = []
        var deletable = []
        for (var j = 0; j < cleaned.length; j++) {
            var candidatePath = cleaned[j]
            var blocked = false
            for (var k = 0; k < (visibleEntries || []).length; k++) {
                var entry = visibleEntries[k]
                if (!entry) {
                    continue
                }
                if (String(entry.path || "") === candidatePath && entry.isEmbryo) {
                    blocked = true
                    break
                }
            }
            if (blocked) {
                embryoBlocked.push(candidatePath)
            } else {
                deletable.push(candidatePath)
            }
        }
        if (deletable.length === 0) {
            moveReportMessage = qsTr("Virtual embryo folders cannot be deleted.")
            moveReportDialog.open()
            return
        }
        cleaned = deletable
        if (embryoBlocked.length > 0) {
            moveReportMessage = qsTr("Embryo folders were skipped when deleting: %1").arg(embryoBlocked.length)
            moveReportDialog.open()
        }
        // Folders go with all their contents and permanently: always ask then. A few
        // files are deleted without asking, as before.
        var hasFolders = false
        for (var f = 0; f < cleaned.length; f++) {
            if (typeof backend.isDir === "function" && backend.isDir(cleaned[f])) hasFolders = true
        }
        if (cleaned.length <= 3 && !hasFolders) {
            performDeleteEntries(cleaned)
            return
        }
        pendingDeleteHasFolders = hasFolders
        pendingDeletePaths = cleaned
        deleteEntriesDialog.open()
    }

    /// Refresh file list and folder bars after entries were moved or deleted
    /// (folders may have appeared, vanished or turned back into embryos).
    function refreshAfterStructureChange() {
        selectedEntryPaths = []
        updateSubProjects()
        updateFiles()
        updateTemplates()
        var listingPath = templatesListingPath()
        standardFolders = listTemplates(listingPath)
        updateStandardFolders()
    }

    function performDeleteEntries(paths) {
        var result = backend.deleteEntries(paths || [])
        var deleted = (result && result.deleted) ? result.deleted.length : 0
        var errors = (result && result.errors) ? result.errors.length : 0
        // Deleted folders and reabsorbed (emptied) template folders change the folder bars too.
        refreshAfterStructureChange()
        if (errors > 0) {
            moveReportMessage = qsTr("Deleted: %1 file(s)\nNot deleted: %2 file(s)")
                .arg(deleted)
                .arg(errors)
            moveReportDialog.open()
        }
    }

    function listEntries(path) {
        if (hasBackend()) {
            return backend.listEntries(path, projectsShowHiddenFolders)
        }
        if (path === cwp) {
            var items = []
            for (var i = 0; i < fsModel.count; i++) {
                items.push({
                    name: fsModel.get(i, "fileName"),
                    isDir: fsModel.get(i, "fileIsDir")
                })
            }
            return items
        }
        return []
    }

    function applyEntries(entries) {
        // A re-listing of the same folder keeps the folder sizes measured so far (matched by path).
        var known = {}
        var previous = fileItemsAll || []
        for (var k = 0; k < previous.length; k++) {
            var old = previous[k]
            if (old && old.path && old.folderSizeBytes !== undefined && old.folderSizeBytes >= 0) {
                known[old.path] = old
            }
        }
        var next = entries || []
        for (var n = 0; n < next.length; n++) {
            var hit = next[n] && next[n].path ? known[next[n].path] : undefined
            if (hit) {
                next[n].folderSizeBytes = hit.folderSizeBytes
                next[n].folderSizeComplete = hit.folderSizeComplete
            }
        }
        fileItemsAll = next
        filterEntries()
        Qt.callLater(function() { recomputeTagBuckets() })
        Qt.callLater(requestAclSummary)
    }

    function entryPath(entry) {
        if (!entry) {
            return ""
        }
        if (entry.path && entry.path.length > 0) {
            return entry.path
        }
        if (entry.name && entry.name.length > 0) {
            if (entry.name.indexOf("/") === 0) {
                return entry.name
            }
            var base = cwp.endsWith("/") ? cwp.slice(0, -1) : cwp
            return base + "/" + entry.name
        }
        return ""
    }

    function _visibleIndexOfPath(path) {
        var target = String(path || "").trim()
        if (!target || !filesModel) {
            return -1
        }
        for (var i = 0; i < filesModel.count; i++) {
            var item = filesModel.get(i)
            if (!item) {
                continue
            }
            if (String(item.path || "").trim() === target) {
                return i
            }
        }
        return -1
    }

    function _visiblePathsInRange(pathA, pathB) {
        var idxA = _visibleIndexOfPath(pathA)
        var idxB = _visibleIndexOfPath(pathB)
        if (idxA < 0 || idxB < 0 || !filesModel) {
            return []
        }
        var start = Math.min(idxA, idxB)
        var end = Math.max(idxA, idxB)
        var range = []
        for (var i = start; i <= end; i++) {
            var item = filesModel.get(i)
            if (!item) {
                continue
            }
            var p = String(item.path || "").trim()
            if (p) {
                range.push(p)
            }
        }
        return range
    }

    function toggleEntrySelection(path, ctrlPressed, shiftPressed) {
        if (!path || path.length === 0) {
            return
        }
        if (shiftPressed) {
            if (!selectionAnchorPath || _visibleIndexOfPath(selectionAnchorPath) < 0) {
                selectedEntryPaths = [path]
                selectionAnchorPath = path
                return
            }
            var rangePaths = _visiblePathsInRange(selectionAnchorPath, path)
            if (ctrlPressed) {
                var mergedRange = selectedEntryPaths ? selectedEntryPaths.slice(0) : []
                for (var r = 0; r < rangePaths.length; r++) {
                    var rp = rangePaths[r]
                    if (mergedRange.indexOf(rp) === -1) {
                        mergedRange.push(rp)
                    }
                }
                selectedEntryPaths = mergedRange
            } else {
                selectedEntryPaths = rangePaths
            }
            return
        }
        if (ctrlPressed) {
            var toggled = selectedEntryPaths ? selectedEntryPaths.slice(0) : []
            var idx = toggled.indexOf(path)
            if (idx === -1) {
                toggled.push(path)
            } else {
                toggled.splice(idx, 1)
            }
            selectedEntryPaths = toggled
            selectionAnchorPath = path
            return
        }
        selectedEntryPaths = [path]
        selectionAnchorPath = path
    }

    function applySelectionBox(paths, additive) {
        var incoming = paths || []
        if (!additive) {
            selectedEntryPaths = incoming
            selectionAnchorPath = incoming.length > 0 ? String(incoming[incoming.length - 1] || "") : ""
            return
        }
        var merged = selectedEntryPaths ? selectedEntryPaths.slice(0) : []
        for (var i = 0; i < incoming.length; i++) {
            var value = incoming[i]
            if (value && merged.indexOf(value) === -1) {
                merged.push(value)
            }
        }
        selectedEntryPaths = merged
        if (incoming.length > 0) {
            selectionAnchorPath = String(incoming[incoming.length - 1] || "")
        }
    }

    function selectAllVisibleEntries() {
        var all = []
        if (!filesModel) {
            selectedEntryPaths = all
            return
        }
        for (var i = 0; i < filesModel.count; i++) {
            var item = filesModel.get(i)
            if (!item) {
                continue
            }
            var p = String(item.path || "").trim()
            if (p.length > 0) {
                all.push(p)
            }
        }
        selectedEntryPaths = all
        selectionAnchorPath = all.length > 0 ? all[0] : ""
    }

    function pruneEntrySelectionToVisible() {
        var source = fileItemsRaw || []
        var visible = {}
        for (var i = 0; i < source.length; i++) {
            var p = entryPath(source[i])
            if (p.length > 0) {
                visible[p] = true
            }
        }
        var next = []
        for (var j = 0; j < selectedEntryPaths.length; j++) {
            var selected = selectedEntryPaths[j]
            if (visible[selected]) {
                next.push(selected)
            }
        }
        if (next.length !== selectedEntryPaths.length) {
            selectedEntryPaths = next
        }
        if (selectionAnchorPath && next.indexOf(selectionAnchorPath) === -1) {
            selectionAnchorPath = next.length > 0 ? next[next.length - 1] : ""
        }
    }

    function filterEntries() {
        var baseFiltered = []
        var found = false
        var source = fileItemsAll || []
        for (var i = 0; i < source.length; i++) {
            var entry = source[i]
            if (entry.isDir && entry.name === myosDirName) {
                found = true
            }
            if (!projectsShowHiddenFolders && entry.name && entry.name.indexOf(".") === 0) {
                continue
            }
            if (!filesPane.showFolders && entry.isDir) {
                continue
            }
            baseFiltered.push(entry)
        }

        var filtered = baseFiltered
        var useTagFilter = selectedTags && selectedTags.length > 0
        if (useTagFilter) {
            var matchAll = tagMatchMode === "and"
            if (hasBackend() && typeof backend.listEntriesFiltered === "function") {
                var coreFiltered = backend.listEntriesFiltered(cwp, selectedTags, matchAll)
                filtered = []
                for (var j = 0; j < coreFiltered.length; j++) {
                    var coreEntry = coreFiltered[j]
                    if (!projectsShowHiddenFolders && coreEntry.name && coreEntry.name.indexOf(".") === 0) {
                        continue
                    }
                    if (!filesPane.showFolders && coreEntry.isDir) {
                        continue
                    }
                    filtered.push(coreEntry)
                }
            }
        }
        // ACL filter: only entries the selected role/person has any right on. Entries the
        // summary does not know yet (just created) are hidden until it is recomputed.
        // A "locked:<id>" chip shows the opposite: the entries closed to that role/person.
        if (selectedAclPrincipal.length > 0 && aclSummary.hasAcls) {
            var access = aclSummary.access || ({})
            var lockedPrefix = "locked:"
            var showLocked = selectedAclPrincipal.indexOf(lockedPrefix) === 0
            var principalId = showLocked ? selectedAclPrincipal.slice(lockedPrefix.length) : selectedAclPrincipal
            var aclFiltered = []
            for (var a = 0; a < filtered.length; a++) {
                var ids = access[entryPath(filtered[a])]
                if (!ids) continue
                if ((ids.indexOf(principalId) !== -1) !== showLocked) aclFiltered.push(filtered[a])
            }
            filtered = aclFiltered
        }
        fileItemsRaw = ListSort.sortEntries(filtered, filesSortKey, filesSortAscending)
        for (var m = 0; m < fileItemsRaw.length; m++) {
            var path = entryPath(fileItemsRaw[m])
            if (path.length > 0 && (!fileItemsRaw[m].path || fileItemsRaw[m].path.length === 0)) {
                fileItemsRaw[m].path = path
            }
        }
        pruneEntrySelectionToVisible()
        fileItemsOffset = 0
        filesModel.clear()
        appendNextChunk()
        if (!hasBackend()) {
            hasMyosInCwp = found
        }
    }

    function _fallbackFileTagsFromEntries() {
        var source = fileItemsAll || []
        var bag = {}
        for (var i = 0; i < source.length; i++) {
            var entry = source[i]
            if (entry.name && entry.name.indexOf(".") === 0) {
                continue
            }
            if (!filesPane.showFolders && entry.isDir) {
                continue
            }
            var entryTags = entry.tags || []
            for (var j = 0; j < entryTags.length; j++) {
                var value = String(entryTags[j] || "").trim()
                if (value.length > 0) {
                    bag[value] = true
                }
            }
        }
        var tags = Object.keys(bag)
        tags.sort(function(a, b) { return a.localeCompare(b) })
        return tags
    }

    function recomputeTagBuckets() {
        var targetPath = currentFilesPath()
        tagsIndexing = true
        var nextFolderTags = []
        var nextSubfolderTags = []
        var nextFileTags = []
        var nextFolderTagColors = ({})
        var nextSubfolderTagColors = ({})
        var nextFileTagColors = ({})
        var nextProjectTags = []
        if (hasBackend() && typeof backend.listTagBuckets === "function") {
            try {
                var buckets = backend.listTagBuckets(targetPath) || {}
                nextFolderTags = buckets.folderTags || []
                nextSubfolderTags = buckets.subfolderTags || []
                nextFileTags = buckets.fileTags || []
                nextFolderTagColors = buckets.folderTagColors || ({})
                nextSubfolderTagColors = buckets.subfolderTagColors || ({})
                nextFileTagColors = buckets.fileTagColors || ({})
            } catch (e) {
                nextFileTags = _fallbackFileTagsFromEntries()
            }
        } else {
            nextFileTags = _fallbackFileTagsFromEntries()
        }
        if (hasBackend() && typeof backend.listProjectTags === "function") {
            try {
                nextProjectTags = backend.listProjectTags(targetPath) || []
            } catch (e2) {
                nextProjectTags = []
            }
        }

        if (!nextFolderTags || nextFolderTags.length === 0) {
            nextFolderTags = []
        }
        if (!nextFileTags || nextFileTags.length === 0) {
            nextFileTags = []
        }

        var folderBag = {}
        for (var i = 0; i < nextFolderTags.length; i++) {
            var folderTag = String(nextFolderTags[i] || "").trim()
            if (folderTag.length > 0) {
                folderBag[folderTag] = true
            }
        }
        // Each tag once, in the first section it belongs to: this folder, subfolders
        // (only while folders are shown in the listing), files.
        var filteredSubfolderTags = []
        if (filesPane.showFolders) {
            for (var k = 0; k < nextSubfolderTags.length; k++) {
                var subfolderTag = String(nextSubfolderTags[k] || "").trim()
                if (subfolderTag.length > 0 && !folderBag[subfolderTag]) {
                    filteredSubfolderTags.push(subfolderTag)
                    folderBag[subfolderTag] = true
                }
            }
        }
        var filteredFileTags = []
        for (var j = 0; j < nextFileTags.length; j++) {
            var fileTag = String(nextFileTags[j] || "").trim()
            if (fileTag.length > 0 && !folderBag[fileTag]) {
                filteredFileTags.push(fileTag)
            }
        }

        folderTags = nextFolderTags
        subfolderTags = filteredSubfolderTags
        fileTags = filteredFileTags
        folderTagColors = nextFolderTagColors
        subfolderTagColors = nextSubfolderTagColors
        fileTagColors = nextFileTagColors
        availableTags = folderTags.concat(subfolderTags, fileTags)

        var suggestionBag = {}
        for (var p = 0; p < nextProjectTags.length; p++) {
            var projectTag = String(nextProjectTags[p] || "").trim()
            if (projectTag.length > 0 && !folderBag[projectTag]) {
                suggestionBag[projectTag] = true
            }
        }
        var contentTags = filteredSubfolderTags.concat(filteredFileTags)
        for (var f = 0; f < contentTags.length; f++) {
            var fileTagSuggestion = String(contentTags[f] || "").trim()
            if (fileTagSuggestion.length > 0 && !folderBag[fileTagSuggestion]) {
                suggestionBag[fileTagSuggestion] = true
            }
        }
        tagSuggestions = Object.keys(suggestionBag).sort(function(a, b) { return a.localeCompare(b) })

        var nextSelected = []
        for (var s = 0; s < selectedTags.length; s++) {
            var selected = selectedTags[s]
            if (availableTags.indexOf(selected) !== -1) {
                nextSelected.push(selected)
            }
        }
        if (nextSelected.length !== selectedTags.length) {
            selectedTags = nextSelected
        }
        tagsIndexing = false
    }

    function setFolderTagColor(tag, color) {
        var normalizedTag = String(tag || "").trim()
        var normalizedColor = String(color || "").trim()
        if (!normalizedTag || !normalizedColor) {
            return
        }
        if (hasBackend() && typeof backend.setFolderTagColor === "function") {
            backend.setFolderTagColor(currentFilesPath(), normalizedTag, normalizedColor)
            recomputeTagBuckets()
        }
    }

    function toggleTagSelection(tag) {
        if (!tag || tag.length === 0) {
            return
        }
        var next = selectedTags ? selectedTags.slice(0) : []
        var idx = next.indexOf(tag)
        if (idx === -1) {
            next.push(tag)
        } else {
            next.splice(idx, 1)
        }
        selectedTags = next
    }

    function addFolderTag(tag) {
        var raw = String(tag || "").trim()
        if (!raw.length) {
            return
        }
        var normalized = raw
        while (normalized.length > 0 && normalized[0] === "#") {
            normalized = normalized.slice(1).trim()
        }
        if (!normalized.length) {
            return
        }
        var next = folderTags ? folderTags.slice(0) : []
        if (next.indexOf(normalized) === -1) {
            next.push(normalized)
        }
        next.sort(function(a, b) { return a.localeCompare(b) })
        if (hasBackend() && typeof backend.setFolderTags === "function") {
            backend.setFolderTags(currentFilesPath(), next)
        }
        recomputeTagBuckets()
        filterEntries()
    }

    function removeFolderTag(tag) {
        var raw = String(tag || "").trim()
        if (!raw.length) {
            return
        }
        var normalized = raw
        while (normalized.length > 0 && normalized[0] === "#") {
            normalized = normalized.slice(1).trim()
        }
        if (!normalized.length) {
            return
        }
        var next = folderTags ? folderTags.slice(0) : []
        var idx = next.indexOf(normalized)
        if (idx !== -1) {
            next.splice(idx, 1)
        }
        if (hasBackend() && typeof backend.setFolderTags === "function") {
            backend.setFolderTags(currentFilesPath(), next)
        }
        recomputeTagBuckets()
        filterEntries()
    }

    /// ListModel exposes to delegates only the roles present when it was first filled,
    /// so every row carries the size roles from the start (-1 = not measured yet).
    function _withSizeRoles(entry) {
        var row = {}
        for (var key in entry) {
            row[key] = entry[key]
        }
        if (row.sizeBytes === undefined || row.sizeBytes === null) row.sizeBytes = -1
        if (row.folderSizeBytes === undefined || row.folderSizeBytes === null) row.folderSizeBytes = -1
        if (row.folderSizeComplete === undefined || row.folderSizeComplete === null) row.folderSizeComplete = false
        if (row.modifiedTs === undefined || row.modifiedTs === null) row.modifiedTs = -1
        if (row.accessedTs === undefined || row.accessedTs === null) row.accessedTs = -1
        row.tagsText = FormatUtils.tagsText(entry.tags)
        if (row.typeName === undefined || row.typeName === null) row.typeName = ""
        if (row.permissions === undefined || row.permissions === null) row.permissions = ""
        if (row.owner === undefined || row.owner === null) row.owner = ""
        if (row.group === undefined || row.group === null) row.group = ""
        return row
    }

    function appendNextChunk() {
        if (fileItemsOffset >= fileItemsRaw.length) return
        var end = Math.min(fileItemsRaw.length, fileItemsOffset + fileItemsChunk)
        for (var i = fileItemsOffset; i < end; i++) {
            filesModel.append(_withSizeRoles(fileItemsRaw[i]))
        }
        fileItemsOffset = end
    }

    function openFilePath(fullPath) {
        var resolved = String(fullPath || "").trim()
        if (!resolved) {
            return
        }
        var lower = resolved.toLowerCase()
        if (lower.endsWith(".md") && hasBackend() && typeof backend.openMarkdown === "function") {
            backend.openMarkdown(resolved)
            return
        }
        Qt.openUrlExternally(PathUtils.toFileUrl(resolved))
    }

    function openFileEntry(name) {
        var fullPath = name.indexOf("/") === 0 ? name : (cwp + "/" + name)
        openFilePath(fullPath)
    }

    function requestOpenWith(path) {
        pendingOpenWithPath = String(path || "").trim()
        if (!pendingOpenWithPath) {
            return
        }
        pendingOpenWithDialog.open()
    }

    function performOpenWith(path, command) {
        var target = String(path || "").trim()
        var cmd = String(command || "").trim()
        if (!target || !cmd) {
            return false
        }
        var ok = false
        if (hasBackend() && typeof backend.openWith === "function") {
            ok = backend.openWith(target, cmd)
        }
        if (ok) {
            pendingOpenWithCommand = cmd
            var next = []
            next.push(cmd)
            for (var i = 0; i < openWithQuickCommands.length; i++) {
                var value = String(openWithQuickCommands[i] || "").trim()
                if (!value || value === cmd) {
                    continue
                }
                next.push(value)
                if (next.length >= 4) {
                    break
                }
            }
            openWithQuickCommands = next
        }
        return ok
    }

    /// Number of entries in the trash of the shown project (side panel button).
    property int trashCount: 0

    function refreshTrash() {
        var path = currentFilesPath()
        trashCount = (path.length > 0 && hasBackend() && typeof backend.trashEntries === "function")
            ? (backend.trashEntries(path) || []).length : 0
    }

    function updateFiles() {
        var targetPath = currentFilesPath()
        if (targetPath.length === 0) {
            return
        }
        refreshTrash()
        if (hasBackend() && typeof backend.invalidateEntries === "function") {
            backend.invalidateEntries(targetPath)
        }
        var entries = listEntries(targetPath)
        applyEntries(entries)
        // Same folder re-listed (e.g. after a move) while sizes are on: measure again.
        if (folderSizesActive && hasBackend() && typeof backend.requestFolderSizes === "function") {
            folderSizesMeasuring = true
            backend.requestFolderSizes(targetPath)
        }
        if (hasBackend()) {
            hasMyosInCwp = backend.hasMyosDir(cwp)
            if (typeof backend.isProject === "function") {
                hasProjectInFilesPath = backend.isProject(targetPath)
            } else {
                hasProjectInFilesPath = false
            }
        }
        updateProjectCreateTarget()
        updateClipboardState()
    }

    function updateTemplates() {
        // The MyOS-folder row follows the CWD (with a lens on: the lens' folder).
        standardPath = cwp
        standardFolders = listTemplates(templatesListingPath())
        updateStandardFolders()
    }

    function updateThumbnail(fullPath, thumbUrl) {
        if (!fullPath || !thumbUrl) return
        updateEntryFields(fullPath, { thumb: thumbUrl })
    }

    /// Set fields on the listed entry with this path (raw/all arrays and the visible model).
    function updateEntryFields(fullPath, fields) {
        if (!fullPath || !fields) return
        function _updateArray(source) {
            var changed = false
            var out = source.slice(0)
            for (var i = 0; i < out.length; i++) {
                var item = out[i]
                if (!item) continue
                var itemPath = item.path ? item.path : (cwp + "/" + item.name)
                if (itemPath !== fullPath) continue
                var next = {}
                for (var key in item) {
                    next[key] = item[key]
                }
                for (var field in fields) {
                    next[field] = fields[field]
                }
                out[i] = next
                changed = true
            }
            return { changed: changed, value: out }
        }

        var allResult = _updateArray(fileItemsAll || [])
        if (allResult.changed) {
            fileItemsAll = allResult.value
        }
        var rawResult = _updateArray(fileItemsRaw || [])
        if (rawResult.changed) {
            fileItemsRaw = rawResult.value
        }

        if (filesModel) {
            for (var j = 0; j < filesModel.count; j++) {
                var modelItem = filesModel.get(j)
                if (!modelItem) continue
                var modelPath = modelItem.path ? modelItem.path : (cwp + "/" + modelItem.name)
                if (modelPath !== fullPath) continue
                for (var name in fields) {
                    filesModel.setProperty(j, name, fields[name])
                }
            }
        }
    }

    /// Apply a batch of live folder sizes in one pass (per-value updates would walk
    /// the whole list and model for every folder and stall the GUI on big listings).
    function applyFolderSizes(listingPath, items) {
        var listing = PathUtils.normalizeFsPath(currentFilesPath())
        if (PathUtils.normalizeFsPath(listingPath) !== listing || !items) return
        var byPath = {}
        var any = false
        var totalArrived = false
        for (var i = 0; i < items.length; i++) {
            var item = items[i]
            if (PathUtils.normalizeFsPath(item.path) === listing) {
                currentFolderSizeBytes = item.bytes
                currentFolderSizeComplete = item.complete
                if (item.complete) folderSizesMeasuring = false
                totalArrived = true
                continue
            }
            byPath[item.path] = item
            any = true
        }
        if (!any && !totalArrived) return
        // Entries are plain objects shared by fileItemsAll and fileItemsRaw; nothing binds to them.
        var all = fileItemsAll || []
        for (var a = 0; a < all.length; a++) {
            var hit = all[a] ? byPath[all[a].path] : undefined
            if (hit) {
                all[a].folderSizeBytes = hit.bytes
                all[a].folderSizeComplete = hit.complete
            }
        }
        for (var j = 0; j < filesModel.count; j++) {
            var row = byPath[filesModel.get(j).path]
            if (row) {
                filesModel.setProperty(j, "folderSizeBytes", row.bytes)
                filesModel.setProperty(j, "folderSizeComplete", row.complete)
            }
        }
        // Sorted by size: re-sort when a pass ends (the listing total arrives after pass 1
        // and pass 2), not on every value, so rows do not keep jumping while measuring.
        if (totalArrived && filesSortKey === "size") {
            filterEntries()
        }
    }

    onActiveChanged: if (active) turnedTo()
    HoverHandler {
        onHoveredChanged: if (hovered) window.turnedTo()
    }

    onCwpChanged: {
        selectedEntryPaths = []
        selectedTags = []
        lensSetCwd()
        updateSubProjects()
        if (hasBackend() && typeof backend.setContext === "function") {
            backend.setContext(cwp)
        }
        updateDefaultProjectTint()
        updateCurrentProjectTint()
        // Keep FilesPanel in sync whenever CWD changes (with a lens on: what it shows).
        commitCTD(filesPathWithLens())
        updateTemplates()
    }
    onCommittedCTDPathChanged: {
        selectedEntryPaths = []
        // The ACL panel keeps showing the previous folder until the new summary arrives
        // (computed in the background); its filter belongs to the folder it was set in.
        selectedAclPrincipal = ""
        currentFolderSizeBytes = -1
        currentFolderSizeComplete = false
        // New folder: sizes are off again until asked for; stop measuring the old one.
        // A sort by size ends with them and falls back to the previous column.
        if (filesSortKey === "size") {
            filesSortKey = filesBaseSortKey
            filesSortAscending = filesBaseSortAscending
        }
        folderSizesActive = false
        folderSizesMeasuring = false
        if (hasBackend() && typeof backend.cancelFolderSizes === "function") {
            backend.cancelFolderSizes()
        }
        updateFiles()
    }

    function updateSubProjects() {
        var query = searchText.trim()
        if (query.length === 0) {
            subProjects = listRightFolders(cwp)
            return
        }
        var mode = "direct"
        if (query[0] === "+") {
            mode = "deep"
            query = query.slice(1).trim()
        } else if (query[0] === "#") {
            mode = "all"
            query = query.slice(1).trim()
        }
        var lower = query.toLowerCase()
        if (hasBackend() && mode !== "direct") {
            mode = "direct"
        }
        if (!hasBackend()) {
            mode = "direct"
        }
        if (mode === "direct") {
            var directItems = listRightFolders(cwp)
            if (lower.length === 0) {
                subProjects = directItems
                return
            }
            subProjects = directItems.filter(function(item){
                return nameForItem(item).toLowerCase().indexOf(lower) !== -1
            })
            return
        }
    }

    function updateStandardFolders() {
        var query = level2SearchText.trim()
        if (query.length === 0) {
            standardFoldersFiltered = standardFolders
            return
        }
        if (query[0] === "+" || query[0] === "#") {
            query = query.slice(1).trim()
        }
        var lower = query.toLowerCase()
        if (lower.length === 0) {
            standardFoldersFiltered = standardFolders
            return
        }
        standardFoldersFiltered = standardFolders.filter(function(item){
            return nameForItem(item).toLowerCase().indexOf(lower) !== -1
        })
    }

    function clearSearchAfterNavigate() {
        if (searchText.trim().length === 0) return
        searchText = ""
        searchActive = false
    }

    function shortenPathForDisplay(path) {
        var trimmed = path[0] === "/" ? path.slice(1) : path
        var parts = trimmed.split("/").filter(function(p){ return p.length > 0 })
        var keepCount = Math.max(1, searchPathPrefixDepth + 1)
        if (parts.length <= keepCount) return path
        return ".../" + parts.slice(parts.length - keepCount).join("/")
    }

    function lastPathSegment(path) {
        var parts = path.split("/").filter(function(p){ return p.length > 0 })
        return parts.length > 0 ? parts[parts.length - 1] : "/"
    }

    function parentPaths() {
        var parts = cwp.split("/").filter(function(p){ return p.length > 0 })
        var paths = []
        for (var i = 0; i < parts.length - 1; i++) {
            paths.push("/" + parts.slice(0, i + 1).join("/"))
        }
        return paths
    }

    function visibleParentPaths() {
        var parents = parentPaths()
        if (parents.length <= maxVerticalParents) return parents
        return parents.slice(Math.max(0, parents.length - maxVerticalParents))
    }

    // F2 renames the entries selected in the FilesPanel (folders in the browser rows: hold
    // the mouse button, or right click).
    Shortcut {
        sequences: ["F2"]
        enabled: !renameActive && !renameEntryDialog.visible
        onActivated: {
            if ((selectedEntryPaths || []).length > 0) requestRenameEntries(selectedEntryPaths)
        }
    }

    function beginRename(path) {
        renameActive = true
        renameTargetPath = path
        var parts = path.split("/").filter(function(p){ return p.length > 0 })
        renameDraft = parts.length > 0 ? parts[parts.length - 1] : ""
        if (projectsBrowser) {
            // Draft first: setting the target switches the field on, which takes the draft
            // at that moment (otherwise the field opens empty).
            projectsBrowser.renameDraft = renameDraft
            projectsBrowser.renameTargetPath = renameTargetPath
        }
    }

    function cancelRename() {
        renameActive = false
        renameTargetPath = ""
        renameDraft = ""
        if (projectsBrowser) {
            projectsBrowser.renameTargetPath = ""
            projectsBrowser.renameDraft = ""
        }
    }

    function commitRename(acceptedNewName) {
        var draftToUse = (typeof acceptedNewName === "string" && acceptedNewName.length > 0) ? acceptedNewName : renameDraft
        if (!renameActive) return
        var trimmed = draftToUse.trim().replace(/\s+/g, " ")
        var parts = renameTargetPath.split("/").filter(function(p){ return p.length > 0 })
        var oldName = parts.length > 0 ? parts[parts.length - 1] : ""
        if (trimmed.length === 0) {
            cancelRename()
            return
        }
        if (trimmed === oldName) {
            cancelRename()
            return
        }
        var success = false
        var newPath = ""
        if (hasBackend() && typeof backend.renameEntry === "function") {
            var newPathResult = backend.renameEntry(renameTargetPath, trimmed)
            success = (typeof newPathResult === "string" && newPathResult.length > 0)
            if (success) newPath = newPathResult
        }
        if (success) {
            if (cwp === renameTargetPath || cwp.indexOf(renameTargetPath + "/") === 0) {
                cwp = newPath + cwp.slice(renameTargetPath.length)
            }
            setCwp(cwp)
            updateSubProjects()
        }
        cancelRename()
    }

    function warnIfMissing(target, propName, label) {
        if (!target || !(propName in target)) {
        }
    }

    function warnIfMissingAny(target, propNames, label) {
        for (var i = 0; i < propNames.length; i++) {
            warnIfMissing(target, propNames[i], label)
        }
    }

    Component.onCompleted: {
        Qt.application.windowIcon = Qt.resolvedUrl(iconFolder)
        window.contentItem.transform = [setupFlip]
        if (hasBackend() && typeof backend.setting === "function") {
            darkTheme = backend.setting("General/darkTheme") === true
            var language = String(backend.setting("General/language") || "de")
            if (typeof backend.setLanguage === "function" && language !== backend.currentLanguage()) backend.setLanguage(language)
            projectsBrowserVisible = backend.setting("Scope/projectsRow") === true
            templatesBrowserVisible = backend.setting("Scope/templatesRow") === true
        }
        settingsRead = true
        if (hasBackend() && typeof backend.currentLanguage === "function") {
            uiLanguage = backend.currentLanguage()
        }
        if (hasBackend() && typeof backend.filesViewStyle === "function") {
            filesItemStyle = backend.filesViewStyle()
        }
        if (hasBackend() && typeof backend.filesXray === "function") {
            xrayEnabled = backend.filesXray()
        }
        if (hasBackend() && typeof backend.filesListColumns === "function") {
            filesListColumns = backend.filesListColumns()
        }
        if (hasBackend() && typeof backend.filesSort === "function") {
            var sort = backend.filesSort()
            filesSortKey = sort.key
            filesSortAscending = sort.ascending
            filesBaseSortKey = sort.key
            filesBaseSortAscending = sort.ascending
        }
        var startPath = (typeof scopeStartPath !== "undefined" && scopeStartPath) ? scopeStartPath : cwp
        if (!hasBackend() && (!startPath || startPath === cwp)) {
            var resolved = Qt.resolvedUrl(".")
            if (resolved.indexOf("file://") === 0) {
                startPath = resolved.slice(7)
            }
        }
        var cwpBeforeInit = String(cwp || "")
        setCwp(startPath)
        // If startup path equals existing cwp, onCwpChanged will not fire.
        // Run one explicit bootstrap so template/file models don't stay on placeholders.
        if (String(cwp || "") === cwpBeforeInit) {
            selectedEntryPaths = []
            selectedTags = []
            lensSetCwd()
            updateSubProjects()
            if (hasBackend() && typeof backend.setContext === "function") {
                backend.setContext(cwp)
            }
            updateDefaultProjectTint()
            updateCurrentProjectTint()
            if (String(committedCTDPath || "").trim().length === 0) {
                commitCTD(cwp)
            }
            updateTemplates()
            var listingPathInit = templatesListingPath()
            standardFolders = listTemplates(listingPathInit)
            updateStandardFolders()
        }
        updateBrowserLayout()
        warnIfMissingAny(templatesBrowser, [
            "projectTint",
            "projectTintBorder",
            "showEmbryos",
            "showSearchToggle",
            "showStyleToggle"
        ], "templatesBrowser")
        warnIfMissingAny(projectsBrowser, [
            "projectTint",
            "projectTintBorder",
            "showEmbryos",
            "showSearchToggle",
            "showStyleToggle"
        ], "projectsBrowser")
        warnIfMissingAny(filesPane, [
            "projectTint",
            "projectTintBorder",
            "showCreateProject"
        ], "filesPane")
    }
    
    property bool newSubprojectEditing: false
    property string newSubprojectDraft: ""
    property bool searchActive: false
    property string searchText: ""
    property bool level2SearchActive: false
    property string level2SearchText: ""
    property bool renameActive: false
    property string renameTargetPath: ""
    property string renameDraft: ""
    property string folderContextPath: ""

    property bool browserLayoutRefreshPending: false

    function scheduleBrowserLayoutRefresh() {
        if (browserLayoutRefreshPending) return
        browserLayoutRefreshPending = true
        Qt.callLater(function() {
            browserLayoutRefreshPending = false
            updateBrowserLayout()
        })
    }

    onVerticalProjectViewChanged: scheduleBrowserLayoutRefresh()
    onLevel2VerticalViewChanged: scheduleBrowserLayoutRefresh()
    onProjectsBrowserVisibleChanged: scheduleBrowserLayoutRefresh()
    onMinimalViewChanged: scheduleBrowserLayoutRefresh()
    onTemplatesBrowserVisibleChanged: scheduleBrowserLayoutRefresh()
    onFilesPaneVisibleChanged: scheduleBrowserLayoutRefresh()
    Connections {
        target: projectsBrowser
        function onImplicitWidthChanged() {
            if (projectsBrowser && projectsBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
        function onVerticalPreferredWidthChanged() {
            if (projectsBrowser && projectsBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
        function onVerticalAutoWidthChanged() {
            if (projectsBrowser && projectsBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
    }
    Connections {
        target: templatesBrowser
        function onImplicitWidthChanged() {
            if (templatesBrowser && templatesBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
        function onVerticalPreferredWidthChanged() {
            if (templatesBrowser && templatesBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
        function onVerticalAutoWidthChanged() {
            if (templatesBrowser && templatesBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
    }
    Connections {
        target: backend
        function onLanguageChanged(code) {
            uiLanguage = String(code || "de")
        }
        function onThumbnailReady(path, thumbUrl) {
            updateThumbnail(path, thumbUrl)
        }
        function onFolderSizesReady(listingPath, items) {
            applyFolderSizes(listingPath, items)
        }
        function onAclSummaryReady(listingPath, summary) {
            applyAclSummary(listingPath, summary)
        }
        function onFilingDone() {
            updateFiles()
        }
        function onEntriesReady(path, entries) {
            if (path === cwp) {
                applyEntries(entries)
                hasMyosInCwp = backend.hasMyosDir(cwp)
            }
        }
    }
    onSearchTextChanged: updateSubProjects()
    onLevel2SearchTextChanged: updateStandardFolders()
    onTagFilterSourceChanged: {
        selectedTags = []
        recomputeTagBuckets()
        filterEntries()
    }
    onSelectedTagsChanged: filterEntries()
    onSelectedAclPrincipalChanged: filterEntries()
    onSearchActiveChanged: {
        if (!searchActive) {
            searchText = ""
        }
    }
    onLevel2SearchActiveChanged: {
        if (!level2SearchActive) {
            level2SearchText = ""
        }
        updateStandardFolders()
    }
    onLevel2ButtonStyleChanged: scheduleBrowserLayoutRefresh()

    function setBrowserParent(item, newParent) {
        if (!item || !newParent) return
        if (item.parent !== newParent) {
            item.parent = newParent
        }
        var isFolderBrowser = item.hasOwnProperty("verticalView")
        if (isFolderBrowser) {
            item.anchors.fill = undefined
            item.anchors.left = newParent.left
            item.anchors.right = newParent.right
            item.anchors.top = newParent.top
            item.anchors.bottom = undefined
        } else {
            item.anchors.fill = newParent
        }
    }

    function setSlotSize(slot, child, inRowLayout, isFilesPane) {
        if (!slot || !child) return
        var effectivelyVisible = isFilesPane ? filesPaneVisible : child.visible
        if (child.visible === false || !effectivelyVisible) {
            slot.Layout.fillWidth = false
            slot.Layout.preferredWidth = 0
            slot.Layout.minimumWidth = 0
            slot.Layout.maximumWidth = 0
            slot.Layout.fillHeight = false
            slot.Layout.preferredHeight = 0
            slot.Layout.minimumHeight = 0
            slot.Layout.maximumHeight = 0
            return
        }
        var isFolderBrowser = child.hasOwnProperty("verticalView")
        var wantsFixedWidth = isFolderBrowser && child.verticalView
        var wantsFillHeight = isFilesPane
        if (wantsFixedWidth) {
            var preferred = (child.verticalPreferredWidth && child.verticalPreferredWidth > 0)
                ? child.verticalPreferredWidth
                : child.implicitWidth
            slot.Layout.fillWidth = false
            slot.Layout.preferredWidth = preferred
            slot.Layout.minimumWidth = preferred
            slot.Layout.maximumWidth = preferred
        } else {
            slot.Layout.fillWidth = true
            slot.Layout.preferredWidth = -1
            slot.Layout.minimumWidth = 0
            slot.Layout.maximumWidth = -1
        }
        if (isFilesPane) {
            slot.Layout.minimumWidth = Math.max(280, slot.Layout.minimumWidth || 0)
        }
        if (wantsFillHeight) {
            slot.Layout.fillHeight = true
            slot.Layout.preferredHeight = -1
            slot.Layout.minimumHeight = 0
            slot.Layout.maximumHeight = (isFilesPane && filesPanelMaxHeight > 0) ? filesPanelMaxHeight : -1
            slot.Layout.alignment = 0
        } else if (isFolderBrowser) {
            slot.Layout.fillHeight = false
            slot.Layout.preferredHeight = Qt.binding(function() { return child.implicitHeight })
            slot.Layout.minimumHeight = Qt.binding(function() { return child.implicitHeight })
            slot.Layout.maximumHeight = Qt.binding(function() { return child.implicitHeight })
            slot.Layout.alignment = Qt.AlignTop
        } else {
            slot.Layout.fillHeight = true
            slot.Layout.preferredHeight = -1
            slot.Layout.minimumHeight = 0
            slot.Layout.maximumHeight = -1
            slot.Layout.alignment = 0
        }
    }

    function updateBrowserLayout() {
        var minimal = minimalView
        var templatesVertical = level2VerticalView
        var projectsVertical = verticalProjectView
        var ph_th = !minimal && (!templatesVertical && !projectsVertical)
        var pv_th = !minimal && (!templatesVertical && projectsVertical)
        var ph_tv = !minimal && (templatesVertical && !projectsVertical)
        var pv_tv = !minimal && (templatesVertical && projectsVertical)

        case_M.visible = minimal
        case_PH_TH.visible = ph_th
        case_PV_TH.visible = pv_th
        case_PH_TV.visible = ph_tv
        case_PV_TV.visible = pv_tv

        if (minimal) {
            // One line: the projects row is only its CWD button, the MyOS folders follow.
            setBrowserParent(projectsBrowser, slotProjects_M)
            setBrowserParent(templatesBrowser, slotTemplates_M)
            setBrowserParent(filesPane, slotFiles_M)
            setSlotSize(slotTemplates_M, templatesBrowser, true, false)
            setSlotSize(slotFiles_M, filesPane, true, true)
            slotProjects_M.Layout.fillWidth = false
            slotProjects_M.Layout.preferredWidth = Qt.binding(function() { return projectsBrowser.minimalWidth })
            slotProjects_M.Layout.preferredHeight = Qt.binding(function() { return projectsBrowser.implicitHeight })
            slotProjects_M.Layout.alignment = Qt.AlignTop
        } else if (ph_th) {
            setBrowserParent(templatesBrowser, slotTemplates_PH_TH)
            setBrowserParent(projectsBrowser, slotProjects_PH_TH)
            setBrowserParent(filesPane, slotFiles_PH_TH)
            setSlotSize(slotTemplates_PH_TH, templatesBrowser, false, false)
            setSlotSize(slotProjects_PH_TH, projectsBrowser, false, false)
            setSlotSize(slotFiles_PH_TH, filesPane, true, true)
        } else if (pv_th) {
            setBrowserParent(projectsBrowser, slotProjects_PV_TH)
            setBrowserParent(templatesBrowser, slotTemplates_PV_TH)
            setBrowserParent(filesPane, slotFiles_PV_TH)
            setSlotSize(slotProjects_PV_TH, projectsBrowser, true, false)
            setSlotSize(slotTemplates_PV_TH, templatesBrowser, false, false)
            setSlotSize(slotFiles_PV_TH, filesPane, true, true)
        } else if (ph_tv) {
            setBrowserParent(projectsBrowser, slotProjects_PH_TV)
            setBrowserParent(templatesBrowser, slotTemplates_PH_TV)
            setBrowserParent(filesPane, slotFiles_PH_TV)
            setSlotSize(slotProjects_PH_TV, projectsBrowser, false, false)
            setSlotSize(slotTemplates_PH_TV, templatesBrowser, true, false)
            setSlotSize(slotFiles_PH_TV, filesPane, true, true)
        } else if (pv_tv) {
            setBrowserParent(projectsBrowser, slotProjects_PV_TV)
            setBrowserParent(templatesBrowser, slotTemplates_PV_TV)
            setBrowserParent(filesPane, slotFiles_PV_TV)
            setSlotSize(slotProjects_PV_TV, projectsBrowser, true, false)
            setSlotSize(slotTemplates_PV_TV, templatesBrowser, true, false)
            setSlotSize(slotFiles_PV_TV, filesPane, true, true)
        }
        // Force folder browsers to recalc height so slots get correct size.
        // Note: QQuickItem.polish is a signal in QML, not a callable function, so we do not call it from here.
        if (templatesBrowser && typeof templatesBrowser.scheduleContentHeightUpdate === "function") {
            templatesBrowser.scheduleContentHeightUpdate()
        }
        if (projectsBrowser && typeof projectsBrowser.scheduleContentHeightUpdate === "function") {
            projectsBrowser.scheduleContentHeightUpdate()
        }
    }

    Component { // SearchField Component
        id: searchFieldComponent
        Item {
            id: searchFieldRoot
            property alias input: searchInput
            width: parent ? parent.width : 0
            height: compactButtonHeight
            clip: true
            Rectangle {
                anchors.fill: parent
                radius: TagChips.CHIP_RADIUS_COMPACT
                color: theme.card
                border.color: theme.pillBorder
                opacity: searchActive ? 1 : 0
                Behavior on opacity {
                    NumberAnimation { duration: 160; easing.type: Easing.OutCubic }
                }
                TextField {
                    id: searchInput
                    anchors.fill: parent
                    anchors.margins: 4
                    text: searchText
                    placeholderText: qsTr("Search      + deep    # all")
                    font.pixelSize: baseFont
                    selectByMouse: true
                    color: theme.text
                    placeholderTextColor: theme.textMuted
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 6
                    rightPadding: 6
                    topPadding: 1
                    bottomPadding: 0
                    background: Rectangle { color: "transparent" }
                    onTextChanged: searchText = text
                    onVisibleChanged: {
                        if (visible && searchActive) {
                            forceActiveFocus()
                            selectAll()
                        }
                    }
                    Keys.onEscapePressed: {
                        searchText = ""
                        searchActive = false
                    }
                }
            }
        }
    }

    FolderMoveConfirmDialog { id: folderMoveConfirmDialog; window: window }

    MoveReportDialog { id: moveReportDialog; window: window }

    OpenWithDialog { id: pendingOpenWithDialog; window: window }

    CreateFolderDialog { id: createFolderDialog; window: window }

    MoveSelectedFoldersDialog { id: moveSelectedFoldersDialog; window: window }

    RenameEntryDialog { id: renameEntryDialog; window: window }
    ProjectRemoveDialog { id: projectRemoveDialog; window: window }
    TrashDialog {
        id: trashDialog
        window: window
        onTrashChanged: window.refreshAfterStructureChange()
    }
    AclRoleDialog {
        id: aclRoleDialog
        window: window
        onRightsChanged: window.requestAclSummary()
    }

    AclPersonDialog {
        id: aclPersonDialog
        window: window
        onMembershipChanged: window.requestAclSummary()
    }

    BatchRenameDialog { id: batchRenameDialog; window: window }

    DeleteEntriesDialog { id: deleteEntriesDialog; window: window }

    onEdgeDockStateChanged: {
        if (edgeDockEnabled) {
            if (edgeDockState === "collapsed") {
                edgeDockStoredExpandedWidth = width
                edgeDockStoredExpandedHeight = height
                height = edgeDockTriggerBarHeight
            } else if (_previousEdgeDockState === "collapsed" && edgeDockState !== "collapsed") {
                if (edgeDockStoredExpandedWidth > 0 && edgeDockStoredExpandedHeight > 0) {
                    width = edgeDockStoredExpandedWidth
                    height = edgeDockStoredExpandedHeight
                }
            }
            if (_previousEdgeDockState === "expandedWithFiles" && edgeDockState !== "expandedWithFiles") {
                edgeDockStoredWidth = width
                edgeDockStoredHeight = height
            } else if (edgeDockState === "expandedWithFiles" && edgeDockStoredWidth > 0 && edgeDockStoredHeight > 0) {
                width = edgeDockStoredWidth
                height = edgeDockStoredHeight
            }
            filesPaneVisible = (edgeDockState === "expandedWithFiles")
            _previousEdgeDockState = edgeDockState
        }
    }
    onEdgeDockEnabledChanged: {
        if (edgeDockEnabled) {
            // Beim Einschalten: aktuelle Größe für "expandedWithFiles" merken, Fenster auf Browser-Höhe verkleinern
            edgeDockStoredWidth = width
            edgeDockStoredHeight = height
            var browserOnlyHeight = Math.max(200, height - Math.min(filesPanelMaxHeight, Math.round(height * 0.5)))
            height = browserOnlyHeight
            edgeDockState = "expanded"
            filesPaneVisible = false
            _previousEdgeDockState = edgeDockState
        } else {
            // Beim Ausschalten: Fenstergröße wiederherstellen (gespeicherte Größe von vor Edge-Dock)
            if (edgeDockStoredWidth > 0 && edgeDockStoredHeight > 0) {
                width = edgeDockStoredWidth
                height = edgeDockStoredHeight
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: theme.bg
        ColumnLayout { // MainRows
            anchors.fill: parent
            spacing: 6
            anchors.margins: Math.max(4, Math.round(16 / 3))

            // Edge-Dock: X11 = top-edge strip (4px), Wayland = visible bar (24px). Click toggles collapsed <-> expanded.
            Rectangle {
                visible: edgeDockEnabled
                Layout.fillWidth: true
                Layout.preferredHeight: visible ? edgeDockTriggerBarHeight : 0
                Layout.minimumHeight: visible ? edgeDockTriggerBarHeight : 0
                color: (edgeDockTriggerBarHeight >= 20) ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.35) : "transparent"
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (!edgeDockEnabled) return
                        if (edgeDockState === "collapsed") {
                            edgeDockState = "expanded"
                        } else {
                            edgeDockState = "collapsed"
                        }
                    }
                }
                Text {
                    visible: edgeDockTriggerBarHeight >= 20
                    anchors.centerIn: parent
                    text: edgeDockCollapsed ? qsTr("Scope \u25BC") : qsTr("Scope \u25B2")
                    color: theme.smallButtonText
                    font.pixelSize: Math.max(10, baseFont - 2)
                }
            }

            RowLayout { // Buttonbar
                visible: !edgeDockCollapsed
                Layout.fillWidth: true
                Layout.preferredHeight: topButtonFlow.implicitHeight
                Layout.minimumHeight: topButtonFlow.implicitHeight
                Layout.maximumHeight: topButtonFlow.implicitHeight
                spacing: 8
                Flow {
                    id: topButtonFlow
                    Layout.fillWidth: true
                    width: parent.width
                    spacing: 8
                Rectangle { // Setup: the back of Scope, far left
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: "transparent"
                    border.width: 0
                    implicitWidth: setupLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: setupLabel
                        anchors.centerIn: parent
                        text: "⚙"
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: window.flipSetup(true)
                    }
                }

                Rectangle { // Minimal view (M)
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: minimalView ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.28) : "transparent"
                    border.width: 0
                    implicitWidth: minimalViewLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: minimalViewLabel
                        anchors.centerIn: parent
                        text: "M"
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        id: minimalViewArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: minimalView = !minimalView
                    }
                    ToolTip.visible: minimalViewArea.containsMouse
                    ToolTip.delay: 600
                    ToolTip.text: qsTr("Minimal view: the current folder top left, the path above it on hover")
                }

                }
            }

            Item {
                id: layoutCases
                visible: !edgeDockCollapsed
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout { // Layout M (minimal view)
                    id: case_M
                    anchors.fill: parent
                    spacing: 0
                    visible: false
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        spacing: 2
                        Item { id: slotProjects_M; Layout.fillHeight: false }
                        Item { id: slotTemplates_M; Layout.fillWidth: true; Layout.alignment: Qt.AlignTop }
                    }
                    Item { id: slotFiles_M; Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumWidth: 280 }
                }

                ColumnLayout { // Layout PH_TH   
                    id: case_PH_TH
                    anchors.fill: parent
                    spacing: 0
                    visible: false
                    Item { id: slotTemplates_PH_TH; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item {
                        id: slotProjects_PH_TH
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Item { id: slotFiles_PH_TH; Layout.fillWidth: true; Layout.fillHeight: true; Layout.minimumWidth: 280 }
                }

                ColumnLayout { // Layout PV_TH
                    id: case_PV_TH
                    anchors.fill: parent
                    spacing: 12
                    visible: false
                    Item { id: slotTemplates_PV_TH; Layout.fillWidth: true; Layout.fillHeight: false }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 0
                        Item { id: slotProjects_PV_TH; Layout.fillWidth: false; Layout.fillHeight: true }
                        Item {
                            id: slotFiles_PV_TH
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumWidth: 280
                            Layout.leftMargin: -window.filesPanelOverlapPx
                        }
                    }
                }

                ColumnLayout { // Layout PH_TV
                    id: case_PH_TV
                    anchors.fill: parent
                    spacing: 0
                    visible: false
                    Item { id: slotProjects_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 0
                        Item { id: slotTemplates_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                        Item {
                            id: slotFiles_PH_TV
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumWidth: 280
                            Layout.leftMargin: -window.filesPanelOverlapPx
                        }
                    }
                }

                RowLayout {   // Layout PV_TV   
                    id: case_PV_TV
                    anchors.fill: parent
                    spacing: 0
                    visible: false
                    Item { id: slotProjects_PV_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item { id: slotTemplates_PV_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item {
                        id: slotFiles_PV_TV
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumWidth: 280
                        Layout.leftMargin: -window.filesPanelOverlapPx
                    }
                }
            }

        }

        Item {
            id: floatingPool
            anchors.fill: parent
            visible: false
        }

        Menu {
            id: folderContextMenu
            parent: floatingPool.parent
            MenuItem {
                text: qsTr("Rename")
                onTriggered: beginRename(folderContextPath)
            }
            MenuItem {
                text: qsTr("Delete")
                onTriggered: requestDeleteEntries([folderContextPath])
            }
        }

        FolderBrowser {  // TemplatesBrowser
            id: templatesBrowser
            debugName: "TemplatesBrowser"
            parent: floatingPool
            visible: templatesBrowserVisible && !edgeDockEnabled
            verticalPreferredHeight: 390
            // With a lens on: the lens' folder in the project it looks into (A1, A4).
            path: window.lensInProject ? String(window.lensState.target || "") : standardPath
            pathDisplayPrefix: window.lensInProject ? String(window.lensState.project_dir || "") : cwp
            lensFrameRoot: window.lensInProject ? String(window.lensState.project_dir || "") : ""
            showEmbryos: window.templatesShowEmbryos
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            tintPathAsProject: false
            cwdOpacity: 1.0
            pathProjectOpacity: 0.7
            folderProjectOpacity: 0.55
            embryoOpacity: window.embryoOpacity
            embryoBadgeOpacity: window.embryoBadgeOpacity
            debugLayout: false
            allowDrags: true
            allowDrops: true
            folders: standardFoldersFiltered
            childrenProvider: function(targetPath) { return listTemplates(targetPath) }
            verticalView: level2VerticalView && !window.minimalView
            pathShownBelow: window.minimalView ? (window.lensInProject ? String(window.lensState.project_dir || "") : cwp) : ""
            buttonStyle: level2ButtonStyle
            allowLargeIcons: true
            showModeToggle: !window.minimalView
            narrowButtons: window.minimalView
            showSearchToggle: true
            // Minimal view: search and Clipboard are in the tools of the CWD dropdown (the
            // search field still opens here), no menu.
            showSearchButton: !window.minimalView
            wrapFolders: !window.minimalView  // M is one line: the folders right of the CWD
            showClipboardButton: !window.minimalView
            showStyleToggle: !window.minimalView
            showEmbryoToggle: !window.minimalView
            showThemeToggle: false
            showCreateFolderButton: true
            clipboardHasItems: window.clipboardHasItems
            baseFont: window.baseFont
            compactButtonHeight: window.compactButtonHeight
            largeButtonHeight: window.largeButtonHeight
            largeButtonPadding: Math.round(window.largeButtonPadding * 0.5)
            iconSizeSmall: window.iconSizeSmall
            iconSizeLarge: window.iconSizeLarge
            iconFolder: window.iconFolder
            iconFolderOff: window.iconFolderOff
            iconSearch: window.iconSearch
            indent: 30
            previewShadeSliderMix: filesPane.uPanelTintMix
            panelColor: theme.panelAlt
            panelBorderColor: theme.pillBorder
            accentPrimary: theme.accentPrimary
            accentPrimaryText: theme.accentPrimaryText
            pill: theme.pill
            pillBorder: theme.pillBorder
            pathButtonFill: theme.folderPathTint
            pathButtonBorder: theme.folderPathBorder
            folderButtonFill: theme.folderULineTint
            folderButtonBorder: theme.folderULineBorder
            smallButtonBg: theme.smallButtonBg
            smallButtonBorder: theme.smallButtonBorder
            smallButtonActiveBg: theme.smallButtonActiveBg
            smallButtonActiveBorder: theme.smallButtonActiveBorder
            smallButtonText: theme.smallButtonText
            accentSecondary: theme.accentSecondary
            accentSecondaryBorder: theme.accentSecondaryBorder
            text: theme.text
            textSoft: theme.textSoft
            textMuted: theme.textMuted
            card: theme.card
            hostBackend: backend
            hostProjectIconForPath: projectIconForPath
            hostHasBackend: hasBackend
            pathSegmentMyosTest: pathSegmentMyosTest
            pathSegmentMyOS: pathSegmentMyOS
            searchActive: level2SearchActive
            searchText: level2SearchText
            onToggleMode: level2VerticalView = !level2VerticalView
            onToggleSearch: level2SearchActive = !level2SearchActive
            onSearchTextChanged: level2SearchText = templatesBrowser.searchText
            onSearchTextEdited: function(value) {
                level2SearchText = value
                updateStandardFolders()
            }
            onStyleChanged: function(style) { level2ButtonStyle = style }
        onLensFrameClosed: takeOffLens()
        onToggleEmbryos: {
            window.templatesShowEmbryos = !window.templatesShowEmbryos
            standardFolders = listTemplates(templatesListingPath())
            updateStandardFolders()
        }
            onPathSegmentActivated: function(index) {
                show_FilesPanel()
                var currentPath = templatesListingPath()
                var nextPath = currentPath
                if (templatesBrowser.fullPathForDisplayIndex) {
                    nextPath = templatesBrowser.fullPathForDisplayIndex(index)
                } else {
                    var parts = currentPath.split("/").filter(function(p){ return p.length > 0 })
                    nextPath = "/" + parts.slice(0, index + 1).join("/")
                }
                if (window.lensOn) {
                    // A flatter lens; the project itself is the way to the shelf (E4).
                    if (nextPath !== String(window.lensState.project_dir || "")) {
                        lensRequest("look_at", { "path": nextPath })
                    }
                } else {
                    standardPath = nextPath
                }
            }
            onPathSelected: function(path) {
                show_FilesPanel()
                if (window.lensOn) {
                    lensRequest("look_at", { "path": String(path || "") })
                } else {
                    standardPath = path
                }
            }
            onFolderActivated: function(name) {
                show_FilesPanel()
                var nextPath = String(name || templatesListingPath())
                if (window.lensOn) {
                    lensRequest("look_at", { "path": nextPath })
                } else {
                    standardPath = nextPath
                }
            }
            onNavigationRequested: function(path, gesture, source, meta) {
                var target = String(path || "").trim()
                if (target.length === 0) return
                if (window.lensOn) {
                    // The lens gets sharper, or another department's lens is put on (A3).
                    lensRequest("look_at", { "path": target })
                } else if (gesture === "single") {
                    applyFolderActivation(target)
                } else if (isMyosFolder(meta)) {
                    lensRequest("look_at", { "path": target })  // put on the lens (A3)
                } else {
                    commitCTD(target)
                }
            }
            onNavigateToPathRequested: function(path) {
                // CWD/CTD handled by onNavigationRequested
            }
            // Edge-Dock: do not call show_FilesPanel() here (double-click path). CWD/CTD handled by onNavigationRequested.
            onFolderDoubleActivated: function(path, folderMeta) {
                // Legacy signal; navigation handled by onNavigationRequested
            }
            // Edge-Dock: do not call show_FilesPanel() here (hover/preview path).
            onFolderPreviewed: function(path) { handlePreviewPath(templatesBrowser, path) }
            onMoveEntryRequested: function(sourcePath, targetDir) { handleMoveEntry(templatesBrowser, sourcePath, targetDir) }
            onCreateFolderRequested: function(basePath) { handleCreateFolder(templatesBrowser, basePath) }
        }

        Component {
            // M's tools at the top of the CWD dropdown: what would hide behind a menu, as
            // buttons (Scope/CwdTools.qml).
            id: cwdToolsComponent
            CwdTools {
                buttonSize: window.compactButtonHeight
                baseFont: window.baseFont
                pill: theme.pill
                pillBorder: theme.pillBorder
                pillActive: theme.smallButtonActiveBg
                textColor: theme.text
                iconSearch: window.iconSearch
                clipboardHasItems: window.clipboardHasItems
                darkTheme: window.darkTheme
                language: window.uiLanguage
                hiddenShown: window.projectsShowHiddenFolders
                onOpenClipboard: {
                    projectsBrowser.closeCwdHoverPanels("tools-clipboard")
                    window.openClipboard()
                }
                onClipboardDrop: function(drop) {
                    var payload = projectsBrowser.dropPayloadText(drop)
                    if (!payload) return
                    window.dropToClipboard(payload)
                    drop.acceptProposedAction()
                }
                onOpenSearch: {
                    projectsBrowser.closeCwdHoverPanels("tools-search")
                    window.level2SearchActive = true
                }
                onSwitchTheme: window.darkTheme = !window.darkTheme
                onSwitchLanguage: window.toggleUiLanguage()
                onToggleHidden: {
                    window.projectsShowHiddenFolders = !window.projectsShowHiddenFolders
                    window.updateSubProjects()
                    window.updateFiles()
                }
                onOpenSetup: {
                    projectsBrowser.closeCwdHoverPanels("tools-setup")
                    window.flipSetup(true)
                }
            }
        }

        SetupPage {
            // The back of Scope: shown from the quarter turn on (flipSetup).
            id: setupPage
            parent: window.contentItem
            anchors.fill: parent
            z: 100000
            visible: window.setupShown
            settings: window.hasBackend() ? backend : null
            darkTheme: window.darkTheme
            language: window.uiLanguage
            baseFont: window.baseFont
            onSwitchTheme: window.darkTheme = !window.darkTheme
            onSwitchLanguage: window.toggleUiLanguage()
            onFlipBack: window.flipSetup(false)
            projectsRowShown: window.projectsBrowserVisible
            templatesRowShown: window.templatesBrowserVisible
            onToggleProjectsRow: {
                window.projectsBrowserVisible = !window.projectsBrowserVisible
                if (window.hasBackend()) backend.setSetting("Scope/projectsRow", window.projectsBrowserVisible)
            }
            onToggleTemplatesRow: {
                window.templatesBrowserVisible = !window.templatesBrowserVisible
                if (window.hasBackend()) backend.setSetting("Scope/templatesRow", window.templatesBrowserVisible)
            }
        }

        FolderBrowser {  // ProjectsBrowser
            id: projectsBrowser
            debugName: "ProjectsBrowser"
            parent: floatingPool
            z: 8
            markCwd: true  // its line ends at the CWD: it glows (FolderItem.cwdMark)
            cwdHoverTools: window.minimalView ? cwdToolsComponent : null
            cwdGlow: window.darkTheme
            visible: projectsBrowserVisible
            maxParents: 10
            path: cwp
            pathDisplayPrefix: cwp
            pathSegmentMyosTest: pathSegmentMyosTest
            pathSegmentMyOS: pathSegmentMyOS
            folders: subProjects
            childrenProvider: function(targetPath, options) { return listRightFolders(targetPath, options) }
            showEmbryos: window.projectsShowEmbryos
            showHiddenFolders: window.projectsShowHiddenFolders
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            tintPathAsProject: false
            cwdOpacity: 1.0
            pathProjectOpacity: 0.7
            folderProjectOpacity: 0.55
            embryoOpacity: window.embryoOpacity
            embryoBadgeOpacity: window.embryoBadgeOpacity
            debugLayout: false
            allowDrags: true
            allowDrops: true
            verticalView: verticalProjectView && !window.minimalView
            usePathBar: !window.minimalView
            foldersShown: !window.minimalView
            narrowButtons: window.minimalView
            cascadeTopPath: window.minimalView ? window.projectsRootPath : ""
            showStyleToggle: !window.minimalView
            showEmbryoToggle: !window.minimalView
            buttonStyle: folderItemStyle
            allowLargeIcons: true
            showModeToggle: !window.minimalView
            showSearchToggle: !window.minimalView
            showClipboardButton: !window.minimalView
            showThemeToggle: false
            showCreateFolderButton: true
            clipboardHasItems: window.clipboardHasItems
            baseFont: window.baseFont
            compactButtonHeight: window.compactButtonHeight
            largeButtonHeight: window.largeButtonHeight
            largeButtonPadding: Math.round(window.largeButtonPadding * 0.5)
            iconSizeSmall: window.iconSizeSmall
            iconSizeLarge: window.iconSizeLarge
            iconFolder: window.iconFolder
            iconFolderOff: window.iconFolderOff
            iconSearch: window.iconSearch
            previewExcludedFromContentHeight: window.edgeDockEnabled && (window.edgeDockState !== "expandedWithFiles")
            indent: 30
            previewShadeSliderMix: filesPane.uPanelTintMix
            panelColor: theme.panel
            panelBorderColor: theme.pillBorder
            accentPrimary: theme.accentPrimary
            accentPrimaryText: theme.accentPrimaryText
            pill: theme.pill
            pillBorder: theme.pillBorder
            pathButtonFill: theme.folderPathTint
            pathButtonBorder: theme.folderPathBorder
            folderButtonFill: theme.folderULineTint
            folderButtonBorder: theme.folderULineBorder
            smallButtonBg: theme.smallButtonBg
            smallButtonBorder: theme.smallButtonBorder
            smallButtonActiveBg: theme.smallButtonActiveBg
            smallButtonActiveBorder: theme.smallButtonActiveBorder
            smallButtonText: theme.smallButtonText
            accentSecondary: theme.accentSecondary
            accentSecondaryBorder: theme.accentSecondaryBorder
            text: theme.text
            textSoft: theme.textSoft
            textMuted: theme.textMuted
            card: theme.card
            hostBackend: backend
            hostProjectIconForPath: projectIconForPath
            hostHasBackend: hasBackend
            allowRename: true
            renameTargetPath: renameTargetPath
            renameDraft: renameDraft
            searchActive: window.searchActive
            searchText: window.searchText
            onToggleMode: verticalProjectView = !verticalProjectView
            onStyleChanged: function(style) { folderItemStyle = style }
        onToggleEmbryos: {
            window.projectsShowEmbryos = !window.projectsShowEmbryos
            updateSubProjects()
        }
            onToggleShowHiddenFolders: {
                window.projectsShowHiddenFolders = !window.projectsShowHiddenFolders
                updateSubProjects()
                updateFiles()
            }
            onToggleSearch: window.searchActive = !window.searchActive
            onSearchTextChanged: {
                window.searchText = projectsBrowser.searchText
                window.updateSubProjects()
            }
            onSearchTextEdited: function(value) {
                window.searchText = value
                window.updateSubProjects()
            }
            onNavigationRequested: function(path, gesture, source, meta) {
                var targetPath = String(path || "").trim().indexOf("/") === 0 ? String(path || "").trim() : (cwp + "/" + String(path || "").trim())
                if (targetPath.length === 0) return
                if (gesture === "single") {
                    // Browsing (the menus open): the FilesPanel shows the folder, a lens stays on.
                    show_FilesPanel()
                    applyFolderActivation(targetPath)
                    clearSearchAfterNavigate()
                } else {
                    if (projectsBrowser && typeof projectsBrowser.resetPreview === "function") {
                        projectsBrowser.resetPreview()
                        projectsBrowser.scheduleContentHeightUpdate()
                    }
                    clearSearchAfterNavigate()
                    // With a lens on this row is left of its frame (A3): the lens goes along,
                    // keeping its depth - into the project there (a folder inside one: its
                    // project), or onto the shelf of a folder of projects. It stays on until
                    // taken off (✕), also outside the projects.
                    if (window.lensOn) {
                        lensRequest("move_to", { "path": targetPath })
                        setCwp(targetPath, "lens.moveTo")
                        return
                    }
                    setCwp(targetPath, "projectsBrowser.navigationRequested")
                    commitCTD(targetPath)
                }
            }
            onNavigateToPathRequested: function(path) {
                // CWD/CTD handled by onNavigationRequested
            }
            onFolderActivated: function(name) {
                show_FilesPanel()
            }
            // Edge-Dock: do not call show_FilesPanel() here (double-click path). CWD/CTD handled by onNavigationRequested.
            onFolderDoubleActivated: function(name, folderMeta) {
                // Legacy signal; navigation handled by onNavigationRequested
            }
            // Edge-Dock: do not call show_FilesPanel() here (hover/preview path).
            onFolderPreviewed: function(path) { handlePreviewPath(projectsBrowser, path) }
            onRenameRequested: function(path) { beginRename(path) }
            onContextMenuRequested: function(fullPath, menuX, menuY, ctrlPressed) {
                folderContextPath = fullPath
                var pt = projectsBrowser.mapToItem(floatingPool.parent, menuX, menuY)
                folderContextMenu.popup(pt.x, pt.y)
            }
            onRenameTextEdited: function(text) {
                renameDraft = text
                if (projectsBrowser) projectsBrowser.renameDraft = text
            }
            onRenameAccepted: function(newName) {
                renameDraft = newName
                if (projectsBrowser) projectsBrowser.renameDraft = newName
                commitRename(newName)
            }
            onRenameCanceled: cancelRename()
            onMoveEntryRequested: function(sourcePath, targetDir) { handleMoveEntry(projectsBrowser, sourcePath, targetDir) }
            onCreateFolderRequested: function(basePath) { handleCreateFolder(projectsBrowser, basePath) }
        }

        Connections {
            target: templatesBrowser
            function onClipboardRequested() { openClipboard() }
            function onClipboardDropRequested(payload) { dropToClipboard(payload) }
        }
        Connections {
            target: projectsBrowser
            function onClipboardRequested() { openClipboard() }
            function onClipboardDropRequested(payload) { dropToClipboard(payload) }
        }

        FilesPanel {  // FilesPanel
            id: filesPane
            parent: floatingPool
            z: 1
            visible: filesPaneVisible
            itemsModel: filesModel
            currentPath: window.currentFilesPath()
            // Entering the panel shows the highlighted folder at the latest, so content and drop target match.
            HoverHandler {
                onHoveredChanged: if (hovered) window.flushFilesPreview()
            }
            baseFont: window.baseFont
            text: theme.text
            textMuted: theme.textMuted
            panelAlt: theme.panelAlt
            pillBorder: theme.pillBorder
            backgroundColor: theme.filesPaneBackground
            templatesBrowserWidth: templatesBrowser.implicitWidth
            projectsBrowserWidth: projectsBrowser.implicitWidth
            iconFolder: window.iconFolder
            iconFolderOff: window.iconFolderOff
            iconFolderXray: Qt.resolvedUrl("Theme/icons/xray.svg")
            embryoOpacity: window.embryoOpacity
            iconFile: window.iconFile
            iconGear: window.iconGear
            itemStyle: window.filesItemStyle
            listColumns: window.filesListColumns
            sortKey: window.filesSortKey
            sortAscending: window.filesSortAscending
            onSortRequested: function(key) { window.setFilesSort(key) }
            onListColumnsChangeRequested: function(columns) {
                window.filesListColumns = columns
                if (hasBackend() && typeof backend.setFilesListColumns === "function") {
                    backend.setFilesListColumns(columns)
                }
            }
            onItemStyleToggleRequested: {
                window.filesItemStyle = window.filesItemStyle === "largeIcon" ? "smallIcon" : "largeIcon"
                if (hasBackend() && typeof backend.setFilesViewStyle === "function") {
                    backend.setFilesViewStyle(window.filesItemStyle)
                }
            }
            compactButtonHeight: window.compactButtonHeight
            largeButtonHeight: window.largeButtonHeight
            largeButtonPadding: window.largeButtonPadding
            iconSizeSmall: window.iconSizeSmall
            iconSizeLarge: window.iconSizeLarge
            itemFillColor: "transparent"
            itemBorderColor: theme.pillBorder
            allowDrags: true
            smallButtonBg: theme.smallButtonBg
            smallButtonBorder: theme.smallButtonBorder
            smallButtonActiveBg: theme.smallButtonActiveBg
            smallButtonActiveBorder: theme.smallButtonActiveBorder
            smallButtonText: theme.smallButtonText
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            pButtonActiveColor: (window.defaultProjectTint && String(window.defaultProjectTint).length > 0)
                ? window.defaultProjectTint
                : "#7b5bd6"
            uPanelTintColor: window.filesPanelTintColor
            uPanelTintMix: 0.65
            projectTintOpacity: 0.75
            projectCreateTarget: window.projectCreateTarget
            projectRemoveTarget: window.projectRemoveTarget
            onRemoveProject: window.removeProjectAt(window.projectRemoveTarget, false)
            hasMyosDirInCwp: window.hasMyosInCwp
            showLeaveMyosButton: window.isInsideMyosFolder
            availableTags: window.availableTags
            folderTags: window.folderTags
            subfolderTags: window.subfolderTags
            fileTags: window.fileTags
            folderTagColors: window.folderTagColors
            subfolderTagColors: window.subfolderTagColors
            fileTagColors: window.fileTagColors
            tagSuggestions: window.tagSuggestions
            selectedPaths: window.selectedEntryPaths
            selectedTags: window.selectedTags
            tagSource: window.tagFilterSource
            uiLanguage: window.uiLanguage
            isTagIndexing: window.tagsIndexing
            aclPanelVisible: !!window.aclSummary.hasAcls && (window.aclSummary.principals || []).length > 0
            aclPrincipals: window.aclSummary.principals || []
            aclEntryCount: Object.keys(window.aclSummary.access || ({})).length
            selectedAclPrincipal: window.selectedAclPrincipal
            onAclPrincipalToggled: function(id) { window.toggleAclPrincipal(id) }
            aclCanEdit: !!window.aclSummary.canEdit
            trashCount: window.trashCount
            onTrashRequested: trashDialog.openFor(window.currentFilesPath())
            onAclRoleEditRequested: function(roleKey, roleName, rights) {
                aclRoleDialog.openFor(window.currentFilesPath(), roleKey, roleName, rights)
            }
            onAclPersonEditRequested: function(userKey) {
                aclPersonDialog.openFor(window.currentFilesPath(), userKey)
            }
            onAclPersonAddRequested: aclPersonDialog.openForNew(window.currentFilesPath())
            aclListed: window.aclSummary.listed !== false
            aclWhoChoices: window.aclSummary.whoChoices || []
            onAclIdentityChosen: function(name) {
                if (window.hasBackend()) backend.aclClaimIdentity(window.currentFilesPath(), name)
                window.requestAclSummary()
            }
            folderSizeBytes: window.currentFolderSizeBytes
            folderSizeComplete: window.currentFolderSizeComplete
            folderSizesActive: window.folderSizesActive
            folderSizesMeasuring: window.folderSizesMeasuring
            onFolderSizesRequested: window.activateFolderSizes()
            onRequestMore: appendNextChunk()
            onFilterChanged: {
                filterEntries()
                recomputeTagBuckets()  // subfolder tags only while folders are shown
            }
            onItemActivated: function(path, ctrlPressed, shiftPressed) {
                toggleEntrySelection(path, ctrlPressed, shiftPressed)
            }
            onSelectionBoxApplied: function(paths, additive) { applySelectionBox(paths, additive) }
            onEmptyAreaClicked: {
                commitCTD(cwp)
                if (projectsBrowser && typeof projectsBrowser.resetPreview === "function") {
                    projectsBrowser.resetPreview()
                    projectsBrowser.scheduleContentHeightUpdate()
                }
                if (templatesBrowser && typeof templatesBrowser.resetPreview === "function") {
                    templatesBrowser.resetPreview()
                    templatesBrowser.scheduleContentHeightUpdate()
                }
            }
            onMoveEntriesRequested: function(payload, targetDir) {
                var target = filesCreateTarget(targetDir)
                if (target.length > 0) moveEntry(payload, target)
            }
            onTagToggled: function(tag) { toggleTagSelection(tag) }
            onAddFolderTagRequested: function(tag) { addFolderTag(tag) }
            onRemoveFolderTagRequested: function(tag) { removeFolderTag(tag) }
            onFolderTagColorRequested: function(tag, color) { setFolderTagColor(tag, color) }
            onRequestTagSourceChange: function(source) { tagFilterSource = source }
            onCreateNoteRequested: createNewNote()
            onCreateFolderRequested: function(basePath) {
                var targetBase = String(basePath || "").trim()
                if (targetBase.length === 0) {
                    targetBase = currentFilesPath()
                }
                targetBase = filesCreateTarget(targetBase)
                if (targetBase.length > 0) requestCreateFolderAt(targetBase)
            }
            onMoveSelectedIntoNewFolderRequested: function(paths) {
                promptMoveSelectedIntoNewFolder(paths)
            }
            onRenameRequested: function(paths) { requestRenameEntries(paths) }
            onDeleteRequested: function(paths) { requestDeleteEntries(paths) }
            onSelectAllRequested: selectAllVisibleEntries()
            onNavigationRequested: function(path, gesture, source) {
                if (gesture !== "double" || source !== "filesPanel") return
                var targetPath = String(path || "").trim()
                if (targetPath.length === 0) return
                show_FilesPanel()
                // With a lens on: a folder of the department makes the lens sharper; any
                // other (the fallback shows the project's folders) takes it off to go there.
                if (window.lensOn) {
                    if (lensRequest("look_at", { "path": targetPath })) return
                    lensRequest("take_off")
                }
                setCwp(targetPath, "filesPane.navigationRequested")
                commitCTD(targetPath)
                clearSearchAfterNavigate()
            }
            onFolderActivated: function(name) {
                show_FilesPanel()
            }
            onFileActivated: function(name) {
                openFileEntry(name)
            }
            onOpenRequested: function(path) {
                openFilePath(path)
            }
            onOpenWithRequested: function(path) {
                requestOpenWith(path)
            }
            onOpenMyosFolder: {
                var base = cwp.endsWith("/") ? cwp.slice(0, -1) : cwp
                var targetPath = base + "/" + myosDirName
                commitCTD(targetPath)
                clearSearchAfterNavigate()
            }
            onCreateMyosAndEnter: {
                if (!hasBackend() || typeof backend.createFolder !== "function") return
                var base = cwp.endsWith("/") ? cwp.slice(0, -1) : cwp
                var created = backend.createFolder(base, myosDirName)
                if (created && created.length > 0) {
                    commitCTD(created)
                    clearSearchAfterNavigate()
                    updateFiles()
                }
            }
            xrayActive: window.xrayEnabled
            onXrayClicked: {
                window.xrayEnabled = !window.xrayEnabled
                if (hasBackend() && typeof backend.setFilesXray === "function") backend.setFilesXray(window.xrayEnabled)
                window.applyXrayView()
            }
            onVisibleCapacityChanged: if (window.xrayEnabled) xrayLayoutTimer.restart()
            onShowFoldersChanged: if (window.xrayEnabled) window.applyXrayView()
            onLeaveMyosFolder: {
                var parent = parentOfPath(currentFilesPath())
                commitCTD(parent)
                clearSearchAfterNavigate()
            }
            onCreateProject: {
                var target = window.projectCreateTarget
                if (target.length > 0 && hasBackend() && typeof backend.createProject === "function") {
                    var shownFolder = target === currentFilesPath()
                    var ok = backend.createProject(target)
                    if (ok) {
                        // The folder shown became a project: be in it, like after a double click.
                        if (shownFolder) {
                            setCwp(target, "filesPane.createProject")
                            commitCTD(target)
                        }
                        updateSubProjects()
                        if (typeof backend.setContext === "function") {
                            backend.setContext(cwp)
                        }
                        updateFiles()
                        updateTemplates()
                        var listingPathAfterCreate = templatesListingPath()
                        standardFolders = listTemplates(listingPathAfterCreate)
                        updateStandardFolders()
                    }
                }
            }
        }
    }
}

