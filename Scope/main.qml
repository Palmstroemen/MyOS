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
    property string iconFolder: "Theme/icons/folder.svg"
    property string iconFolderOff: "Theme/icons/folder_off.svg"
    property string iconSearch: "Theme/icons/search.svg"
    property string iconFile: "Theme/icons/file.svg"
    property string iconGear: "Theme/icons/gear.svg"
    property string folderItemStyle: "text" // text | smallIcon | largeIcon
    property int iconSizeSmall: Math.round(baseFont * 1.35)
    property int iconSizeLarge: 64
    property int compactButtonHeight: 32
    property int largeButtonPadding: 14
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
        property color accentPrimary: darkTheme ? "#524dbe" : "#6a5cff"
        property color accentPrimaryText: "#ffffff"
        property color accentSecondary: darkTheme ? "#3b476b" : "#b8c8ee"
        property color accentSecondaryBorder: darkTheme ? "#58648a" : "#9fb1dd"
        property color action: darkTheme ? "#39456b" : "#c8d2f0"
        property color actionBorder: darkTheme ? "#56618a" : "#9aa7cf"
        property color text: darkTheme ? "#e6e6e6" : "#1f2433"
        property color textMuted: darkTheme ? "#c9ccd7" : "#3b4152"
        property color textSoft: darkTheme ? "#cfd3df" : "#2b3140"
        property color filesPaneBackground: darkTheme ? "#404040" : "#b0b0b0"
        property color highlight: accentPrimary
    }

    property string cwp: "/Projekte/Haus/Dach"
    property var subProjects: []
    property string standardPath: "/finanz/Ausgangsrechnungen/2025"
    property var standardFolders: ["01", "02", "03", "04", "05"]
    property var standardFoldersFiltered: ["01", "02", "03", "04", "05"]
    property var userFolders: ["myFolder", "myOtherFolder"]
    property var files: ["Rechnung_001.pdf", "Angebot_Alpha.docx", "Note.md"]
    property var fileItemsRaw: []
    property int fileItemsOffset: 0
    property int fileItemsChunk: 160
    property bool hasMyosInCwp: false
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

    function toFileUrl(path) {
        if (path.indexOf("file://") === 0) return path
        return "file://" + path
    }

    function listChildren(path) {
        if (hasBackend()) {
            return backend.listChildren(path)
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
        var filtered = []
        var found = false
        for (var i = 0; i < entries.length; i++) {
            var entry = entries[i]
            if (entry.isDir && entry.name === ".MyOS") {
                found = true
            }
            if (entry.name && entry.name.indexOf(".") === 0) {
                continue
            }
            if (!filesPane.showFolders && entry.isDir) {
                continue
            }
            filtered.push(entry)
        }
        fileItemsRaw = filtered
        fileItemsOffset = 0
        filesModel.clear()
        appendNextChunk()
        if (!hasBackend()) {
            hasMyosInCwp = found
        }
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
        var entries = listEntries(cwp)
        applyEntries(entries)
        if (hasBackend()) {
            hasMyosInCwp = backend.hasMyosDir(cwp)
        }
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

    onCwpChanged: updateFiles()

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
            subProjects = directItems.filter(function(name){
                return name.toLowerCase().indexOf(lower) !== -1
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
        standardFoldersFiltered = standardFolders.filter(function(name){
            return name.toLowerCase().indexOf(lower) !== -1
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

    Rectangle {
        anchors.fill: parent
        color: theme.bg
        ColumnLayout { // MainRows
            anchors.fill: parent
            spacing: 12
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
                    spacing: 12
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
                        spacing: 12
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
                        spacing: 12
                        Item { id: slotTemplates_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                        Item { id: slotFiles_PH_TV; Layout.fillWidth: true; Layout.fillHeight: true }
                    }
                }

                RowLayout {   // Layout PV_TV   
                    id: case_PV_TV
                    anchors.fill: parent
                    spacing: 12
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

        FolderBrowser {
            id: templatesBrowser
            parent: floatingPool
            visible: templatesBrowserVisible
            path: standardPath
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
            largeButtonPadding: window.largeButtonPadding
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
            onSearchTextEdited: {
                level2SearchText = value
                updateStandardFolders()
            }
            onStyleChanged: level2ButtonStyle = style
            onPathSegmentActivated: {
                var parts = standardPath.split("/").filter(function(p){ return p.length > 0 })
                standardPath = "/" + parts.slice(0, index + 1).join("/")
            }
            onPathSelected: standardPath = path
            onFolderActivated: {
                var base = standardPath.endsWith("/") ? standardPath.slice(0, -1) : standardPath
                standardPath = base + "/" + name
            }
        }

        FolderBrowser {
            id: projectsBrowser
            parent: floatingPool
            visible: projectsBrowserVisible
            path: cwp
            folders: subProjects
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
            largeButtonPadding: window.largeButtonPadding
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
            onStyleChanged: folderItemStyle = style
            onToggleSearch: window.searchActive = !window.searchActive
            onSearchTextChanged: {
                window.searchText = projectsBrowser.searchText
                window.updateSubProjects()
            }
            onSearchTextEdited: {
                window.searchText = value
                window.updateSubProjects()
            }
            onPathSegmentActivated: function(index) {
                var parts = cwp.split("/").filter(function(p){ return p.length > 0 })
                setCwp("/" + parts.slice(0, index + 1).join("/"))
            }
            onPathSelected: setCwp(path)
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
        }

        FilesPanel {
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
            smallButtonBg: theme.smallButtonBg
            smallButtonBorder: theme.smallButtonBorder
            smallButtonActiveBg: theme.smallButtonActiveBg
            smallButtonActiveBorder: theme.smallButtonActiveBorder
            smallButtonText: theme.smallButtonText
            showMyosButton: window.hasMyosInCwp
        onRequestMore: appendNextChunk()
        onFilterChanged: applyEntries(fileItemsRaw)
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
        }

    }
}

