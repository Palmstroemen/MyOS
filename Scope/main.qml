import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.folderlistmodel 2.15
import "Theme/tag_chips.js" as TagChips
import "js/PathUtils.js" as PathUtils
import "./Dialogs" 1.0

ApplicationWindow {
    id: window
    width: 1400
    height: 900
    visible: true
    title: "Scope - MyOS GUI Stub"

    property int baseFont: Qt.application.font.pixelSize
    property bool darkTheme: true
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
    property var searchInputRef: null
    property string standardButtonStyle: "text"
    property string userButtonStyle: "text"
    property string uiLanguage: "de"
    property string userPath: "/Eigene"
    property string level2ButtonStyle: "smallIcon"
    // Browser visibility
    property bool projectsBrowserVisible: true
    property bool templatesBrowserVisible: true
    property bool filesPanelHalfTransparent: false
    property bool schmalMode: false
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
    readonly property color filesPanelTintColor: hasProjectInCwp && projectsBrowser ? projectsBrowser.currentPathFillColor : theme.folderPathTint

    // --- Pfadkonzepte CWD / CWP / CTD (Begriffe: siehe Vision/GUI Filebrowser.md, Abschnitt Begriffe) ---
    // CWD (Current Working Directory): Im Scope durch die Property cwp repräsentiert; der „Arbeitspfad“
    //     ist hier das aktuelle Projektverzeichnis.
    // CWP (Current Working Project): Im Code die Property cwp (Pfad zum aktuellen Projektordner, z. B. /Projekte/Haus/Dach).
    // CTD (Current Target Directory): Zielordner für Datei-Operationen (z. B. Verschieben, Vorschau).
    //     Properties: previewCTDPath (Vorschau beim Navigieren), committedCTDPath (bestätigter Zielpfad).
    //     Funktionen: previewCTD(path), commitCTD(path). Welcher Pfad für die Dateiliste gilt: currentFilesPath()
    //     (Fallback auf cwp, wenn kein CTD gesetzt).

    property string cwp: "/Projekte/Haus/Dach"
    property var subProjects: []
    property string templatesRootPath: ""
    property string standardPath: "/"
    property string templatesPerspectivePath: "/Templates"
    property var templatesPerspectiveCpdByDisplayPath: ({})
    property string templatesCtdPath: ""
    property string previewCTDPath: ""
    property string committedCTDPath: ""
    property string clipboardPath: ""
    property bool clipboardHasItems: false
    // Controls whether TemplatesBrowser acts as perspective selector (CPD semantics)
    // or as plain embryo browser (CTD semantics).
    property bool templatesUsePerspective: true
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
    property bool hasProjectInCwp: false
    property string tagFilterSource: "visible" // legacy
    property var availableTags: []
    property var folderTags: []
    property var fileTags: []
    property var folderTagColors: ({})
    property var fileTagColors: ({})
    property var tagSuggestions: []
    property var selectedTags: []
    property bool tagsIndexing: false
    property int currentFolderSizeBytes: 0
    property string tagMatchMode: "or" // or | and
    property bool projectsShowEmbryos: false
    property bool projectsShowHiddenFolders: false
    property bool templatesShowEmbryos: true
    property var pendingMoveSources: []
    property string pendingMoveTargetDir: ""
    property string pendingMoveMessage: ""
    property string moveReportMessage: ""
    property var pendingFolderBatchSources: []
    property string pendingFolderBatchName: qsTr("Neuer Ordner")
    property string pendingCreateFolderTargetPath: ""
    property string pendingCreateFolderName: qsTr("Neuer Ordner")
    property string pendingRenamePath: ""
    property string pendingRenameName: ""
    property var pendingDeletePaths: []
    property var pendingBatchRenamePaths: []
    property string pendingBatchReplaceFrom: ""
    property string pendingBatchReplaceTo: ""
    property string pendingOpenWithPath: ""
    property string pendingOpenWithCommand: "xdg-open"
    property var openWithQuickCommands: ["xdg-open", "code", "libreoffice"]
    property var pendingConfigPrompt: ({ pending: false, options: [] })
    property string pendingConfigPromptContext: ""
    property string pendingConfigPromptName: "Desk.md"
    property var availableFilters: []
    property var activeFilter: ({ active: false, name: "", mode: "auto", path: "", chain: [] })
    property var perspectiveState: ({ active: false, cpd: "", projectRoot: "", cwdReal: "" })
    property bool perspectiveModeEnabled: false
    property string lastSyncedPerspectiveCpd: ""
    property bool lastSyncedPerspectiveActive: false
    property string manualFilterPath: ""
    property string filterSaveSourcePath: ""
    property var filterSaveTargets: []
    property string pendingFilterNewName: ""
    property string selectionAnchorPath: ""
    property int maxVerticalParents: 4
    property int verticalParentSpacing: 6
    ListModel {
        id: filesModel
        dynamicRoles: true
    }


    QtObject {
        id: demoData
        property var tree: ({
            "Projekte": {
                "Haus": {
                    "Dach": {
                        "Fundraising": {},
                        "Webseite": {},
                        "Angebote": {}
                    },
                    "Ausmalen": {}
                },
                "Garten": {}
            }
        })

        function getNode(path) {
            var parts = path.split("/").filter(function(p){ return p.length > 0 })
            var node = tree
            for (var i = 0; i < parts.length; i++) {
                if (!node[parts[i]]) {
                    return null
                }
                node = node[parts[i]]
            }
            return node
        }

        function childrenOf(path) {
            var node = getNode(path)
            if (!node) return []
            return Object.keys(node)
        }

        function addChild(path, name) {
            var node = getNode(path)
            if (!node) return false
            if (node[name]) return false
            node[name] = {}
            return true
        }

        function collectPathsFromNode(node, prefix, out) {
            var keys = Object.keys(node)
            for (var i = 0; i < keys.length; i++) {
                var key = keys[i]
                var next = prefix ? (prefix + "/" + key) : ("/" + key)
                out.push(next)
                collectPathsFromNode(node[key], next, out)
            }
        }

        function collectFromPath(path) {
            var node = getNode(path)
            if (!node) return []
            var out = []
            collectPathsFromNode(node, path, out)
            return out
        }

        function collectAll() {
            var out = []
            collectPathsFromNode(tree, "", out)
            return out
        }

        function renamePath(path, newName) {
            var parts = path.split("/").filter(function(p){ return p.length > 0 })
            if (parts.length === 0) return false
            var parentParts = parts.slice(0, parts.length - 1)
            var oldName = parts[parts.length - 1]
            var parentPath = "/" + parentParts.join("/")
            var parentNode = parentParts.length === 0 ? tree : getNode(parentPath)
            if (!parentNode) return false
            if (!parentNode[oldName]) return false
            if (parentNode[newName]) return false
            parentNode[newName] = parentNode[oldName]
            delete parentNode[oldName]
            return true
        }
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

    function previewCTD(path) {
        previewCTDPath = String(path || "").trim()
    }

    function commitCTD(path) {
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
        filesPanelHalfTransparent = false
    }
    function hide_FilesPanel() {
        filesPanelHalfTransparent = true
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

    function refreshPerspectiveState() {
        if (!hasBackend() || typeof backend.perspectiveState !== "function") {
            perspectiveState = ({ active: false, cpd: "", projectRoot: "", cwdReal: "" })
            perspectiveModeEnabled = false
            lastSyncedPerspectiveCpd = ""
            lastSyncedPerspectiveActive = false
            return
        }
        var next = backend.perspectiveState() || ({ active: false, cpd: "", projectRoot: "", cwdReal: "" })
        var nextActive = !!next.active
        var nextCpd = String(next.cpd || "")
        var stateChanged = (nextActive !== lastSyncedPerspectiveActive) || (nextCpd !== lastSyncedPerspectiveCpd)
        perspectiveState = next
        perspectiveModeEnabled = nextActive
        var desiredTemplatesPath = nextActive
            ? templatesDisplayPathFromPerspectiveCpd(nextCpd)
            : templatesDisplayPathFromPerspectiveCpd("/Templates")
        var displayChanged = desiredTemplatesPath !== String(templatesPerspectivePath || "")
        if (displayChanged) {
            templatesPerspectivePath = desiredTemplatesPath
        }
        if (stateChanged || (templatesUsePerspective && displayChanged)) {
            lastSyncedPerspectiveActive = nextActive
            lastSyncedPerspectiveCpd = nextCpd
            var listingPath = templatesPerspectiveActive() ? templatesPerspectivePath : standardPath
            standardFolders = listTemplates(listingPath)
            updateStandardFolders()
        }
    }

    function templatesPerspectiveActive() {
        return !!templatesUsePerspective && !!perspectiveModeEnabled
    }

    function templatesListingPath() {
        return templatesPerspectiveActive() ? templatesPerspectivePath : standardPath
    }

    function parsePerspectiveCpd(cpd) {
        var raw = String(cpd || "").trim()
        var parts = raw.split("/").filter(function(p) { return p.length > 0 })
        var idx = -1
        for (var i = 0; i < parts.length; i++) {
            if (parts[i] === "Projekte") {
                idx = i
                break
            }
        }
        if (idx < 0 || idx + 1 >= parts.length) {
            return { valid: false, templateParts: [], projectName: "", tailParts: [] }
        }
        return {
            valid: true,
            templateParts: parts.slice(0, idx),
            projectName: String(parts[idx + 1] || ""),
            tailParts: parts.slice(idx + 2)
        }
    }

    function buildPerspectiveCpd(templateParts, projectName, tailParts) {
        var out = []
        for (var i = 0; i < (templateParts || []).length; i++) {
            out.push(String(templateParts[i] || ""))
        }
        out.push("Projekte")
        out.push(String(projectName || ""))
        for (var j = 0; j < (tailParts || []).length; j++) {
            out.push(String(tailParts[j] || ""))
        }
        return "/" + out.filter(function(p) { return p.length > 0 }).join("/")
    }

    function resolveProjectRootPath() {
        if (hasBackend() && typeof backend.getProjectRoot === "function") {
            var root = String(backend.getProjectRoot() || "")
            if (root.length > 0) {
                return PathUtils.trimTrailingSlash(root)
            }
        }
        var perspectiveRoot = String((perspectiveState && perspectiveState.projectRoot) ? perspectiveState.projectRoot : "")
        return PathUtils.trimTrailingSlash(perspectiveRoot)
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

    function projectNameFromCwp() {
        var root = resolveProjectRootPath()
        var prefix = root.length > 0 ? (PathUtils.trimTrailingSlash(root) + "/") : ""
        if (prefix.length > 0 && String(cwp || "").indexOf(prefix) === 0) {
            var rel = String(cwp || "").slice(prefix.length)
            var first = rel.split("/").filter(function(p) { return p.length > 0 })[0]
            if (first && first.length > 0) {
                return first
            }
        }
        var parsed = parsePerspectiveCpd(String((perspectiveState && perspectiveState.cpd) ? perspectiveState.cpd : ""))
        return parsed.valid ? String(parsed.projectName || "") : ""
    }

    function templatePartsFromTemplatesPath(path) {
        var root = PathUtils.trimTrailingSlash(templatesRootPath.length > 0 ? templatesRootPath : resolveTemplatesRootPath())
        var target = PathUtils.trimTrailingSlash(path)
        if (root.length === 0 || target.length === 0) return []
        if (target === root) return []
        if (target.indexOf(root + "/") !== 0) return []
        return target.slice(root.length + 1).split("/").filter(function(p) { return p.length > 0 })
    }

    function perspectiveCpdFromTemplatePath(path) {
        var raw = String(path || "").trim()
        if (raw === "/Templates" || raw === "/Templates/") {
            return "/Templates"
        }
        if (templatesPerspectiveCpdByDisplayPath && templatesPerspectiveCpdByDisplayPath[raw]) {
            return String(templatesPerspectiveCpdByDisplayPath[raw] || "")
        }
        var templateParts = raw.indexOf("/Templates/") === 0
            ? raw.slice("/Templates/".length).split("/").filter(function(p) { return p.length > 0 })
            : templatePartsFromTemplatesPath(path)
        var projectName = projectNameFromCwp()
        if (projectName.length === 0) return ""
        if (templateParts.length === 0) {
            return "/Templates"
        }
        var parsedState = parsePerspectiveCpd(String((perspectiveState && perspectiveState.cpd) ? perspectiveState.cpd : ""))
        var hint = parsedState.valid && parsedState.templateParts.length > 0
            ? String(parsedState.templateParts[0] || "")
            : String((perspectiveState && perspectiveState.templateRoot) ? perspectiveState.templateRoot : "")
        return buildPerspectiveCpd(hint.length > 0 ? [hint] : [], projectName, templateParts)
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

    function shouldApplyPerspectiveForFolderType(folderMeta) {
        return folderTypeFromMeta(folderMeta) > 0
    }

    function templatesDisplayPathFromPerspectiveCpd(cpd) {
        var root = PathUtils.trimTrailingSlash(templatesRootPath.length > 0 ? templatesRootPath : resolveTemplatesRootPath())
        var parsed = parsePerspectiveCpd(cpd)
        if (!parsed.valid) {
            return root.length > 0 ? root : "/Templates"
        }
        var tail = parsed.templateParts.slice(1).concat(parsed.tailParts)
        if (root.length === 0) {
            return tail.length > 0 ? ("/Templates/" + tail.join("/")) : "/Templates"
        }
        return tail.length > 0 ? (root + "/" + tail.join("/")) : root
    }

    function resolveTemplateDisplayPathToReal(path) {
        var raw = String(path || "").trim()
        if (raw.length === 0) {
            return ""
        }
        if (!(raw === "/Templates" || raw === "/Templates/" || raw.indexOf("/Templates/") === 0)) {
            return raw
        }
        var root = PathUtils.trimTrailingSlash(templatesRootPath.length > 0 ? templatesRootPath : resolveTemplatesRootPath())
        if (root.length === 0) {
            return raw
        }
        if (raw === "/Templates" || raw === "/Templates/") {
            return root
        }
        return root + raw.slice("/Templates".length)
    }

    function disablePerspectiveMode() {
        if (!hasBackend() || typeof backend.perspectiveSetCpd !== "function") {
            return false
        }
        backend.perspectiveSetCpd("/Templates")
        refreshPerspectiveState()
        templatesPerspectivePath = templatesDisplayPathFromPerspectiveCpd("/Templates")
        templatesPerspectiveCpdByDisplayPath = ({})
        var listingPath = templatesListingPath()
        standardFolders = listTemplates(listingPath)
        updateStandardFolders()
        return true
    }

    function ensurePerspectiveOpen() {
        // onCwpChanged already refreshes perspective state before updateTemplates().
        // Avoid a redundant second refresh on startup/path changes.
        if (!hasBackend() || typeof backend.perspectiveOpen !== "function") {
            return false
        }
        if (perspectiveState.active) {
            return true
        }
        var opened = backend.perspectiveOpen(cwp, "flipped") || ({ active: false })
        refreshPerspectiveState()
        return !!opened.active || !!perspectiveState.active
    }

    function ensurePerspectiveOpenForTemplates() {
        return ensurePerspectiveOpen()
    }

    function applyPerspectiveForRealPath(realPath) {
        var target = String(realPath || "").trim()
        if (target.length === 0) {
            return false
        }
        if (!ensurePerspectiveOpen()) {
            return false
        }
        if (!hasBackend() || typeof backend.perspectiveResolveReal !== "function") {
            return false
        }
        var resolved = backend.perspectiveResolveReal(target) || ({ ok: false })
        var nextCpd = String(resolved.cpd || "").trim()
        if (nextCpd.length === 0) {
            return false
        }
        return applyPerspectiveCpd(nextCpd)
    }

    function applyPerspectiveCpd(targetCpd) {
        var next = String(targetCpd || "").trim()
        if (next.length === 0 || next === "/") {
            return disablePerspectiveMode()
        }
        if (!hasBackend() || typeof backend.perspectiveSetCpd !== "function") {
            return false
        }
        var isTemplatesAnchor = (next === "/Templates" || next === "/Templates/")
        var parsed = parsePerspectiveCpd(next)
        if (!isTemplatesAnchor && !parsed.valid) {
            return false
        }
        var result = backend.perspectiveSetCpd(next) || ({ ok: false })
        refreshPerspectiveState()
        if (!result.ok) {
            return false
        }
        templatesPerspectivePath = templatesDisplayPathFromPerspectiveCpd(
            String((perspectiveState && perspectiveState.cpd) ? perspectiveState.cpd : next)
        )
        var listingPath = templatesListingPath()
        standardFolders = listTemplates(listingPath)
        updateStandardFolders()
        return true
    }

    function listPerspectiveTemplates(cpd, displayPath) {
        if (!hasBackend()) {
            return []
        }
        var rows = []
        if (typeof backend.perspectiveListTemplates === "function") {
            rows = backend.perspectiveListTemplates(cpd || "")
        } else if (typeof backend.perspectiveListDir === "function") {
            rows = backend.perspectiveListDir(cpd || "")
        } else {
            return []
        }
        var out = []
        var displayBase = String(displayPath || templatesPerspectivePath || "/Templates")
        var nextMap = {}
        if (templatesPerspectiveCpdByDisplayPath) {
            for (var key in templatesPerspectiveCpdByDisplayPath) {
                nextMap[key] = templatesPerspectiveCpdByDisplayPath[key]
            }
        }
        for (var i = 0; i < rows.length; i++) {
            var nodeType = String((rows[i] && rows[i].nodeType) ? rows[i].nodeType : "")
            if (nodeType === "dir") {
                var name = String((rows[i] && rows[i].name) ? rows[i].name : "")
                if (name.length === 0) {
                    continue
                }
                var base = displayBase.length > 1 && displayBase.endsWith("/")
                    ? displayBase.slice(0, -1)
                    : displayBase
                var displayPath = (base === "/" ? "" : base) + "/" + name
                nextMap[displayPath] = String((rows[i] && rows[i].cpd) ? rows[i].cpd : "")
                var rowFolderType = (rows[i] && rows[i].folderType !== undefined)
                    ? Number(rows[i].folderType)
                    : 2
                if (isNaN(rowFolderType)) {
                    rowFolderType = 2
                }
                out.push({
                    "name": name,
                    "isEmbryo": true,
                    "folderType": rowFolderType,
                    "color": String((rows[i] && rows[i].color) ? rows[i].color : ""),
                    "cpd": String((rows[i] && rows[i].cpd) ? rows[i].cpd : "")
                })
            }
        }
        templatesPerspectiveCpdByDisplayPath = nextMap
        return out
    }

    function _isMyOSFolderTrace(pathOrName) {
        var s = String(pathOrName || "")
        return s.indexOf("/" + pathSegmentMyosTest) >= 0 || s.indexOf("/" + pathSegmentMyOS + "/") >= 0 || s.endsWith("/" + pathSegmentMyOS) || s === pathSegmentMyOS
    }
    function listChildren(path) {
        if (hasBackend()) {
            var result = backend.listChildren(path, projectsShowEmbryos, projectsShowHiddenFolders)
            return result
        }
        if (path === cwp) {
            var dirs = []
            for (var i = 0; i < fsModel.count; i++) {
                var isDir = fsModel.get(i, "fileIsDir")
                if (isDir) {
                    dirs.push(fsModel.get(i, "fileName"))
                }
            }
            return dirs
        }
        return demoData.childrenOf(path)
    }

    function listTemplates(path) {
        if (templatesUsePerspective && perspectiveModeEnabled && hasBackend()) {
            var queryCpd = perspectiveCpdFromTemplatePath(path)
            return listPerspectiveTemplates(queryCpd, path)
        }
        if (hasBackend() && typeof backend.listTemplates === "function") {
            return backend.listTemplates(path, templatesShowEmbryos)
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

    function _openConfigPromptIfPending() {
        if (!hasBackend() || typeof backend.configPromptState !== "function") {
            return
        }
        var prompt = backend.configPromptState()
        if (!prompt || !prompt.pending) {
            return
        }
        pendingConfigPrompt = prompt
        pendingConfigPromptContext = String(prompt.contextPath || "")
        pendingConfigPromptName = String(prompt.configName || "Desk.md")
        configPromptDialog.open()
    }

    function toggleUiLanguage() {
        var next = uiLanguage === "de" ? "en" : "de"
        if (hasBackend() && typeof backend.setLanguage === "function") {
            backend.setLanguage(next)
            if (typeof backend.currentLanguage === "function") {
                uiLanguage = backend.currentLanguage()
                return
            }
        }
        uiLanguage = next
    }

    function _moveReasonText(code) {
        switch (String(code || "")) {
        case "target_not_directory":
            return qsTr("Ziel ist kein Ordner.")
        case "source_missing":
            return qsTr("Eintrag existiert nicht mehr.")
        case "target_inside_source":
            return qsTr("Ein Ordner kann nicht in sich selbst verschoben werden.")
        case "destination_exists":
            return qsTr("Am Ziel existiert bereits ein Eintrag mit diesem Namen.")
        case "move_failed":
            return qsTr("Verschieben fehlgeschlagen.")
        case "same_as_target":
            return qsTr("Eintrag ist bereits im Zielordner.")
        case "duplicate_source":
            return qsTr("Eintrag wurde mehrfach ausgewaehlt.")
        default:
            return qsTr("Vorgang uebersprungen.")
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
            var skipped = (batch && batch.skipped) ? batch.skipped : []
            var errors = (batch && batch.errors) ? batch.errors : []
            if (batch && batch.moved && batch.moved.length > 0) {
                selectedEntryPaths = []
                updateSubProjects()
                updateFiles()
                updateTemplates()
                var listingPath = templatesListingPath()
                standardFolders = listTemplates(listingPath)
                updateStandardFolders()
            }
            if (errors.length > 0 || skipped.length > 0) {
                var lines = []
                var movedCount = (batch && batch.moved) ? batch.moved.length : 0
                if (movedCount > 0) {
                    lines.push(qsTr("Verschoben: %1").arg(movedCount))
                }
                if (errors.length > 0) {
                    if (lines.length > 0) {
                        lines.push("")
                    }
                    lines.push(qsTr("Konnte nicht verschieben:"))
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
                    lines.push(qsTr("Uebersprungen:"))
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
            pendingMoveMessage = qsTr("Soll(en) %1 Ordner wirklich nach \"%2\" verschoben werden?")
                .arg(count)
                .arg(resolvedTarget)
            folderMoveConfirmDialog.open()
            return
        }
        if (sources.length === 1 && hasBackend() && typeof backend.previewSortTargetForMove === "function") {
            var preview = backend.previewSortTargetForMove(String(sources[0] || ""), resolvedTarget)
            if (preview && preview.ok && preview.target) {
                moveReportMessage = qsTr("Nach dem Verschieben wird einsortiert nach:\n%1").arg(String(preview.target))
                moveReportDialog.open()
            }
        }
        _performMove(sources, resolvedTarget)
    }

    function createNewNote() {
        if (!hasBackend() || typeof backend.createNote !== "function") {
            return
        }
        var targetDir = currentFilesPath()
        var createdPath = backend.createNote(targetDir, "New Note")
        if (!createdPath || createdPath.length === 0) {
            moveReportMessage = qsTr("Konnte in diesem Ordner keine Notiz erstellen.")
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
        pendingFolderBatchName = qsTr("Neuer Ordner")
        moveSelectedFoldersDialog.open()
    }

    function requestCreateFolderAt(targetPath) {
        var target = String(targetPath || "").trim()
        if (target.length === 0) {
            return
        }
        pendingCreateFolderTargetPath = target
        pendingCreateFolderName = qsTr("Neuer Ordner")
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
            moveReportMessage = qsTr("Sammelumbenennung funktioniert aktuell nur fuer Dateien.")
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
            moveReportMessage = qsTr("Virtuelle Embryo-Ordner koennen nicht geloescht werden.")
            moveReportDialog.open()
            return
        }
        cleaned = deletable
        if (embryoBlocked.length > 0) {
            moveReportMessage = qsTr("Embryo-Ordner wurden beim Loeschen uebersprungen: %1").arg(embryoBlocked.length)
            moveReportDialog.open()
        }
        if (cleaned.length <= 3) {
            performDeleteEntries(cleaned)
            return
        }
        pendingDeletePaths = cleaned
        deleteEntriesDialog.open()
    }

    function performDeleteEntries(paths) {
        var result = backend.deleteEntries(paths || [])
        var deleted = (result && result.deleted) ? result.deleted.length : 0
        var errors = (result && result.errors) ? result.errors.length : 0
        selectedEntryPaths = []
        updateFiles()
        if (errors > 0) {
            moveReportMessage = qsTr("Geloescht: %1 Datei(en)\nNicht geloescht: %2 Datei(en)")
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
        var demoItems = demoData.childrenOf(path).map(function(name){
            return { name: name, isDir: true }
        })
        for (var j = 0; j < files.length; j++) {
            demoItems.push({ name: files[j], isDir: false })
        }
        return demoItems
    }

    function applyEntries(entries) {
        fileItemsAll = entries || []
        filterEntries()
        Qt.callLater(function() { recomputeTagBuckets() })
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
        fileItemsRaw = filtered
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
        var nextFileTags = []
        var nextFolderTagColors = ({})
        var nextFileTagColors = ({})
        var nextProjectTags = []
        var nextFolderSize = currentFolderSizeBytes
        if (hasBackend() && typeof backend.listTagBuckets === "function") {
            try {
                var buckets = backend.listTagBuckets(targetPath) || {}
                nextFolderTags = buckets.folderTags || []
                nextFileTags = buckets.fileTags || []
                nextFolderTagColors = buckets.folderTagColors || ({})
                nextFileTagColors = buckets.fileTagColors || ({})
                nextFolderSize = Number(buckets.folderSizeBytes !== undefined ? buckets.folderSizeBytes : currentFolderSizeBytes)
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
        var filteredFileTags = []
        for (var j = 0; j < nextFileTags.length; j++) {
            var fileTag = String(nextFileTags[j] || "").trim()
            if (fileTag.length > 0 && !folderBag[fileTag]) {
                filteredFileTags.push(fileTag)
            }
        }

        folderTags = nextFolderTags
        fileTags = filteredFileTags
        folderTagColors = nextFolderTagColors
        fileTagColors = nextFileTagColors
        currentFolderSizeBytes = Math.max(0, Math.round(nextFolderSize || 0))
        availableTags = folderTags.concat(fileTags)

        var suggestionBag = {}
        for (var p = 0; p < nextProjectTags.length; p++) {
            var projectTag = String(nextProjectTags[p] || "").trim()
            if (projectTag.length > 0 && !folderBag[projectTag]) {
                suggestionBag[projectTag] = true
            }
        }
        for (var f = 0; f < filteredFileTags.length; f++) {
            var fileTagSuggestion = String(filteredFileTags[f] || "").trim()
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

    function appendNextChunk() {
        if (fileItemsOffset >= fileItemsRaw.length) return
        var end = Math.min(fileItemsRaw.length, fileItemsOffset + fileItemsChunk)
        for (var i = fileItemsOffset; i < end; i++) {
            filesModel.append(fileItemsRaw[i])
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

    function refreshFilters(path) {
        var targetPath = String(path || currentFilesPath())
        var nextAvailable = []
        var nextActive = ({ active: false, name: "", mode: "auto", path: "", chain: [] })
        if (hasBackend() && typeof backend.listFilters === "function") {
            try {
                nextAvailable = backend.listFilters(targetPath) || []
            } catch (e0) {
                nextAvailable = []
            }
        }
        if (hasBackend() && typeof backend.resolveActiveFilter === "function") {
            try {
                nextActive = backend.resolveActiveFilter(targetPath) || nextActive
            } catch (e1) {
                nextActive = ({ active: false, name: "", mode: "auto", path: "", chain: [] })
            }
        }
        availableFilters = nextAvailable
        activeFilter = nextActive
        manualFilterPath = String(nextActive.manualPath || "")
    }

    function activateFilterPath(path) {
        var target = String(path || "").trim()
        if (!hasBackend() || typeof backend.setManualFilter !== "function") {
            return
        }
        if (!target) {
            if (typeof backend.clearManualFilter === "function") {
                backend.clearManualFilter()
            }
        } else {
            var ok = backend.setManualFilter(target)
            if (!ok) {
                moveReportMessage = qsTr("Filter konnte nicht aktiviert werden.")
                moveReportDialog.open()
            }
        }
        refreshFilters()
        updateFiles()
    }

    function clearManualFilterOverride() {
        if (hasBackend() && typeof backend.clearManualFilter === "function") {
            backend.clearManualFilter()
        }
        refreshFilters()
        updateFiles()
    }

    function openActiveFilterSource() {
        var sourcePath = String(activeFilter.path || "").trim()
        if (!sourcePath.length) {
            return
        }
        requestOpenWith(sourcePath)
    }

    function promptFilterSave() {
        var sourcePath = String(activeFilter.path || "").trim()
        if (!sourcePath.length || !hasBackend() || typeof backend.listFilterSaveTargets !== "function") {
            return
        }
        filterSaveSourcePath = sourcePath
        filterSaveTargets = backend.listFilterSaveTargets(cwp, sourcePath) || []
        pendingFilterNewName = ""
        filterSaveDialog.open()
    }

    function applyFilterSave(targetId) {
        var target = String(targetId || "").trim()
        if (!target.length || !hasBackend() || typeof backend.saveFilter !== "function") {
            return
        }
        var result = backend.saveFilter(cwp, filterSaveSourcePath, target, pendingFilterNewName)
        if (result && result.ok) {
            moveReportMessage = qsTr("Filter gespeichert: %1").arg(String(result.path || ""))
            moveReportDialog.open()
            refreshFilters()
            return
        }
        moveReportMessage = qsTr("Filter konnte nicht gespeichert werden.")
        moveReportDialog.open()
    }

    function updateFiles() {
        var targetPath = currentFilesPath()
        if (targetPath.length === 0) {
            return
        }
        if (hasBackend() && typeof backend.invalidateEntries === "function") {
            backend.invalidateEntries(targetPath)
        }
        var entries = listEntries(targetPath)
        applyEntries(entries)
        if (hasBackend()) {
            hasMyosInCwp = backend.hasMyosDir(cwp)
            if (typeof backend.isProject === "function") {
                hasProjectInCwp = backend.isProject(cwp)
            } else {
                hasProjectInCwp = false
            }
        }
        updateClipboardState()
        refreshFilters(targetPath)
    }

    function updateTemplates() {
        var root = PathUtils.trimTrailingSlash(resolveTemplatesRootPath())
        templatesRootPath = root
        // APD follows CWD whenever perspective is inactive.
        standardPath = cwp
        if (templatesUsePerspective && perspectiveModeEnabled) {
            if (perspectiveState.active) {
                templatesPerspectivePath = templatesDisplayPathFromPerspectiveCpd(
                    String((perspectiveState && perspectiveState.cpd) ? perspectiveState.cpd : "/Templates")
                )
            } else {
                templatesPerspectivePath = templatesDisplayPathFromPerspectiveCpd("/Templates")
            }
        } else {
            templatesPerspectiveCpdByDisplayPath = ({})
        }
        var listingPath = templatesListingPath()
        standardFolders = listTemplates(listingPath)
        updateStandardFolders()
    }

    function updateThumbnail(fullPath, thumbUrl) {
        if (!fullPath || !thumbUrl) return
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
                next.thumb = thumbUrl
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
                filesModel.setProperty(j, "thumb", thumbUrl)
            }
        }
    }

    onCwpChanged: {
        selectedEntryPaths = []
        selectedTags = []
        refreshPerspectiveState()
        updateSubProjects()
        if (hasBackend() && typeof backend.setContext === "function") {
            backend.setContext(cwp)
            _openConfigPromptIfPending()
        }
        updateDefaultProjectTint()
        updateCurrentProjectTint()
        // Keep FilesPanel in sync whenever CWD changes.
        commitCTD(cwp)
        updateTemplates()
    }
    onCommittedCTDPathChanged: {
        selectedEntryPaths = []
        updateFiles()
    }
    onStandardPathChanged: {
        if (templatesUsePerspective) {
            return
        }
        if (hasBackend() && typeof backend.invalidateEntries === "function") {
            backend.invalidateEntries(standardPath)
        }
        standardFolders = listTemplates(standardPath)
        updateStandardFolders()
    }
    onTemplatesPerspectivePathChanged: {
        if (!templatesPerspectiveActive()) {
            return
        }
        standardFolders = listTemplates(templatesPerspectivePath)
        updateStandardFolders()
    }

    function updateSubProjects() {
        var query = searchText.trim()
        if (query.length === 0) {
            subProjects = listChildren(cwp)
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
        if (mode === "direct") {
            var directItems = listChildren(cwp)
            if (lower.length === 0) {
                subProjects = directItems
                return
            }
            subProjects = directItems.filter(function(item){
                return nameForItem(item).toLowerCase().indexOf(lower) !== -1
            })
            return
        }
        if (mode === "deep") {
            var allUnder = demoData.collectFromPath(cwp)
            var prefix = cwp.endsWith("/") ? cwp : (cwp + "/")
            var rel = allUnder.map(function(p){
                return p.indexOf(prefix) === 0 ? p.slice(prefix.length) : p
            })
            if (lower.length === 0) {
                subProjects = rel
                return
            }
            subProjects = rel.filter(function(name){
                return name.toLowerCase().indexOf(lower) !== -1
            })
            return
        }
        var all = demoData.collectAll()
        if (lower.length === 0) {
            subProjects = all
            return
        }
        subProjects = all.filter(function(path){
            return path.toLowerCase().indexOf(lower) !== -1
        })
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

    function beginRename(path) {
        renameActive = true
        renameTargetPath = path
        var parts = path.split("/").filter(function(p){ return p.length > 0 })
        renameDraft = parts.length > 0 ? parts[parts.length - 1] : ""
    }

    function cancelRename() {
        renameActive = false
        renameTargetPath = ""
        renameDraft = ""
    }

    function commitRename() {
        if (!renameActive) return
        var trimmed = renameDraft.trim().replace(/\s+/g, " ")
        if (trimmed.length === 0) {
            cancelRename()
            return
        }
        var parts = renameTargetPath.split("/").filter(function(p){ return p.length > 0 })
        var oldName = parts.length > 0 ? parts[parts.length - 1] : ""
        if (trimmed === oldName) {
            cancelRename()
            return
        }
        var success = demoData.renamePath(renameTargetPath, trimmed)
        if (success) {
            var newPathParts = parts.slice(0, parts.length - 1).concat([trimmed])
            var newPath = "/" + newPathParts.join("/")
            if (cwp === renameTargetPath || cwp.indexOf(renameTargetPath + "/") === 0) {
                cwp = newPath + cwp.slice(renameTargetPath.length)
            }
            setCwp(cwp)
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
        if (hasBackend() && typeof backend.currentLanguage === "function") {
            uiLanguage = backend.currentLanguage()
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
            refreshPerspectiveState()
            updateSubProjects()
            if (hasBackend() && typeof backend.setContext === "function") {
                backend.setContext(cwp)
                _openConfigPromptIfPending()
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
    onTemplatesBrowserVisibleChanged: scheduleBrowserLayoutRefresh()
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
        if (child.visible === false) {
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
            slot.Layout.maximumHeight = -1
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
        var templatesVertical = level2VerticalView
        var projectsVertical = verticalProjectView
        var ph_th = (!templatesVertical && !projectsVertical)
        var pv_th = (!templatesVertical && projectsVertical)
        var ph_tv = (templatesVertical && !projectsVertical)
        var pv_tv = (templatesVertical && projectsVertical)

        case_PH_TH.visible = ph_th
        case_PV_TH.visible = pv_th
        case_PH_TV.visible = ph_tv
        case_PV_TV.visible = pv_tv

        if (ph_th) {
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
        // Force folder browsers to recalc height and trigger layout polish so slots get correct size.
        if (templatesBrowser && typeof templatesBrowser.scheduleContentHeightUpdate === "function") {
            templatesBrowser.scheduleContentHeightUpdate()
        }
        if (projectsBrowser && typeof projectsBrowser.scheduleContentHeightUpdate === "function") {
            projectsBrowser.scheduleContentHeightUpdate()
        }
        Qt.callLater(function() {
            if (layoutCases) layoutCases.polish()
        })
        Qt.callLater(function() {
            Qt.callLater(function() {
                if (layoutCases) layoutCases.polish()
            })
        })
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
                    placeholderText: "Search      + deep    # all"
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

    ConfigPromptDialog { id: configPromptDialog; window: window }

    FolderMoveConfirmDialog { id: folderMoveConfirmDialog; window: window }

    MoveReportDialog { id: moveReportDialog; window: window }

    OpenWithDialog { id: pendingOpenWithDialog; window: window }

    FilterSaveDialog { id: filterSaveDialog; window: window }

    FilterNameDialog { id: filterNameDialog; window: window }

    CreateFolderDialog { id: createFolderDialog; window: window }

    MoveSelectedFoldersDialog { id: moveSelectedFoldersDialog; window: window }

    RenameEntryDialog { id: renameEntryDialog; window: window }

    BatchRenameDialog { id: batchRenameDialog; window: window }

    DeleteEntriesDialog { id: deleteEntriesDialog; window: window }

    onSchmalModeChanged: {
        if (schmalMode) hide_FilesPanel()
        else show_FilesPanel()
    }

    Rectangle {
        anchors.fill: parent
        color: theme.bg
        ColumnLayout { // MainRows
            anchors.fill: parent
            spacing: 6
            anchors.margins: Math.max(4, Math.round(16 / 3))

            RowLayout { // Buttonbar
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
                Rectangle { // Theme Switch
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: "transparent"
                    border.width: 0
                    implicitWidth: themeSwitchLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: themeSwitchLabel
                        anchors.centerIn: parent
                        text: darkTheme ? qsTr("Hell") : qsTr("Dunkel")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: darkTheme = !darkTheme
                    }
                }

                Rectangle { // Language toggle
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: "transparent"
                    border.width: 0
                    implicitWidth: languageToggleLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: languageToggleLabel
                        anchors.centerIn: parent
                        text: uiLanguage.toUpperCase()
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: toggleUiLanguage()
                    }
                }

                Rectangle { // Filter toggle
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: activeFilter.active ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.28) : "transparent"
                    border.width: 0
                    implicitWidth: filterToggleLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: filterToggleLabel
                        anchors.centerIn: parent
                        text: {
                            if (!activeFilter || !activeFilter.active) {
                                return qsTr("Filter: Auto")
                            }
                            var modeText = String(activeFilter.mode || "auto") === "manual" ? "M" : "A"
                            var stacked = (activeFilter.chain && activeFilter.chain.length > 1) ? " +" : ""
                            return qsTr("Filter") + ": " + String(activeFilter.name || "?") + " [" + modeText + "]" + stacked
                        }
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                        elide: Text.ElideRight
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: filterMenu.open()
                    }
                }

                Menu {
                    id: filterMenu

                    MenuItem {
                        text: qsTr("Auto folgen")
                        onTriggered: clearManualFilterOverride()
                    }
                    MenuItem {
                        text: qsTr("Aktiven Filter oeffnen")
                        enabled: String(activeFilter.path || "").length > 0
                        onTriggered: openActiveFilterSource()
                    }
                    MenuItem {
                        text: qsTr("Filter speichern ...")
                        enabled: String(activeFilter.path || "").length > 0
                        onTriggered: promptFilterSave()
                    }
                    MenuSeparator {}
                    Instantiator {
                        model: availableFilters || []
                        delegate: MenuItem {
                            required property var modelData
                            text: {
                                var item = modelData || ({})
                                var name = String(item.name || "")
                                var origin = String(item.originType || "")
                                var depth = Number(item.depth || 0)
                                return name + " [" + origin + ", d" + depth + "]"
                            }
                            onTriggered: {
                                var item = modelData || ({})
                                activateFilterPath(String(item.path || ""))
                            }
                        }
                        onObjectAdded: function(index, object) { filterMenu.insertItem(index + 4, object) }
                        onObjectRemoved: function(index, object) { filterMenu.removeItem(object) }
                    }
                }

                Rectangle { // Projects browser visibility toggle
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: projectsBrowserVisible ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.28) : "transparent"
                    border.width: 0
                    implicitWidth: projectsToggleLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: projectsToggleLabel
                        anchors.centerIn: parent
                        text: qsTr("Projekte") + " " + (projectsBrowserVisible ? qsTr("AN") : qsTr("AUS"))
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: projectsBrowserVisible = !projectsBrowserVisible
                    }
                }

                Rectangle { // Templates browser visibility toggle
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: templatesBrowserVisible ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.28) : "transparent"
                    border.width: 0
                    implicitWidth: templatesToggleLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: templatesToggleLabel
                        anchors.centerIn: parent
                        text: qsTr("Vorlagen") + " " + (templatesBrowserVisible ? qsTr("AN") : qsTr("AUS"))
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: templatesBrowserVisible = !templatesBrowserVisible
                    }
                }

                Rectangle { // Files panel opacity toggle
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: filesPanelHalfTransparent ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.28) : "transparent"
                    border.width: 0
                    implicitWidth: filesOpacityToggleLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: filesOpacityToggleLabel
                        anchors.centerIn: parent
                        text: qsTr("Dateien 50%")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: filesPanelHalfTransparent = !filesPanelHalfTransparent
                    }
                }

                Rectangle { // Schmal-Modus: 50% bei Aktivierung und wenn Maus Fenster verlässt
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: schmalMode ? Qt.rgba(theme.smallButtonActiveBg.r, theme.smallButtonActiveBg.g, theme.smallButtonActiveBg.b, 0.28) : "transparent"
                    border.width: 0
                    implicitWidth: schmalModeLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: schmalModeLabel
                        anchors.centerIn: parent
                        text: qsTr("Schmal")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: schmalMode = !schmalMode
                    }
                }

                Rectangle { // Ensure Desk.md in current project
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: "transparent"
                    border.width: 0
                    implicitWidth: deskThemeLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: deskThemeLabel
                        anchors.centerIn: parent
                        text: qsTr("Projekt mit Thema versehen")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (!hasBackend() || typeof backend.ensureProjectConfig !== "function") {
                                return
                            }
                            var result = backend.ensureProjectConfig(cwp, "Desk.md")
                            if (!result || !result.ok) {
                                moveReportMessage = qsTr("Desk.md konnte nicht erstellt werden.")
                            } else {
                                moveReportMessage = qsTr("Desk.md ist bereit im aktuellen Projekt.")
                            }
                            moveReportDialog.open()
                        }
                    }
                }

                Rectangle { // Ensure Sort.md in current project
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: "transparent"
                    border.width: 0
                    implicitWidth: sortActivateLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: sortActivateLabel
                        anchors.centerIn: parent
                        text: qsTr("Ordnung aktivieren")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (!hasBackend() || typeof backend.ensureProjectConfig !== "function") {
                                return
                            }
                            var result = backend.ensureProjectConfig(cwp, "Sort.md")
                            if (!result || !result.ok) {
                                moveReportMessage = qsTr("Sort.md konnte nicht erstellt werden.")
                            } else {
                                moveReportMessage = qsTr("Sort.md ist bereit im aktuellen Projekt.")
                            }
                            moveReportDialog.open()
                        }
                    }
                }

                Rectangle { // Manual apply sort
                    radius: TagChips.CHIP_RADIUS_MEDIUM
                    height: compactButtonHeight
                    color: "transparent"
                    border.width: 0
                    implicitWidth: sortNowLabel.implicitWidth + 16
                    width: implicitWidth
                    Text {
                        id: sortNowLabel
                        anchors.centerIn: parent
                        text: qsTr("Jetzt einsortieren")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (!hasBackend() || typeof backend.applySortNow !== "function") {
                                return
                            }
                            var report = backend.applySortNow(cwp)
                            var movedCount = (report && report.moved) ? report.moved.length : 0
                            var errorCount = (report && report.errors) ? report.errors.length : 0
                            moveReportMessage = qsTr("Sortierung: %1 verschoben, %2 Fehler")
                                .arg(movedCount)
                                .arg(errorCount)
                            moveReportDialog.open()
                            updateFiles()
                        }
                    }
                }
                
                }
            }

            Item {
                id: layoutCases
                Layout.fillWidth: true
                Layout.fillHeight: true

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

        FolderBrowser {  // TemplatesBrowser
            id: templatesBrowser
            debugName: "TemplatesBrowser"
            parent: floatingPool
            visible: templatesBrowserVisible
            verticalPreferredHeight: 390
            isPerspective: window.templatesUsePerspective
            path: (templatesBrowser.isPerspective && window.perspectiveModeEnabled)
                ? window.templatesPerspectivePath
                : standardPath
            pathDisplayPrefix: cwp
            showLeftAction: templatesBrowser.isPerspective && window.perspectiveModeEnabled
            leftActionText: qsTr("Perspective OFF")
            showEmbryos: window.templatesShowEmbryos
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            tintPathAsProject: false
            cwdOpacity: 1.0
            pathProjectOpacity: 0.7
            folderProjectOpacity: 0.55
            embryoOpacity: 0.4
            debugLayout: false
            allowDrags: true
            allowDrops: true
            folders: standardFoldersFiltered
            childrenProvider: function(targetPath) { return listTemplates(targetPath) }
            verticalView: level2VerticalView
            buttonStyle: level2ButtonStyle
            allowLargeIcons: true
            showModeToggle: true
            showSearchToggle: true
            showStyleToggle: true
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
            resolvePath: resolveTemplateDisplayPathToReal
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
        onLeftActionTriggered: {
            disablePerspectiveMode()
        }
        onToggleEmbryos: {
            window.templatesShowEmbryos = !window.templatesShowEmbryos
                var perspectiveActive = templatesBrowser.isPerspective && window.perspectiveModeEnabled
                var listingPath = perspectiveActive ? window.templatesPerspectivePath : standardPath
            standardFolders = listTemplates(listingPath)
            updateStandardFolders()
        }
            onPathSegmentActivated: function(index) {
                show_FilesPanel()
                var perspectiveActive = templatesBrowser.isPerspective && window.perspectiveModeEnabled
                var currentPath = perspectiveActive ? window.templatesPerspectivePath : standardPath
                var nextPath = currentPath
                if (templatesBrowser.fullPathForDisplayIndex) {
                    nextPath = templatesBrowser.fullPathForDisplayIndex(index)
                } else {
                    var parts = currentPath.split("/").filter(function(p){ return p.length > 0 })
                    nextPath = "/" + parts.slice(0, index + 1).join("/")
                }
                if (perspectiveActive) {
                    window.templatesPerspectivePath = nextPath
                } else {
                    standardPath = nextPath
                }
            }
            onPathSelected: function(path) {
                show_FilesPanel()
                var perspectiveActive = templatesBrowser.isPerspective && window.perspectiveModeEnabled
                if (perspectiveActive) {
                    window.templatesPerspectivePath = String(path || "")
                } else {
                    standardPath = path
                }
            }
            onFolderActivated: function(name) {
                show_FilesPanel()
                var perspectiveActive = templatesBrowser.isPerspective && window.perspectiveModeEnabled
                var currentPath = perspectiveActive ? window.templatesPerspectivePath : standardPath
                var nextPath = String(name || currentPath)
                if (perspectiveActive) {
                    window.templatesPerspectivePath = nextPath
                } else {
                    standardPath = nextPath
                }
            }
            onNavigateToPathRequested: function(path) {
                applyFolderActivation(resolveTemplateDisplayPathToReal(path))
            }
            onFolderDoubleActivated: function(path, folderMeta) {
                var targetPath = String(path || "")
                if (targetPath.length > 0) {
                    commitCTD(resolveTemplateDisplayPathToReal(targetPath))
                }
                if (!shouldApplyPerspectiveForFolderType(folderMeta)) {
                    return
                }
                if (!ensurePerspectiveOpenForTemplates()) {
                    return
                }
                var targetCpd = perspectiveCpdFromTemplatePath(String(path || ""))
                if (targetCpd.length === 0) {
                    return
                }
                applyPerspectiveCpd(targetCpd)
            }
            onFolderPreviewed: function(path) { handlePreviewPath(templatesBrowser, path) }
            onMoveEntryRequested: function(sourcePath, targetDir) { handleMoveEntry(templatesBrowser, sourcePath, targetDir) }
            onCreateFolderRequested: function(basePath) { handleCreateFolder(templatesBrowser, basePath) }
        }

        FolderBrowser {  // ProjectsBrowser
            id: projectsBrowser
            debugName: "ProjectsBrowser"
            parent: floatingPool
            z: 8
            visible: projectsBrowserVisible
            maxParents: 0
            path: cwp
            pathDisplayPrefix: cwp
            pathSegmentMyosTest: pathSegmentMyosTest
            pathSegmentMyOS: pathSegmentMyOS
            folders: subProjects
            childrenProvider: function(targetPath) { return listChildren(targetPath) }
            showEmbryos: window.projectsShowEmbryos
            showHiddenFolders: window.projectsShowHiddenFolders
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            tintPathAsProject: false
            cwdOpacity: 1.0
            pathProjectOpacity: 0.7
            folderProjectOpacity: 0.55
            embryoOpacity: 0.4
            debugLayout: false
            allowDrags: true
            allowDrops: true
            verticalView: verticalProjectView
            buttonStyle: folderItemStyle
            allowLargeIcons: true
            showModeToggle: true
            showSearchToggle: true
            showStyleToggle: true
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
            onNavigateToPathRequested: function(path) {
                show_FilesPanel()
                applyFolderActivation(path)
                clearSearchAfterNavigate()
            }
            onFolderActivated: function(name) {
                show_FilesPanel()
            }
            onFolderDoubleActivated: function(name, folderMeta) {
                var targetPath = ""
                if (name.indexOf("/") === 0) {
                    targetPath = name
                } else {
                    targetPath = cwp + "/" + name
                }
                if (projectsBrowser && typeof projectsBrowser.resetPreview === "function") {
                    projectsBrowser.resetPreview()
                    projectsBrowser.scheduleContentHeightUpdate()
                }
                setCwp(targetPath, "projectsBrowser.folderDouble")
                var committed = commitCTD(targetPath)
                clearSearchAfterNavigate()
                if (!shouldApplyPerspectiveForFolderType(folderMeta)) {
                    return
                }
                applyPerspectiveForRealPath(targetPath)
            }
            onFolderPreviewed: function(path) { handlePreviewPath(projectsBrowser, path) }
            onRenameRequested: beginRename(fullPath)
            onRenameTextEdited: renameDraft = text
            onRenameAccepted: commitRename()
            onRenameCanceled: cancelRename()
            onMoveEntryRequested: function(sourcePath, targetDir) { handleMoveEntry(projectsBrowser, sourcePath, targetDir) }
            onCreateFolderRequested: function(basePath) { handleCreateFolder(projectsBrowser, basePath) }
        }

        Connections {
            target: templatesBrowser
            onClipboardRequested: openClipboard()
            onClipboardDropRequested: function(payload) { dropToClipboard(payload) }
        }
        Connections {
            target: projectsBrowser
            onClipboardRequested: openClipboard()
            onClipboardDropRequested: function(payload) { dropToClipboard(payload) }
        }

        FilesPanel {  // FilesPanel
            id: filesPane
            parent: floatingPool
            z: 1
            itemsModel: filesModel
            baseFont: window.baseFont
            text: theme.text
            textMuted: theme.textMuted
            panelAlt: theme.panelAlt
            pillBorder: theme.pillBorder
            backgroundColor: theme.filesPaneBackground
            halfTransparent: filesPanelHalfTransparent
            templatesBrowserWidth: templatesBrowser.implicitWidth
            projectsBrowserWidth: projectsBrowser.implicitWidth
            iconFolder: window.iconFolder
            iconFolderOff: window.iconFolderOff
            iconFolderXray: Qt.resolvedUrl("Theme/icons/folder_xray.svg")
            iconFile: window.iconFile
            iconGear: window.iconGear
            itemStyle: "largeIcon"
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
            hasProjectInCwp: window.hasProjectInCwp
            hasMyosDirInCwp: window.hasMyosInCwp
            showLeaveMyosButton: window.isInsideMyosFolder
            availableTags: window.availableTags
            folderTags: window.folderTags
            fileTags: window.fileTags
            folderTagColors: window.folderTagColors
            fileTagColors: window.fileTagColors
            tagSuggestions: window.tagSuggestions
            selectedPaths: window.selectedEntryPaths
            selectedTags: window.selectedTags
            tagSource: window.tagFilterSource
            uiLanguage: window.uiLanguage
            isTagIndexing: window.tagsIndexing
            folderSizeBytes: window.currentFolderSizeBytes
            onRequestMore: appendNextChunk()
            onFilterChanged: filterEntries()
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
            onMoveEntriesRequested: function(payload, targetDir) { moveEntry(payload, targetDir) }
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
                requestCreateFolderAt(targetBase)
            }
            onMoveSelectedIntoNewFolderRequested: function(paths) {
                promptMoveSelectedIntoNewFolder(paths)
            }
            onRenameRequested: function(paths) { requestRenameEntries(paths) }
            onDeleteRequested: function(paths) { requestDeleteEntries(paths) }
            onSelectAllRequested: selectAllVisibleEntries()
            onFolderActivated: function(name) {
                show_FilesPanel()
                var targetPath = ""
                if (name.indexOf("/") === 0) {
                    targetPath = name
                } else {
                    targetPath = cwp + "/" + name
                }
                setCwp(targetPath, "filesPane.folderActivated")
                commitCTD(targetPath)
                clearSearchAfterNavigate()
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
            onXrayClicked: {
                // X-Ray-Darstellung: Platzhalter für spätere Implementierung
            }
            onLeaveMyosFolder: {
                var parent = parentOfPath(currentFilesPath())
                commitCTD(parent)
                clearSearchAfterNavigate()
            }
            onCreateProject: {
                if (hasBackend() && typeof backend.createProject === "function") {
                    var ok = backend.createProject(cwp)
                    if (ok) {
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

