import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.folderlistmodel 2.15

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
    property string userPath: "/Eigene"
    property string level2ButtonStyle: "smallIcon"
    property real level2AvailableWidth: 0
    property real level2PathPreferredWidth: 0
    property real level2FlowPreferredWidth: 0
    property bool level2LayoutUpdatePending: false
    property real level2RightButtonsWidth: 0
    property bool level2FlowOnSecondLine: false


    // Browser visibility
    property bool projectsBrowserVisible: true
    property bool templatesBrowserVisible: true
    property bool filesPanelHalfTransparent: false
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
        // property color accentPrimary: darkTheme ? "#524dbe" : "#6a5cff"
        property color accentPrimary: darkTheme ? "#4a5675" : "#4a5163"
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

    property color currentProjectTint: theme.projectFolderTint

    property string cwp: "/Projekte/Haus/Dach"
    property var subProjects: []
    property string standardPath: "/finanz/Ausgangsrechnungen/2025"
    property var standardFolders: ["01", "02", "03", "04", "05"]
    property var standardFoldersFiltered: ["01", "02", "03", "04", "05"]
    property var userFolders: ["myFolder", "myOtherFolder"]
    property var files: ["Rechnung_001.pdf", "Angebot_Alpha.docx", "Note.md"]
    property var fileItemsAll: []
    property var fileItemsRaw: []
    property var selectedEntryPaths: []
    property int fileItemsOffset: 0
    property int fileItemsChunk: 160
    property bool hasMyosInCwp: false
    property bool hasProjectInCwp: false
    property string tagFilterSource: "project" // project | visible
    property var availableTags: []
    property var selectedTags: []
    property string tagMatchMode: "or" // or | and
    property bool projectsShowEmbryos: true
    property bool templatesShowEmbryos: true
    property var pendingMoveSources: []
    property string pendingMoveTargetDir: ""
    property string pendingMoveMessage: ""
    property string moveReportMessage: ""
    property var pendingFolderBatchSources: []
    property string pendingFolderBatchName: qsTr("Neuer Ordner")
    property string pendingRenamePath: ""
    property string pendingRenameName: ""
    property var pendingDeletePaths: []
    property var pendingBatchRenamePaths: []
    property string pendingBatchReplaceFrom: ""
    property string pendingBatchReplaceTo: ""
    property string selectionAnchorPath: ""
    property int maxVerticalParents: 4
    property int verticalParentSpacing: 6
    ListModel { id: filesModel }


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
        folder: toFileUrl(cwp)
        onCountChanged: {
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
        nameFilters: [".MyOS"]
        folder: toFileUrl(cwp)
        onCountChanged: {
            if (!hasBackend()) {
                hasMyosInCwp = fsHiddenModel.count > 0
            }
        }
    }

    function setCwp(path) {
        cwp = path
        updateSubProjects()
        updateFiles()
    }

    function hasBackend() {
        return typeof backend !== "undefined" && backend !== null
    }

    function nameForItem(item) {
        return (item && item.name) ? item.name : item
    }

    function toFileUrl(path) {
        if (path.indexOf("file://") === 0) return path
        return "file://" + path
    }

    function listChildren(path) {
        if (hasBackend()) {
            return backend.listChildren(path, projectsShowEmbryos)
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
        if (hasBackend() && typeof backend.listTemplates === "function") {
            return backend.listTemplates(path, templatesShowEmbryos)
        }
        return []
    }

    function updateCurrentProjectTint() {
        if (hasBackend() && typeof backend.projectColor === "function") {
            var color = backend.projectColor(cwp)
            currentProjectTint = (color && color.length > 0) ? color : theme.projectFolderTint
            if (typeof scopeDebugOpen !== "undefined" && scopeDebugOpen) {
                console.log("[scope] project color", cwp, currentProjectTint)
            }
            return
        }
        currentProjectTint = theme.projectFolderTint
    }

    function _decodeDragPayload(payload) {
        var text = String(payload || "").trim()
        if (text.length === 0) {
            return []
        }
        if (text.indexOf("__MYOS_PATHS__") === 0) {
            var raw = text.slice("__MYOS_PATHS__".length)
            try {
                var arr = JSON.parse(raw)
                return (arr && arr.length) ? arr : []
            } catch (e) {
                return []
            }
        }
        return [text]
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

    function _basename(path) {
        var text = String(path || "")
        if (text.length === 0) {
            return "(unknown)"
        }
        var parts = text.split("/")
        return parts.length > 0 ? (parts[parts.length - 1] || text) : text
    }

    function _splitStemAndExt(name) {
        var fileName = String(name || "")
        var dot = fileName.lastIndexOf(".")
        if (dot <= 0) {
            return { stem: fileName, ext: "" }
        }
        return {
            stem: fileName.slice(0, dot),
            ext: fileName.slice(dot)
        }
    }

    function _longestCommonPrefix(values) {
        if (!values || values.length === 0) {
            return ""
        }
        var prefix = String(values[0] || "")
        for (var i = 1; i < values.length; i++) {
            var current = String(values[i] || "")
            while (prefix.length > 0 && current.indexOf(prefix) !== 0) {
                prefix = prefix.slice(0, prefix.length - 1)
            }
            if (prefix.length === 0) {
                break
            }
        }
        return prefix
    }

    function _suggestBatchRenameToken(paths) {
        var stems = []
        for (var i = 0; i < (paths || []).length; i++) {
            var base = _basename(paths[i])
            var parts = _splitStemAndExt(base)
            stems.push(String(parts.stem || ""))
        }
        var prefix = _longestCommonPrefix(stems)
        while (prefix.length > 1) {
            var tail = prefix.charAt(prefix.length - 1)
            if ((tail >= "0" && tail <= "9") || tail === "_" || tail === "-" || tail === " ") {
                prefix = prefix.slice(0, prefix.length - 1)
                continue
            }
            break
        }
        if (prefix.length > 0) {
            return prefix
        }
        return stems.length > 0 ? stems[0] : ""
    }

    function _withNumberSuffix(stem, ext, number) {
        return stem + "(" + number + ")" + ext
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
                standardFolders = listTemplates(standardPath)
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
                        var errSource = _basename(err && err.source ? err.source : "")
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
                        var skipSource = _basename(skip && skip.source ? skip.source : "")
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
            standardFolders = listTemplates(standardPath)
            updateStandardFolders()
        }
    }

    function moveEntry(sourcePath, targetDir) {
        if (!sourcePath || !targetDir) {
            return
        }
        var sources = _decodeDragPayload(sourcePath)
        if (!sources || sources.length === 0) {
            return
        }
        if (_containsDirectory(sources)) {
            pendingMoveSources = sources
            pendingMoveTargetDir = targetDir
            var count = sources.length
            pendingMoveMessage = qsTr("Soll(en) %1 Ordner wirklich nach \"%2\" verschoben werden?")
                .arg(count)
                .arg(targetDir)
            folderMoveConfirmDialog.open()
            return
        }
        _performMove(sources, targetDir)
    }

    function createNewNote() {
        if (!hasBackend() || typeof backend.createNote !== "function") {
            return
        }
        var createdPath = backend.createNote(cwp, "New Note")
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
        pendingBatchReplaceFrom = _suggestBatchRenameToken(filesOnly)
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
            return backend.listEntries(path)
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
        recomputeAvailableTags()
        filterEntries()
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
            if (entry.isDir && entry.name === ".MyOS") {
                found = true
            }
            if (entry.name && entry.name.indexOf(".") === 0) {
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
                    if (coreEntry.name && coreEntry.name.indexOf(".") === 0) {
                        continue
                    }
                    if (!filesPane.showFolders && coreEntry.isDir) {
                        continue
                    }
                    filtered.push(coreEntry)
                }
            } else {
                filtered = []
                for (var k = 0; k < baseFiltered.length; k++) {
                    var item = baseFiltered[k]
                    var tags = item.tags || []
                    if (tags.length === 0) {
                        continue
                    }
                    var hits = 0
                    for (var t = 0; t < selectedTags.length; t++) {
                        if (tags.indexOf(selectedTags[t]) !== -1) {
                            hits++
                        }
                    }
                    var ok = matchAll ? (hits === selectedTags.length) : (hits > 0)
                    if (ok) {
                        filtered.push(item)
                    }
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

    function recomputeAvailableTags() {
        var tags = []
        if (tagFilterSource === "project" && hasBackend() && typeof backend.listProjectTags === "function") {
            tags = backend.listProjectTags(cwp) || []
        } else {
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
                    var value = entryTags[j]
                    if (value && value.length > 0) {
                        bag[value] = true
                    }
                }
            }
            tags = Object.keys(bag)
            tags.sort(function(a, b) { return a.localeCompare(b) })
        }
        availableTags = tags

        var nextSelected = []
        for (var s = 0; s < selectedTags.length; s++) {
            var selected = selectedTags[s]
            if (tags.indexOf(selected) !== -1) {
                nextSelected.push(selected)
            }
        }
        if (nextSelected.length !== selectedTags.length) {
            selectedTags = nextSelected
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

    function appendNextChunk() {
        if (fileItemsOffset >= fileItemsRaw.length) return
        var end = Math.min(fileItemsRaw.length, fileItemsOffset + fileItemsChunk)
        for (var i = fileItemsOffset; i < end; i++) {
            filesModel.append(fileItemsRaw[i])
        }
        fileItemsOffset = end
    }

    function openFileEntry(name) {
        var fullPath = name.indexOf("/") === 0 ? name : (cwp + "/" + name)
        var lower = fullPath.toLowerCase()
        if (typeof scopeDebugOpen !== "undefined" && scopeDebugOpen) {
            var backendAvailable = hasBackend()
            var openMarkdownType = backendAvailable ? typeof backend.openMarkdown : "n/a"
            console.log("[scope] openFileEntry", fullPath, "backend", backendAvailable, "openMarkdown", openMarkdownType)
        }
        if (lower.endsWith(".md") && hasBackend() && typeof backend.openMarkdown === "function") {
            backend.openMarkdown(fullPath)
            return
        }
        Qt.openUrlExternally(toFileUrl(fullPath))
    }

    function updateFiles() {
        if (hasBackend() && typeof backend.invalidateEntries === "function") {
            backend.invalidateEntries(cwp)
        }
        var entries = listEntries(cwp)
        applyEntries(entries)
        if (hasBackend()) {
            hasMyosInCwp = backend.hasMyosDir(cwp)
            if (typeof backend.isProject === "function") {
                hasProjectInCwp = backend.isProject(cwp)
            } else {
                hasProjectInCwp = false
            }
        }
    }

    function updateTemplates() {
        if (typeof scopeDebugOpen !== "undefined" && scopeDebugOpen) {
            console.log("[scope] updateTemplates cwp", cwp)
        }
        standardPath = cwp
    }

    function updateThumbnail(fullPath, thumbUrl) {
        if (!fullPath || !thumbUrl) return
        var updated = fileItems.slice(0)
        for (var i = 0; i < updated.length; i++) {
            var item = updated[i]
            var itemPath = item.path ? item.path : (cwp + "/" + item.name)
            if (itemPath === fullPath) {
                var next = {}
                for (var key in item) {
                    next[key] = item[key]
                }
                next.thumb = thumbUrl
                updated[i] = next
                fileItems = updated
                return
            }
        }
    }

    onCwpChanged: {
        selectedEntryPaths = []
        selectedTags = []
        if (hasBackend() && typeof backend.setContext === "function") {
            backend.setContext(cwp)
        }
        updateCurrentProjectTint()
        updateFiles()
        updateTemplates()
    }
    onStandardPathChanged: {
        if (hasBackend() && typeof backend.invalidateEntries === "function") {
            backend.invalidateEntries(standardPath)
        }
        standardFolders = listTemplates(standardPath)
        if (typeof scopeDebugOpen !== "undefined" && scopeDebugOpen) {
            console.log("[scope] templates", standardPath, standardFolders)
        }
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

    function displaySubprojectLabel(path) {
        var query = searchText.trim()
        if (query.length === 0) return path
        if (query[0] === "+" || query[0] === "#") {
            return shortenPathForDisplay(path)
        }
        return path
    }

    function verticalfolderItemStyle() {
        return folderItemStyle === "largeIcon" ? "text" : folderItemStyle
    }

    function lastPathSegment(path) {
        var parts = path.split("/").filter(function(p){ return p.length > 0 })
        return parts.length > 0 ? parts[parts.length - 1] : "/"
    }

    function rootPathOf(path) {
        var parts = path.split("/").filter(function(p){ return p.length > 0 })
        return parts.length > 0 ? ("/" + parts[0]) : "/"
    }

    function parentPathsFor(path) {
        var parts = path.split("/").filter(function(p){ return p.length > 0 })
        var paths = []
        for (var i = 0; i < parts.length - 1; i++) {
            paths.push("/" + parts.slice(0, i + 1).join("/"))
        }
        return paths
    }

    function visibleParentPathsFor(path, panelHeight) {
        var parents = parentPathsFor(path)
        if (parents.length <= maxVerticalParents) return parents
        var approxNeeded = parents.length * (compactButtonHeight + verticalParentSpacing)
        var reserve = (compactButtonHeight + verticalParentSpacing) * 4
        if (panelHeight && (approxNeeded + reserve) > panelHeight) {
            return parents.slice(Math.max(0, parents.length - maxVerticalParents))
        }
        return parents
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

    function createSubproject(name) {
        var trimmed = name.trim().replace(/\s+/g, " ")
        if (trimmed.length === 0) return false
        if (demoData.addChild(cwp, trimmed)) {
            setCwp(cwp)
            return true
        }
        return false
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
            console.warn("[scope] missing property", propName, "on", label)
        }
    }

    function warnIfMissingAny(target, propNames, label) {
        for (var i = 0; i < propNames.length; i++) {
            warnIfMissing(target, propNames[i], label)
        }
    }

    Component.onCompleted: {
        Qt.application.windowIcon = Qt.resolvedUrl(iconFolder)
        if (typeof scopeDebugOpen !== "undefined" && scopeDebugOpen) {
            var backendAvailable = hasBackend()
            var openMarkdownType = backendAvailable ? typeof backend.openMarkdown : "n/a"
            console.log("[scope] backend available", backendAvailable, "openMarkdown", openMarkdownType)
        }
        var startPath = (typeof scopeStartPath !== "undefined" && scopeStartPath) ? scopeStartPath : cwp
        if (!hasBackend() && (!startPath || startPath === cwp)) {
            var resolved = Qt.resolvedUrl(".")
            if (resolved.indexOf("file://") === 0) {
                startPath = resolved.slice(7)
            }
        }
        setCwp(startPath)
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
    }
    Connections {
        target: templatesBrowser
        function onImplicitWidthChanged() {
            if (templatesBrowser && templatesBrowser.verticalView) {
                scheduleBrowserLayoutRefresh()
            }
        }
    }
    Connections {
        target: backend
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
        recomputeAvailableTags()
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
    onLevel2ButtonStyleChanged: {
        scheduleLevel2LayoutUpdate()
        scheduleBrowserLayoutRefresh()
    }

    function scheduleLevel2LayoutUpdate() {
        if (level2LayoutUpdatePending) return
        level2LayoutUpdatePending = true
        Qt.callLater(function() {
            level2LayoutUpdatePending = false
            updateLevel2FlowPlacement()
        })
    }

    function updateLevel2FlowPlacement() {
        if (typeof standardTopRow === "undefined" ||
            typeof standardPathRow === "undefined" ||
            typeof level2TopFoldersRow === "undefined" ||
            typeof level2RightButtons === "undefined" ||
            typeof level2ToggleButton === "undefined") {
            return
        }
        if (!standardTopRow || !standardPathRow || !level2TopFoldersRow || !level2RightButtons || !level2ToggleButton) return
        var available = standardTopRow.width - level2RightButtonsWidth - level2ToggleButton.width - (standardTopRow.spacing * 3)
        if (available < 0) available = 0
        if (level2AvailableWidth !== available) level2AvailableWidth = available
        if (available === 0) {
            if (!level2FlowOnSecondLine) level2FlowOnSecondLine = true
            if (level2PathPreferredWidth !== standardPathRow.implicitWidth) level2PathPreferredWidth = standardPathRow.implicitWidth
            if (level2FlowPreferredWidth !== 0) level2FlowPreferredWidth = 0
            return
        }
        var shouldWrap = (standardPathRow.implicitWidth + level2TopFoldersRow.implicitWidth) > available
        if (level2FlowOnSecondLine !== shouldWrap) level2FlowOnSecondLine = shouldWrap
        if (shouldWrap) {
            if (level2PathPreferredWidth !== available) level2PathPreferredWidth = available
            if (level2FlowPreferredWidth !== 0) level2FlowPreferredWidth = 0
        } else {
            var newPath = Math.min(standardPathRow.implicitWidth, available - level2TopFoldersRow.implicitWidth)
            var newFlow = Math.max(0, available - newPath)
            if (level2PathPreferredWidth !== newPath) level2PathPreferredWidth = newPath
            if (level2FlowPreferredWidth !== newFlow) level2FlowPreferredWidth = newFlow
        }
    }

    function setBrowserParent(item, newParent) {
        if (item && newParent && item.parent !== newParent) {
            item.parent = newParent
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
        if (wantsFillHeight) {
            slot.Layout.fillHeight = true
            slot.Layout.preferredHeight = -1
            slot.Layout.minimumHeight = 0
            slot.Layout.maximumHeight = -1
        } else if (isFolderBrowser && !inRowLayout) {
            slot.Layout.fillHeight = false
            slot.Layout.preferredHeight = Qt.binding(function() { return child.implicitHeight })
            slot.Layout.minimumHeight = Qt.binding(function() { return child.implicitHeight })
            slot.Layout.maximumHeight = Qt.binding(function() { return child.implicitHeight })
        } else {
            slot.Layout.fillHeight = true
            slot.Layout.preferredHeight = -1
            slot.Layout.minimumHeight = 0
            slot.Layout.maximumHeight = -1
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
                radius: 4
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

    Dialog {
        id: folderMoveConfirmDialog
        title: qsTr("Ordner-Verschieben bestaetigen")
        modal: true
        focus: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: Overlay.overlay
        width: Math.max(440, Math.round(window.width * 0.34))
        Overlay.modal: Rectangle {
            color: "black"
            opacity: 0.38
        }
        background: Rectangle {
            radius: 16
            color: dialogPanelBg
            border.color: dialogPanelBorder
            border.width: 2
        }
        onOpened: {
            _setDialogButtonText(folderMoveConfirmDialog, Dialog.Ok, qsTr("Uebernehmen"))
            _setDialogButtonText(folderMoveConfirmDialog, Dialog.Cancel, qsTr("Abbrechen"))
        }
        onAccepted: {
            _performMove(pendingMoveSources, pendingMoveTargetDir)
            pendingMoveSources = []
            pendingMoveTargetDir = ""
            pendingMoveMessage = ""
        }
        onRejected: {
            pendingMoveSources = []
            pendingMoveTargetDir = ""
            pendingMoveMessage = ""
        }
        contentItem: Text {
            text: pendingMoveMessage
            wrapMode: Text.WordWrap
            color: dialogTextStrong
            font.pixelSize: baseFont
        }
    }

    Dialog {
        id: moveReportDialog
        title: qsTr("Verschiebebericht")
        modal: true
        focus: true
        standardButtons: Dialog.Ok
        anchors.centerIn: Overlay.overlay
        width: Math.max(520, Math.round(window.width * 0.42))
        Overlay.modal: Rectangle {
            color: "black"
            opacity: 0.38
        }
        background: Rectangle {
            radius: 16
            color: dialogPanelBg
            border.color: dialogPanelBorder
            border.width: 2
        }
        onOpened: _setDialogButtonText(moveReportDialog, Dialog.Ok, qsTr("Schliessen"))
        onAccepted: moveReportMessage = ""
        onRejected: moveReportMessage = ""
        contentItem: Text {
            text: moveReportMessage
            wrapMode: Text.WordWrap
            color: dialogTextStrong
            font.pixelSize: baseFont
        }
    }

    Dialog {
        id: moveSelectedFoldersDialog
        title: qsTr("In neuen Ordner verschieben")
        modal: true
        focus: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: Overlay.overlay
        width: Math.max(460, Math.round(window.width * 0.35))
        Overlay.modal: Rectangle {
            color: "black"
            opacity: 0.38
        }
        background: Rectangle {
            radius: 16
            color: dialogPanelBg
            border.color: dialogPanelBorder
            border.width: 2
        }
        onOpened: {
            _setDialogButtonText(moveSelectedFoldersDialog, Dialog.Ok, qsTr("Uebernehmen"))
            _setDialogButtonText(moveSelectedFoldersDialog, Dialog.Cancel, qsTr("Abbrechen"))
            folderBatchNameInput.forceActiveFocus()
            folderBatchNameInput.selectAll()
        }
        onAccepted: {
            var folderName = String(folderBatchNameInput.text || "").trim()
            if (!folderName) {
                pendingFolderBatchSources = []
                pendingFolderBatchName = qsTr("Neuer Ordner")
                return
            }
            if (!hasBackend() || typeof backend.createFolder !== "function") {
                pendingFolderBatchSources = []
                pendingFolderBatchName = qsTr("Neuer Ordner")
                return
            }
            var targetPath = backend.createFolder(cwp, folderName)
            if (!targetPath || targetPath.length === 0) {
                moveReportMessage = qsTr("Konnte Zielordner \"%1\" nicht erstellen.").arg(folderName)
                moveReportDialog.open()
                pendingFolderBatchSources = []
                pendingFolderBatchName = qsTr("Neuer Ordner")
                return
            }
            _performMove(pendingFolderBatchSources, targetPath)
            pendingFolderBatchSources = []
            pendingFolderBatchName = qsTr("Neuer Ordner")
        }
        onRejected: {
            pendingFolderBatchSources = []
            pendingFolderBatchName = qsTr("Neuer Ordner")
        }
        contentItem: Column {
            spacing: 10
            Text {
                text: qsTr("Erstellt einen Ordner und verschiebt die ausgewaehlten Eintraege hinein.")
                wrapMode: Text.WordWrap
                color: dialogTextStrong
                font.pixelSize: baseFont
            }
            TextField {
                id: folderBatchNameInput
                text: pendingFolderBatchName
                placeholderText: qsTr("Neuer Ordnername")
                selectByMouse: true
                color: dialogInputText
                placeholderTextColor: dialogInputPlaceholder
                topPadding: 10
                bottomPadding: 10
                leftPadding: 12
                rightPadding: 12
                background: Rectangle {
                    radius: 12
                    color: dialogInputBg
                    border.color: dialogInputBorder
                    border.width: 2
                }
            }
        }
    }

    Dialog {
        id: renameEntryDialog
        title: qsTr("Datei umbenennen")
        modal: true
        focus: true
        standardButtons: Dialog.Cancel
        anchors.centerIn: Overlay.overlay
        width: Math.max(420, Math.round(window.width * 0.30))
        Overlay.modal: Rectangle {
            color: "black"
            opacity: 0.38
        }
        background: Rectangle {
            radius: 16
            color: dialogPanelBg
            border.color: dialogPanelBorder
            border.width: 2
        }
        onOpened: {
            _setDialogButtonText(renameEntryDialog, Dialog.Cancel, qsTr("Abbrechen"))
            renameEntryInput.forceActiveFocus()
            renameEntryInput.selectAll()
        }
        onAccepted: {
            var nextName = String(renameEntryInput.text || "").trim()
            if (!nextName) {
                pendingRenamePath = ""
                pendingRenameName = ""
                return
            }
            var renamed = backend.renameEntry(pendingRenamePath, nextName)
            if (!renamed || renamed.length === 0) {
                moveReportMessage = qsTr("Konnte \"%1\" nicht umbenennen.").arg(_basename(pendingRenamePath))
                moveReportDialog.open()
                pendingRenamePath = ""
                pendingRenameName = ""
                return
            }
            selectedEntryPaths = [renamed]
            updateFiles()
            pendingRenamePath = ""
            pendingRenameName = ""
        }
        onRejected: {
            pendingRenamePath = ""
            pendingRenameName = ""
        }
        contentItem: Column {
            spacing: 8
            Text {
                text: qsTr("Neuen Dateinamen eingeben und mit Return uebernehmen.")
                wrapMode: Text.WordWrap
                color: dialogTextStrong
                font.pixelSize: baseFont
            }
            TextField {
                id: renameEntryInput
                text: pendingRenameName
                placeholderText: qsTr("Neuer Name")
                selectByMouse: true
                color: dialogInputText
                placeholderTextColor: dialogInputPlaceholder
                topPadding: 10
                bottomPadding: 10
                leftPadding: 12
                rightPadding: 12
                background: Rectangle {
                    radius: 12
                    color: dialogInputBg
                    border.color: dialogInputBorder
                    border.width: 2
                }
                Keys.onReturnPressed: renameEntryDialog.accept()
                Keys.onEnterPressed: renameEntryDialog.accept()
                Keys.onEscapePressed: renameEntryDialog.reject()
            }
        }
    }

    Dialog {
        id: batchRenameDialog
        title: qsTr("Dateien gesammelt umbenennen")
        modal: true
        focus: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: Overlay.overlay
        width: Math.max(480, Math.round(window.width * 0.36))
        Overlay.modal: Rectangle {
            color: "black"
            opacity: 0.38
        }
        background: Rectangle {
            radius: 16
            color: dialogPanelBg
            border.color: dialogPanelBorder
            border.width: 2
        }
        onOpened: {
            _setDialogButtonText(batchRenameDialog, Dialog.Ok, qsTr("Uebernehmen"))
            _setDialogButtonText(batchRenameDialog, Dialog.Cancel, qsTr("Abbrechen"))
            batchRenameToInput.forceActiveFocus()
            batchRenameToInput.selectAll()
        }
        onAccepted: {
            var fromText = String(pendingBatchReplaceFrom || "")
            var toText = String(batchRenameToInput.text || "")
            if (fromText.length === 0) {
                moveReportMessage = qsTr("Kein gemeinsamer Suchtext gefunden.")
                moveReportDialog.open()
                pendingBatchRenamePaths = []
                pendingBatchReplaceFrom = ""
                pendingBatchReplaceTo = ""
                return
            }
            var renamedPaths = []
            var unchangedCount = 0
            var failedCount = 0
            for (var i = 0; i < pendingBatchRenamePaths.length; i++) {
                var source = String(pendingBatchRenamePaths[i] || "").trim()
                if (!source) {
                    continue
                }
                var base = _basename(source)
                var split = _splitStemAndExt(base)
                var nextStem = split.stem.split(fromText).join(toText)
                if (nextStem === split.stem) {
                    unchangedCount += 1
                    continue
                }
                var renamed = ""
                var nextName = nextStem + split.ext
                renamed = backend.renameEntry(source, nextName)
                if (!renamed || renamed.length === 0) {
                    for (var n = 1; n < 1000; n++) {
                        var fallback = _withNumberSuffix(nextStem, split.ext, n)
                        renamed = backend.renameEntry(source, fallback)
                        if (renamed && renamed.length > 0) {
                            break
                        }
                    }
                }
                if (renamed && renamed.length > 0) {
                    renamedPaths.push(renamed)
                } else {
                    failedCount += 1
                }
            }
            pendingBatchRenamePaths = []
            pendingBatchReplaceFrom = ""
            pendingBatchReplaceTo = ""
            selectedEntryPaths = renamedPaths
            updateFiles()
            moveReportMessage = qsTr("Umbenannt: %1\nUnveraendert: %2\nFehlgeschlagen: %3")
                .arg(renamedPaths.length)
                .arg(unchangedCount)
                .arg(failedCount)
            moveReportDialog.open()
        }
        onRejected: {
            pendingBatchRenamePaths = []
            pendingBatchReplaceFrom = ""
            pendingBatchReplaceTo = ""
        }
        contentItem: Column {
            spacing: 12
            Text {
                text: qsTr("\"%1\" umbenennen auf").arg(pendingBatchReplaceFrom)
                wrapMode: Text.WordWrap
                color: dialogTextStrong
                font.pixelSize: Math.max(baseFont + 1, 14)
                font.bold: true
            }
            TextField {
                id: batchRenameToInput
                text: pendingBatchReplaceTo
                placeholderText: pendingBatchReplaceFrom.length > 0
                    ? pendingBatchReplaceFrom
                    : qsTr("Neuer Text")
                selectByMouse: true
                color: dialogInputText
                placeholderTextColor: dialogInputPlaceholder
                topPadding: 10
                bottomPadding: 10
                leftPadding: 12
                rightPadding: 12
                background: Rectangle {
                    radius: 12
                    color: dialogInputBg
                    border.color: dialogInputBorder
                    border.width: 2
                }
            }
            Text {
                text: qsTr("Bei Namenskonflikten wird automatisch (1), (2), ... angehaengt.")
                wrapMode: Text.WordWrap
                color: dialogTextMuted
                font.pixelSize: Math.max(baseFont - 1, 11)
            }
        }
    }

    Dialog {
        id: deleteEntriesDialog
        title: qsTr("Dateien loeschen")
        modal: true
        focus: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        anchors.centerIn: Overlay.overlay
        width: Math.max(440, Math.round(window.width * 0.32))
        Overlay.modal: Rectangle {
            color: "black"
            opacity: 0.38
        }
        background: Rectangle {
            radius: 16
            color: dialogPanelBg
            border.color: dialogPanelBorder
            border.width: 2
        }
        onOpened: {
            _setDialogButtonText(deleteEntriesDialog, Dialog.Ok, qsTr("Uebernehmen"))
            _setDialogButtonText(deleteEntriesDialog, Dialog.Cancel, qsTr("Abbrechen"))
        }
        onAccepted: {
            performDeleteEntries(pendingDeletePaths)
            pendingDeletePaths = []
        }
        onRejected: pendingDeletePaths = []
        contentItem: Text {
            text: qsTr("Wirklich %1 Dateien loeschen? Das kann nicht rueckgaengig gemacht werden.")
                .arg(pendingDeletePaths.length)
            wrapMode: Text.WordWrap
            color: dialogTextStrong
            font.pixelSize: baseFont
        }
    }

    Rectangle {
        anchors.fill: parent
        color: theme.bg
        ColumnLayout { // MainRows
            anchors.fill: parent
            spacing: 6
            anchors.margins: 16

            RowLayout { // Buttonbar
                Layout.fillWidth: true
                spacing: 8
                Rectangle { // Theme Switch
                    radius: 6
                    height: compactButtonHeight
                    color: theme.accentPrimary
                    border.color: theme.accentPrimary
                    Text {
                        anchors.centerIn: parent
                        text: darkTheme ? "Light" : "Dark"
                        color: theme.accentPrimaryText
                        font.pixelSize: baseFont
                    }
                    implicitWidth: 70
                    MouseArea {
                        anchors.fill: parent
                        onClicked: darkTheme = !darkTheme
                    }
                }

                Rectangle { // Projects browser visibility toggle
                    radius: 6
                    height: compactButtonHeight
                    color: projectsBrowserVisible ? theme.smallButtonActiveBg : theme.smallButtonBg
                    border.color: projectsBrowserVisible ? theme.smallButtonActiveBorder : theme.smallButtonBorder
                    implicitWidth: 180
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Projects " + (projectsBrowserVisible ? "ON" : "OFF")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: projectsBrowserVisible = !projectsBrowserVisible
                    }
                }
                
                Rectangle { // Templates browser visibility toggle
                    radius: 6
                    height: compactButtonHeight
                    color: templatesBrowserVisible ? theme.smallButtonActiveBg : theme.smallButtonBg
                    border.color: templatesBrowserVisible ? theme.smallButtonActiveBorder : theme.smallButtonBorder
                    implicitWidth: 180
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Templates " + (templatesBrowserVisible ? "ON" : "OFF")
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: templatesBrowserVisible = !templatesBrowserVisible
                    }
                }

                Rectangle { // Files panel opacity toggle
                    radius: 6
                    height: compactButtonHeight
                    color: filesPanelHalfTransparent ? theme.smallButtonActiveBg : theme.smallButtonBg
                    border.color: filesPanelHalfTransparent ? theme.smallButtonActiveBorder : theme.smallButtonBorder
                    implicitWidth: 160
                    Text {
                        anchors.centerIn: parent
                        text: "Files 50%"
                        color: theme.smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: filesPanelHalfTransparent = !filesPanelHalfTransparent
                    }
                }
                
                Item { Layout.fillWidth: true }
            }

            Item {
                id: layoutCases
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout { // Layout PH_TH   
                    id: case_PH_TH
                    anchors.fill: parent
                    spacing: 6
                    visible: false
                    Item { id: slotTemplates_PH_TH; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item { id: slotProjects_PH_TH; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item { id: slotFiles_PH_TH; Layout.fillWidth: true; Layout.fillHeight: true }
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
                        spacing: 6
                        Item { id: slotProjects_PV_TH; Layout.fillWidth: false; Layout.fillHeight: true }
                        Item { id: slotFiles_PV_TH; Layout.fillWidth: true; Layout.fillHeight: true }
                    }
                }


                ColumnLayout { // Layout PH_TV
                    id: case_PH_TV
                    anchors.fill: parent
                    spacing: 12
                    visible: false
                    Item { id: slotProjects_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 6
                        Item { id: slotTemplates_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                        Item { id: slotFiles_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    }
                }

                RowLayout {   // Layout PV_TV   
                    id: case_PV_TV
                    anchors.fill: parent
                    spacing: 6
                    visible: false
                    Item { id: slotProjects_PV_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item { id: slotTemplates_PV_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    Item { id: slotFiles_PV_TV; Layout.fillWidth: true; Layout.fillHeight: true }
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
            parent: floatingPool
            visible: templatesBrowserVisible
            path: standardPath
            pathDisplayPrefix: cwp
            showEmbryos: window.templatesShowEmbryos
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            tintPathAsProject: false
            cwdOpacity: 1.0
            pathProjectOpacity: 0.7
            folderProjectOpacity: 0.55
            embryoOpacity: 0.4
            debugLayout: typeof scopeDebugOpen !== "undefined" && scopeDebugOpen
            allowDrags: true
            allowDrops: true
            folders: standardFoldersFiltered
            verticalView: level2VerticalView
            buttonStyle: level2ButtonStyle
            allowLargeIcons: true
            showModeToggle: true
            showSearchToggle: true
            showStyleToggle: true
            showThemeToggle: false
            baseFont: window.baseFont
            compactButtonHeight: window.compactButtonHeight
            largeButtonHeight: window.largeButtonHeight
            largeButtonPadding: Math.round(window.largeButtonPadding * 0.5)
            iconSizeSmall: window.iconSizeSmall
            iconSizeLarge: window.iconSizeLarge
            iconFolder: window.iconFolder
            iconSearch: window.iconSearch
            indent: 30
            panelColor: theme.panelAlt
            panelBorderColor: theme.pillBorder
            accentPrimary: theme.accentPrimary
            accentPrimaryText: theme.accentPrimaryText
            pill: theme.pill
            pillBorder: theme.pillBorder
            pathButtonFill: theme.pill
            pathButtonBorder: theme.pillBorder
            folderButtonFill: theme.smallButtonBg
            folderButtonBorder: theme.smallButtonBorder
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
        onToggleEmbryos: {
            window.templatesShowEmbryos = !window.templatesShowEmbryos
            standardFolders = listTemplates(standardPath)
            updateStandardFolders()
        }
            onPathSegmentActivated: function(index) {
                if (templatesBrowser.fullPathForDisplayIndex) {
                    standardPath = templatesBrowser.fullPathForDisplayIndex(index)
                    return
                }
                var parts = standardPath.split("/").filter(function(p){ return p.length > 0 })
                standardPath = "/" + parts.slice(0, index + 1).join("/")
            }
            onPathSelected: function(path) { standardPath = path }
            onFolderActivated: {
                var base = standardPath.endsWith("/") ? standardPath.slice(0, -1) : standardPath
                standardPath = base + "/" + name
            }
            onMoveEntryRequested: moveEntry(sourcePath, targetDir)
        }

        FolderBrowser {  // ProjectsBrowser
            id: projectsBrowser
            parent: floatingPool
            visible: projectsBrowserVisible
            path: cwp
            folders: subProjects
            showEmbryos: window.projectsShowEmbryos
            projectTint: window.currentProjectTint
            projectTintBorder: window.currentProjectTint
            tintPathAsProject: true
            cwdOpacity: 1.0
            pathProjectOpacity: 0.7
            folderProjectOpacity: 0.55
            embryoOpacity: 0.4
            debugLayout: typeof scopeDebugOpen !== "undefined" && scopeDebugOpen
            allowDrags: true
            allowDrops: true
            verticalView: verticalProjectView
            buttonStyle: folderItemStyle
            allowLargeIcons: true
            showModeToggle: true
            showSearchToggle: true
            showStyleToggle: true
            showThemeToggle: false
            baseFont: window.baseFont
            compactButtonHeight: window.compactButtonHeight
            largeButtonHeight: window.largeButtonHeight
            largeButtonPadding: Math.round(window.largeButtonPadding * 0.5)
            iconSizeSmall: window.iconSizeSmall
            iconSizeLarge: window.iconSizeLarge
            iconFolder: window.iconFolder
            iconSearch: window.iconSearch
            indent: 30
            panelColor: theme.panel
            panelBorderColor: theme.pillBorder
            accentPrimary: theme.accentPrimary
            accentPrimaryText: theme.accentPrimaryText
            pill: theme.pill
            pillBorder: theme.pillBorder
            pathButtonFill: theme.pill
            pathButtonBorder: theme.pillBorder
            folderButtonFill: theme.smallButtonBg
            folderButtonBorder: theme.smallButtonBorder
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
            allowRename: true
            renameTargetPath: renameTargetPath
            renameDraft: renameDraft
            searchActive: window.searchActive
            searchText: window.searchText
            onToggleMode: verticalProjectView = !verticalProjectView
            // Eingesetzt
            pathColorFunction: function(path, isCurrent) {
                if (!hasBackend()) return null;

                // 👇 Nur echte Projekte bekommen eine Farbe
                if (!backend.isProject(path)) return null;

                var color = backend.projectColor(path);
                if (color && color.length > 0) {
                    var opacity = isCurrent ? projectsBrowser.cwdOpacity : projectsBrowser.pathProjectOpacity;
                    return {
                        fill:   projectsBrowser.colorWithAlpha(color, opacity, projectsBrowser.projectTint),
                        stroke: projectsBrowser.colorWithAlpha(color, opacity, projectsBrowser.projectTintBorder)
                    };
                }
                return null;
            }
            // Ende Eingesetzt

            onStyleChanged: function(style) { folderItemStyle = style }
        onToggleEmbryos: {
            window.projectsShowEmbryos = !window.projectsShowEmbryos
            updateSubProjects()
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
            onPathSegmentActivated: function(index) {
                var parts = cwp.split("/").filter(function(p){ return p.length > 0 })
                setCwp("/" + parts.slice(0, index + 1).join("/"))
            }
            onPathSelected: function(path) { setCwp(path) }
            onFolderActivated: function(name) {
                if (name.indexOf("/") === 0) {
                    setCwp(name)
                } else {
                    setCwp(cwp + "/" + name)
                }
                clearSearchAfterNavigate()
            }
            onRenameRequested: beginRename(fullPath)
            onRenameTextEdited: renameDraft = text
            onRenameAccepted: commitRename()
            onRenameCanceled: cancelRename()
            onMoveEntryRequested: moveEntry(sourcePath, targetDir)
        }

        FilesPanel {  // FilesPanel
            id: filesPane
            parent: floatingPool
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
            projectTintOpacity: 0.75
            showMyosButton: window.hasProjectInCwp
            showCreateProject: !window.hasProjectInCwp
            availableTags: window.availableTags
            selectedPaths: window.selectedEntryPaths
            selectedTags: window.selectedTags
            tagSource: window.tagFilterSource
            onRequestMore: appendNextChunk()
            onFilterChanged: filterEntries()
            onItemActivated: function(path, ctrlPressed, shiftPressed) {
                toggleEntrySelection(path, ctrlPressed, shiftPressed)
            }
            onSelectionBoxApplied: function(paths, additive) { applySelectionBox(paths, additive) }
            onMoveEntriesRequested: function(payload, targetDir) { moveEntry(payload, targetDir) }
            onTagToggled: function(tag) { toggleTagSelection(tag) }
            onRequestTagSourceChange: function(source) { tagFilterSource = source }
            onCreateNoteRequested: createNewNote()
            onMoveSelectedIntoNewFolderRequested: function(paths) {
                promptMoveSelectedIntoNewFolder(paths)
            }
            onRenameRequested: function(paths) { requestRenameEntries(paths) }
            onDeleteRequested: function(paths) { requestDeleteEntries(paths) }
            onSelectAllRequested: selectAllVisibleEntries()
            onFolderActivated: function(name) {
                if (name.indexOf("/") === 0) {
                    setCwp(name)
                } else {
                    setCwp(cwp + "/" + name)
                }
                clearSearchAfterNavigate()
            }
            onFileActivated: function(name) {
                openFileEntry(name)
            }
            onOpenMyosFolder: {
                var base = cwp.endsWith("/") ? cwp.slice(0, -1) : cwp
                setCwp(base + "/.MyOS")
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
                        standardFolders = listTemplates(cwp)
                        updateStandardFolders()
                    }
                }
            }
        }

    }
}

