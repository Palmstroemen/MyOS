import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    width: 1400
    height: 900
    visible: true
    title: "Scope - MyOS GUI Stub"

    property int baseFont: Qt.application.font.pixelSize
    property bool darkTheme: true
    property string iconFolder: "Theme/icons/folder.svg"
    property string iconSearch: "Theme/icons/search.svg"
    property string projectButtonStyle: "text" // text | smallIcon | largeIcon
    property int iconSizeSmall: Math.round(baseFont * 1.35)
    property int iconSizeLarge: 120
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
    QtObject {
        id: theme
        property color bg: darkTheme ? "#0f1014" : "#f3f4f8"
        property color panel: darkTheme ? "#1b1d26" : "#e6e8f0"
        property color panelAlt: darkTheme ? "#151821" : "#e9ecf5"
        property color panelAlt2: darkTheme ? "#12141b" : "#eef1f8"
        property color card: darkTheme ? "#0f1117" : "#ffffff"
        property color pill: darkTheme ? "#2a2f40" : "#dfe3f0"
        property color pillBorder: darkTheme ? "#3a4158" : "#c6ccdf"
        property color accentPrimary: darkTheme ? "#524dbe" : "#6a5cff"
        property color accentPrimaryText: "#ffffff"
        property color accentSecondary: darkTheme ? "#3b476b" : "#b8c8ee"
        property color accentSecondaryBorder: darkTheme ? "#58648a" : "#9fb1dd"
        property color action: darkTheme ? "#39456b" : "#c8d2f0"
        property color actionBorder: darkTheme ? "#56618a" : "#9aa7cf"
        property color text: darkTheme ? "#e6e6e6" : "#1f2433"
        // property color textMuted: darkTheme ? "#c9ccd7" : "#3b4152"
        property color textMuted: darkTheme ? "#ff0000" : "#3b4152"
        // property color textSoft: darkTheme ? "#00ff00" : "#2b3140"
        property color textSoft: darkTheme ? "#cfd3df" : "#2b3140"
        property color highlight: accentPrimary
    }

    property string cwp: "/Projekte/Haus/Dach"
    property var subProjects: []
    property string standardPath: "/finanz/Ausgangsrechnungen/2025"
    property var standardFolders: ["01", "02", "03", "04", "05"]
    property var standardFoldersFiltered: ["01", "02", "03", "04", "05"]
    property var userFolders: ["myFolder", "myOtherFolder"]
    property var files: ["Rechnung_001.pdf", "Angebot_Alpha.docx", "Note.md"]
    property int maxVerticalParents: 4
    property int verticalParentSpacing: 6

    // Browser visibility
    property bool projectsBrowserVisible: true
    property bool templatesBrowserVisible: true



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

    function setCwp(path) {
        cwp = path
        updateSubProjects()
    }

    function updateSubProjects() {
        var query = searchText.trim()
        if (query.length === 0) {
            subProjects = demoData.childrenOf(cwp)
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
        if (mode === "direct") {
            var directItems = demoData.childrenOf(cwp)
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

    function verticalProjectButtonStyle() {
        return projectButtonStyle === "largeIcon" ? "text" : projectButtonStyle
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
        setCwp(cwp)
        updateBrowserLayout()
    }
    
    property bool newSubprojectEditing: false
    property string newSubprojectDraft: ""
    // legacy layout properties removed
    property bool searchActive: false
    property string searchText: ""
    property bool level2SearchActive: false
    property string level2SearchText: ""
    property bool renameActive: false
    property string renameTargetPath: ""
    property string renameDraft: ""

    // legacy layout handlers removed
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
    // legacy search width handler removed
    onLevel2ButtonStyleChanged: scheduleLevel2LayoutUpdate()

    // legacy layout update functions removed

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
        var wantsFixedWidth = inRowLayout && isFolderBrowser && child.verticalView
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
                    color: projectsBrowserVisible ? theme.accentSecondary : theme.pill
                    border.color: projectsBrowserVisible ? theme.accentSecondaryBorder : theme.pillBorder
                    implicitWidth: 180
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Projects " + (projectsBrowserVisible ? "ON" : "OFF")
                        color: theme.text
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
                    color: templatesBrowserVisible ? theme.accentSecondary : theme.pill
                    border.color: templatesBrowserVisible ? theme.accentSecondaryBorder : theme.pillBorder
                    implicitWidth: 180
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Templates " + (templatesBrowserVisible ? "ON" : "OFF")
                        color: theme.text
                        font.pixelSize: baseFont
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: templatesBrowserVisible = !templatesBrowserVisible
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
            buttonStyle: projectButtonStyle
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
            onStyleChanged: projectButtonStyle = style
            onToggleSearch: window.searchActive = !window.searchActive
            onSearchTextChanged: {
                window.searchText = projectsBrowser.searchText
                window.updateSubProjects()
            }
            onSearchTextEdited: {
                window.searchText = value
                window.updateSubProjects()
            }
            onPathSegmentActivated: {
                var parts = cwp.split("/").filter(function(p){ return p.length > 0 })
                setCwp("/" + parts.slice(0, index + 1).join("/"))
            }
            onPathSelected: setCwp(path)
            onFolderActivated: {
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

        Rectangle {
            id: filesPane
            parent: floatingPool
            radius: 8
            color: "#333333"
            border.color: theme.pillBorder
            implicitWidth: 0
            implicitHeight: 0
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8
                Text {
                    text: "Files Panel"
                    color: theme.textMuted
                    font.pixelSize: baseFont
                }
                Repeater {
                    model: files
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        height: 36
                        radius: 6
                        color: theme.panelAlt
                        border.color: theme.pillBorder
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 12
                            text: modelData
                            color: theme.text
                            font.pixelSize: baseFont
                        }
                    }
                }
            }
        }

        /*
        RowLayout {
            visible: false
            anchors.fill: parent
            spacing: 12
            anchors.margins: 16

            Rectangle {
                id: leftProjectPanel
                visible: verticalProjectView
                Layout.preferredWidth: 320
                Layout.fillHeight: true
                radius: 8
                color: theme.panel
                border.color: theme.pillBorder
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        Row {
                            id: leftTopButtons
                            spacing: 6
                            Rectangle {
                                width: compactButtonHeight
                                height: compactButtonHeight
                                radius: 4
                                color: theme.pill
                                border.color: theme.accentSecondaryBorder
                                Text {
                                    anchors.centerIn: parent
                                    text: verticalProjectView ? "H" : "V"
                                    color: theme.text
                                    font.pixelSize: baseFont - 2
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: verticalProjectView = !verticalProjectView
                                }
                            }
                            Rectangle {
                                width: compactButtonHeight
                                height: compactButtonHeight
                                radius: 4
                                color: theme.pill
                                border.color: theme.pillBorder
                                Image {
                                    anchors.centerIn: parent
                                    source: iconSearch
                                    width: baseFont
                                    height: baseFont
                                    fillMode: Image.PreserveAspectFit
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        searchActive = !searchActive
                                    }
                                }
                            }
                            Repeater {
                                model: [
                                    { label: "t", style: "text" },
                                    { label: "k", style: "smallIcon" }
                                ]
                                delegate: Rectangle {
                                    width: compactButtonHeight
                                    height: compactButtonHeight
                                    radius: 4
                                    property bool isActive: projectButtonStyle === modelData.style
                                    color: isActive ? theme.accentSecondary : theme.pill
                                    border.color: isActive ? theme.accentSecondaryBorder : theme.pillBorder
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.label
                                        color: theme.text
                                        font.pixelSize: baseFont - 2
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: projectButtonStyle = modelData.style
                                    }
                                }
                            }
                            Rectangle {
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
                        }
                        Item { Layout.fillWidth: true }
                    }
                    Loader {
                        id: verticalSearchLoader
                        Layout.fillWidth: true
                        Layout.preferredHeight: searchActive ? compactButtonHeight : 0
                        visible: searchActive
                        sourceComponent: searchFieldComponent
                        onLoaded: {
                            searchInputRef = item.input
                            if (searchActive) {
                                item.input.forceActiveFocus()
                                item.input.selectAll()
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: verticalParentSpacing
                        Repeater {
                            model: visibleParentPaths()
                            delegate: ProjectButton {
                                width: parent.width
                                label: lastPathSegment(modelData)
                                    style: verticalProjectButtonStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                iconSource: iconFolder
                                fillColor: theme.pill
                                strokeColor: theme.pillBorder
                                textColor: theme.text
                                textSize: baseFont
                                renaming: false
                                renameEnabled: false
                                onActivate: {
                                    setCwp(modelData)
                                }
                            }
                        }
                    }
                        ProjectButton {
                        width: parent.width
                        label: lastPathSegment(cwp)
                        style: verticalProjectButtonStyle()
                        compactHeight: compactButtonHeight
                        largeHeight: largeButtonHeight
                        largePadding: largeButtonPadding
                        iconSmall: iconSizeSmall
                        iconLarge: iconSizeLarge
                        iconSource: iconFolder
                        fillColor: theme.accentPrimary
                        strokeColor: theme.accentPrimary
                        textColor: theme.accentPrimaryText
                        textSize: baseFont + 1
                        textBold: true
                        renaming: false
                        renameEnabled: false
                            textLeftInset: verticalProjectButtonStyle() === "text" ? 16 : 0
                        onActivate: {}
                    }
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: width
                        clip: true
                        Column {
                            width: parent.width
                            spacing: 6
                                Repeater {
                                    model: subProjects
                                    delegate: ProjectButton {
                                        x: 16
                                        width: parent.width - 16
                                    property string fullPath: modelData.indexOf("/") === 0 ? modelData : (cwp + "/" + modelData)
                                    label: displaySubprojectLabel(modelData)
                                    style: verticalProjectButtonStyle()
                                    compactHeight: compactButtonHeight
                                    largeHeight: largeButtonHeight
                                    largePadding: largeButtonPadding
                                    iconSmall: iconSizeSmall
                                    iconLarge: iconSizeLarge
                                    iconSource: iconFolder
                                    fillColor: theme.accentSecondary
                                    strokeColor: theme.accentSecondaryBorder
                                    textColor: theme.textSoft
                                    textSize: baseFont
                                    renaming: renameActive && renameTargetPath === fullPath
                                    renameEnabled: true
                                    renameText: renameDraft
                                        textLeftInset: verticalProjectButtonStyle() === "text" ? 16 : 0
                                    onRenameRequested: beginRename(fullPath)
                                    onRenameTextEdited: renameDraft = text
                                    onRenameAccepted: commitRename()
                                    onRenameCanceled: cancelRename()
                                    onActivate: {
                                        if (modelData.indexOf("/") === 0) {
                                            setCwp(modelData)
                                        } else {
                                            var newPath = cwp + "/" + modelData
                                            setCwp(newPath)
                                        }
                                        clearSearchAfterNavigate()
                                    }
                                }
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                id: rightContent
                visible: false
                Layout.fillWidth: false
                Layout.fillHeight: false
                Layout.preferredWidth: 0
                Layout.preferredHeight: 0
                Layout.minimumWidth: 0
                Layout.minimumHeight: 0
                spacing: 8

                // Project bar
                Rectangle {
                    visible: !verticalProjectView
                    Layout.fillWidth: true
                    Layout.preferredHeight: 0
                    radius: 8
                    color: theme.panel
                    border.color: theme.pillBorder
                    ColumnLayout {
                        id: projectBarContent
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                    RowLayout {
                        id: topProjectRow
                        Layout.fillWidth: true
                        Layout.preferredHeight: projectButtonStyle === "largeIcon" ? largeButtonHeight : compactButtonHeight
                        spacing: 6
                        onWidthChanged: scheduleLayoutUpdate()
                        Rectangle {
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: 4
                            color: theme.pill
                            border.color: theme.accentSecondaryBorder
                            Layout.alignment: Qt.AlignTop
                            Text {
                                anchors.centerIn: parent
                                text: verticalProjectView ? "H" : "V"
                                color: theme.text
                                font.pixelSize: baseFont - 2
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: verticalProjectView = !verticalProjectView
                            }
                        }
                        Item {
                            id: cwpHost
                            Layout.fillWidth: false
                            Layout.preferredHeight: projectButtonStyle === "largeIcon" ? largeButtonHeight : compactButtonHeight
                            Layout.minimumHeight: Layout.preferredHeight
                            Layout.preferredWidth: cwpPreferredWidth
                            clip: true
                            Row {
                                id: cwpRow
                                spacing: 6
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: cwpRow.implicitWidth <= cwpHost.width ? parent.left : undefined
                                anchors.right: cwpRow.implicitWidth <= cwpHost.width ? undefined : parent.right
                                onImplicitWidthChanged: scheduleLayoutUpdate()
                                Repeater {
                                    model: cwp.split("/").filter(function(p){ return p.length > 0 })
                                    delegate: ProjectButton {
                                        property bool isCurrent: index === cwp.split("/").filter(function(p){ return p.length > 0 }).length - 1
                                        label: displaySubprojectLabel(modelData)
                                        style: projectButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: isCurrent ? theme.accentPrimary : theme.pill
                                        strokeColor: isCurrent ? theme.accentPrimary : theme.pillBorder
                                        textColor: isCurrent ? theme.accentPrimaryText : theme.text
                                        textSize: baseFont + 1
                                        largeTextSize: baseFont - 1
                                        textBold: isCurrent
                                        largeTextBold: isCurrent
                                        renaming: false
                                        renameEnabled: false
                                        onActivate: {
                                            var parts = cwp.split("/").filter(function(p){ return p.length > 0 })
                                            var idx = index
                                            var newPath = "/" + parts.slice(0, idx + 1).join("/")
                                            setCwp(newPath)
                                        }
                                    }
                                }
                            }
                        }
                        Item {
                            id: topFlowHost
                            Layout.fillWidth: false
                            Layout.preferredHeight: projectButtonStyle === "largeIcon" ? largeButtonHeight : compactButtonHeight
                            Layout.alignment: Qt.AlignTop
                            Layout.preferredWidth: flowPreferredWidth
                            visible: !flowOnSecondLine
                            onWidthChanged: scheduleLayoutUpdate()
                            Component.onCompleted: scheduleLayoutUpdate()
                            Row {
                                id: topSubprojectRow
                                spacing: 6
                                visible: !flowOnSecondLine
                                onImplicitWidthChanged: scheduleLayoutUpdate()
                                anchors.verticalCenter: parent.verticalCenter
                                Repeater {
                                    model: subProjects
                                    delegate: ProjectButton {
                                        property string fullPath: modelData.indexOf("/") === 0 ? modelData : (cwp + "/" + modelData)
                                        label: displaySubprojectLabel(modelData)
                                        style: projectButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: theme.accentSecondary
                                        strokeColor: theme.accentSecondaryBorder
                                        textColor: theme.textSoft
                                        textSize: baseFont
                                        largeTextSize: baseFont - 1
                                        renaming: renameActive && renameTargetPath === fullPath
                                        renameEnabled: true
                                        renameText: renameDraft
                                        onRenameRequested: beginRename(fullPath)
                                        onRenameTextEdited: renameDraft = text
                                        onRenameAccepted: commitRename()
                                        onRenameCanceled: cancelRename()
                                        onActivate: {
                                            if (modelData.indexOf("/") === 0) {
                                                setCwp(modelData)
                                            } else {
                                                var newPath = cwp + "/" + modelData
                                                setCwp(newPath)
                                            }
                                            clearSearchAfterNavigate()
                                        }
                                    }
                                }
                                Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? largeButtonHeight : compactButtonHeight
                                    color: theme.accentSecondary
                                    border.color: theme.accentSecondaryBorder
                                    visible: !newSubprojectEditing
                                    clip: true
                                    implicitWidth: {
                                        var base = newProjectTextMeasureTop.width + 24
                                        if (projectButtonStyle === "smallIcon") {
                                            return Math.max(140, base + iconSizeSmall + 6)
                                        }
                                        if (projectButtonStyle === "largeIcon") {
                                            return Math.max(140, Math.max(iconSizeLarge, newProjectTextMeasureTop.width) + 20)
                                        }
                                        return Math.max(140, base)
                                    }
                                    Item {
                                        anchors.fill: parent
                                        visible: projectButtonStyle === "text"
                                        Text {
                                            anchors.centerIn: parent
                                            text: "new Subproject"
                                            color: theme.text
                                            font.pixelSize: baseFont
                                            elide: Text.ElideRight
                                            width: parent.width - 16
                                        }
                                    }
                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 6
                                        visible: projectButtonStyle === "smallIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeSmall
                                            height: iconSizeSmall
                                            fillMode: Image.PreserveAspectFit
                                        }
                                        Text {
                                            text: "new Subproject"
                                            color: theme.text
                                            font.pixelSize: baseFont
                                            elide: Text.ElideRight
                                        }
                                    }
                                    Column {
                                        anchors.centerIn: parent
                                        width: parent.width
                                        spacing: 2
                                        visible: projectButtonStyle === "largeIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeLarge
                                            height: iconSizeLarge
                                            fillMode: Image.PreserveAspectFit
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }
                                        Text {
                                            text: "new Subproject"
                                            color: theme.text
                                            font.pixelSize: baseFont - 1
                                            horizontalAlignment: Text.AlignHCenter
                                            elide: Text.ElideRight
                                            width: parent.width
                                        }
                                    }
                                    Text { id: newProjectTextMeasureTop; text: "new Subproject"; visible: false; font.pixelSize: baseFont }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            newSubprojectDraft = ""
                                            newSubprojectEditing = true
                                        }
                                    }
                                }
                                Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? (iconSizeLarge + 44) : 32
                                    color: theme.card
                                    border.color: theme.pillBorder
                                    visible: newSubprojectEditing
                                    implicitWidth: Math.max(220, (
                                        projectButtonStyle === "largeIcon" ? newSubprojectInputLarge.implicitWidth :
                                        (projectButtonStyle === "smallIcon" ? newSubprojectInputSmallIcon.implicitWidth : newSubprojectInputSmallText.implicitWidth)
                                    ) + 12)
                                    Column {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 4
                                        visible: projectButtonStyle === "largeIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeLarge
                                            height: iconSizeLarge
                                            fillMode: Image.PreserveAspectFit
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }
                                        TextField {
                                            id: newSubprojectInputLarge
                                            width: parent.width
                                            height: 24
                                            text: newSubprojectDraft
                                            placeholderText: "new Subproject"
                                            font.pixelSize: baseFont
                                            selectByMouse: true
                                            color: theme.text
                                            placeholderTextColor: theme.textMuted
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 6
                                            rightPadding: 6
                                            topPadding: 1
                                            bottomPadding: 0
                                            onTextChanged: newSubprojectDraft = text
                                            background: Rectangle {
                                                color: "transparent"
                                            }
                                            onVisibleChanged: {
                                                if (visible) {
                                                    text = newSubprojectDraft
                                                    forceActiveFocus()
                                                    selectAll()
                                                }
                                            }
                                            Keys.onReturnPressed: {
                                                if (createSubproject(text)) {
                                                    newSubprojectDraft = ""
                                                    newSubprojectEditing = false
                                                }
                                            }
                                            Keys.onEscapePressed: {
                                                newSubprojectDraft = ""
                                                newSubprojectEditing = false
                                            }
                                        }
                                    }
                                    Row {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 6
                                        visible: projectButtonStyle === "smallIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeSmall
                                            height: iconSizeSmall
                                            fillMode: Image.PreserveAspectFit
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        TextField {
                                            id: newSubprojectInputSmallIcon
                                            width: parent.width - iconSizeSmall - 6
                                            height: parent.height - 2
                                            text: newSubprojectDraft
                                            placeholderText: "new Subproject"
                                            font.pixelSize: baseFont
                                            selectByMouse: true
                                            color: theme.text
                                            placeholderTextColor: theme.textMuted
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 6
                                            rightPadding: 6
                                            topPadding: 1
                                            bottomPadding: 0
                                            onTextChanged: newSubprojectDraft = text
                                            background: Rectangle { color: "transparent" }
                                            onVisibleChanged: {
                                                if (visible) {
                                                    text = newSubprojectDraft
                                                    forceActiveFocus()
                                                    selectAll()
                                                }
                                            }
                                            Keys.onReturnPressed: {
                                                if (createSubproject(text)) {
                                                    newSubprojectDraft = ""
                                                    newSubprojectEditing = false
                                                }
                                            }
                                            Keys.onEscapePressed: {
                                                newSubprojectDraft = ""
                                                newSubprojectEditing = false
                                            }
                                        }
                                    }
                                    TextField {
                                        id: newSubprojectInputSmallText
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.leftMargin: 6
                                        anchors.rightMargin: 6
                                        height: parent.height - 2
                                        visible: projectButtonStyle === "text"
                                        text: newSubprojectDraft
                                        placeholderText: "new Subproject"
                                        font.pixelSize: baseFont
                                        selectByMouse: true
                                        color: theme.text
                                        placeholderTextColor: theme.textMuted
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 6
                                        rightPadding: 6
                                        topPadding: 1
                                        bottomPadding: 0
                                        onTextChanged: newSubprojectDraft = text
                                        background: Rectangle { color: "transparent" }
                                        onVisibleChanged: {
                                            if (visible) {
                                                text = newSubprojectDraft
                                                forceActiveFocus()
                                                selectAll()
                                            }
                                        }
                                        Keys.onReturnPressed: {
                                            if (createSubproject(text)) {
                                                newSubprojectDraft = ""
                                                newSubprojectEditing = false
                                            }
                                        }
                                        Keys.onEscapePressed: {
                                            newSubprojectDraft = ""
                                            newSubprojectEditing = false
                                        }
                                    }
                                }
                            }
                        }
                        Item {
                            id: searchHost
                            Layout.fillWidth: false
                            Layout.preferredWidth: searchWidth
                            Layout.minimumWidth: 0
                            Layout.maximumWidth: 520
                            Layout.preferredHeight: compactButtonHeight
                            Layout.alignment: Qt.AlignTop | Qt.AlignRight
                            width: searchWidth
                            height: compactButtonHeight
                            clip: true
                            Behavior on Layout.preferredWidth {
                                NumberAnimation { duration: 320; easing.type: Easing.OutCubic }
                            }
                            Loader {
                                id: horizontalSearchLoader
                                anchors.fill: parent
                                sourceComponent: searchFieldComponent
                                onLoaded: {
                                    searchInputRef = item.input
                                    if (searchActive) {
                                        item.input.forceActiveFocus()
                                        item.input.selectAll()
                                    }
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }
                    RowLayout {
                        id: bottomProjectRow
                        Layout.fillWidth: true
                        spacing: 6
                        visible: flowOnSecondLine
                        implicitHeight: bottomSubprojectFlow.implicitHeight
                        Layout.preferredHeight: flowOnSecondLine ? bottomSubprojectFlow.implicitHeight : 0
                        Item {
                            id: bottomFlowHost
                            Layout.fillWidth: true
                            Layout.preferredHeight: flowOnSecondLine ? bottomSubprojectFlow.implicitHeight : 0
                            onWidthChanged: updateFlowPlacement()
                            Flow {
                                id: bottomSubprojectFlow
                                width: bottomFlowHost.width
                                height: implicitHeight
                                spacing: 6
                                flow: Flow.LeftToRight
                                layoutDirection: Qt.LeftToRight
                                Repeater {
                                    model: subProjects
                                    delegate: ProjectButton {
                                        property string fullPath: modelData.indexOf("/") === 0 ? modelData : (cwp + "/" + modelData)
                                        label: displaySubprojectLabel(modelData)
                                        style: projectButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: theme.accentSecondary
                                        strokeColor: theme.accentSecondaryBorder
                                        textColor: theme.textSoft
                                        textSize: baseFont
                                        largeTextSize: baseFont - 1
                                        renaming: renameActive && renameTargetPath === fullPath
                                        renameEnabled: true
                                        renameText: renameDraft
                                        onRenameRequested: beginRename(fullPath)
                                        onRenameTextEdited: renameDraft = text
                                        onRenameAccepted: commitRename()
                                        onRenameCanceled: cancelRename()
                                        onActivate: {
                                            if (modelData.indexOf("/") === 0) {
                                                setCwp(modelData)
                                            } else {
                                                var newPath = cwp + "/" + modelData
                                                setCwp(newPath)
                                            }
                                            clearSearchAfterNavigate()
                                        }
                                    }
                                }
                                Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? largeButtonHeight : compactButtonHeight
                                    color: theme.accentSecondary
                                    border.color: theme.accentSecondaryBorder
                                    visible: !newSubprojectEditing
                                    clip: true
                                    implicitWidth: {
                                        var base = newProjectTextMeasureBottom.width + 24
                                        if (projectButtonStyle === "smallIcon") {
                                            return Math.max(140, base + iconSizeSmall + 6)
                                        }
                                        if (projectButtonStyle === "largeIcon") {
                                            return Math.max(140, Math.max(iconSizeLarge, newProjectTextMeasureBottom.width) + 20)
                                        }
                                        return Math.max(140, base)
                                    }
                                    Item {
                                        anchors.fill: parent
                                        visible: projectButtonStyle === "text"
                                        Text {
                                            anchors.centerIn: parent
                                            text: "new Subproject"
                                            color: theme.text
                                            font.pixelSize: baseFont
                                            elide: Text.ElideRight
                                            width: parent.width - 16
                                        }
                                    }
                                    Row {
                                        anchors.centerIn: parent
                                        spacing: 6
                                        visible: projectButtonStyle === "smallIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeSmall
                                            height: iconSizeSmall
                                            fillMode: Image.PreserveAspectFit
                                        }
                                        Text {
                                            text: "new Subproject"
                                            color: theme.text
                                            font.pixelSize: baseFont
                                            elide: Text.ElideRight
                                        }
                                    }
                                    Column {
                                        anchors.centerIn: parent
                                        width: parent.width
                                        spacing: 2
                                        visible: projectButtonStyle === "largeIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeLarge
                                            height: iconSizeLarge
                                            fillMode: Image.PreserveAspectFit
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }
                                        Text {
                                            text: "new Subproject"
                                            color: theme.text
                                            font.pixelSize: baseFont - 1
                                            horizontalAlignment: Text.AlignHCenter
                                            elide: Text.ElideRight
                                            width: parent.width
                                        }
                                    }
                                    Text { id: newProjectTextMeasureBottom; text: "new Subproject"; visible: false; font.pixelSize: baseFont }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            newSubprojectDraft = ""
                                            newSubprojectEditing = true
                                        }
                                    }
                                }
                                Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? (iconSizeLarge + 44) : 32
                                    color: theme.card
                                    border.color: theme.pillBorder
                                    visible: newSubprojectEditing
                                    implicitWidth: Math.max(220, (
                                        projectButtonStyle === "largeIcon" ? newSubprojectInputBottomLarge.implicitWidth :
                                        (projectButtonStyle === "smallIcon" ? newSubprojectInputBottomSmallIcon.implicitWidth : newSubprojectInputBottomSmallText.implicitWidth)
                                    ) + 12)
                                    Column {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 4
                                        visible: projectButtonStyle === "largeIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeLarge
                                            height: iconSizeLarge
                                            fillMode: Image.PreserveAspectFit
                                            anchors.horizontalCenter: parent.horizontalCenter
                                        }
                                        TextField {
                                            id: newSubprojectInputBottomLarge
                                            width: parent.width
                                            height: 24
                                            text: newSubprojectDraft
                                            placeholderText: "new Subproject"
                                            font.pixelSize: baseFont
                                            selectByMouse: true
                                            color: theme.text
                                            placeholderTextColor: theme.textMuted
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 6
                                            rightPadding: 6
                                            topPadding: 1
                                            bottomPadding: 0
                                            onTextChanged: newSubprojectDraft = text
                                            background: Rectangle {
                                                color: "transparent"
                                            }
                                            onVisibleChanged: {
                                                if (visible) {
                                                    text = newSubprojectDraft
                                                    forceActiveFocus()
                                                    selectAll()
                                                }
                                            }
                                            Keys.onReturnPressed: {
                                                if (createSubproject(text)) {
                                                    newSubprojectDraft = ""
                                                    newSubprojectEditing = false
                                                }
                                            }
                                            Keys.onEscapePressed: {
                                                newSubprojectDraft = ""
                                                newSubprojectEditing = false
                                            }
                                        }
                                    }
                                    Row {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 6
                                        visible: projectButtonStyle === "smallIcon"
                                        Image {
                                            source: iconFolder
                                            width: iconSizeSmall
                                            height: iconSizeSmall
                                            fillMode: Image.PreserveAspectFit
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        TextField {
                                            id: newSubprojectInputBottomSmallIcon
                                            width: parent.width - iconSizeSmall - 6
                                            height: parent.height - 2
                                            text: newSubprojectDraft
                                            placeholderText: "new Subproject"
                                            font.pixelSize: baseFont
                                            selectByMouse: true
                                            color: theme.text
                                            placeholderTextColor: theme.textMuted
                                            verticalAlignment: Text.AlignVCenter
                                            leftPadding: 6
                                            rightPadding: 6
                                            topPadding: 1
                                            bottomPadding: 0
                                            onTextChanged: newSubprojectDraft = text
                                            background: Rectangle { color: "transparent" }
                                            onVisibleChanged: {
                                                if (visible) {
                                                    text = newSubprojectDraft
                                                    forceActiveFocus()
                                                    selectAll()
                                                }
                                            }
                                            Keys.onReturnPressed: {
                                                if (createSubproject(text)) {
                                                    newSubprojectDraft = ""
                                                    newSubprojectEditing = false
                                                }
                                            }
                                            Keys.onEscapePressed: {
                                                newSubprojectDraft = ""
                                                newSubprojectEditing = false
                                            }
                                        }
                                    }
                                    TextField {
                                        id: newSubprojectInputBottomSmallText
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.leftMargin: 6
                                        anchors.rightMargin: 6
                                        height: parent.height - 2
                                        visible: projectButtonStyle === "text"
                                        text: newSubprojectDraft
                                        placeholderText: "new Subproject"
                                        font.pixelSize: baseFont
                                        selectByMouse: true
                                        color: theme.text
                                        placeholderTextColor: theme.textMuted
                                        verticalAlignment: Text.AlignVCenter
                                        leftPadding: 6
                                        rightPadding: 6
                                        topPadding: 1
                                        bottomPadding: 0
                                        onTextChanged: newSubprojectDraft = text
                                        background: Rectangle { color: "transparent" }
                                        onVisibleChanged: {
                                            if (visible) {
                                                text = newSubprojectDraft
                                                forceActiveFocus()
                                                selectAll()
                                            }
                                        }
                                        Keys.onReturnPressed: {
                                            if (createSubproject(text)) {
                                                newSubprojectDraft = ""
                                                newSubprojectEditing = false
                                            }
                                        }
                                        Keys.onEscapePressed: {
                                            newSubprojectDraft = ""
                                            newSubprojectEditing = false
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                Item {
                    id: rightButtonsHost
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.topMargin: 12
                    anchors.rightMargin: 12
                    visible: !verticalProjectView
                    width: rightButtonsWidth
                    height: topProjectRow.Layout.preferredHeight
                    clip: true
                    Row {
                        id: topRightButtons
                        anchors.right: parent.right
                        anchors.top: parent.top
                        spacing: 6
                        Component.onCompleted: {
                            rightButtonsWidth = topRightButtons.implicitWidth
                            scheduleLayoutUpdate()
                        }
                        Rectangle {
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: 4
                            color: theme.pill
                            border.color: theme.pillBorder
                            Image {
                                anchors.centerIn: parent
                                source: iconSearch
                                width: baseFont
                                height: baseFont
                                fillMode: Image.PreserveAspectFit
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    searchActive = !searchActive
                                }
                            }
                        }
                        Repeater {
                            model: [
                                { label: "t", icon: "", style: "text" },
                                { label: "G", icon: "", style: "largeIcon" },
                                { label: "k", icon: "", style: "smallIcon" }
                            ]
                            delegate: Rectangle {
                                width: compactButtonHeight
                                height: compactButtonHeight
                                radius: 4
                                property bool isActive: modelData.style !== "" && projectButtonStyle === modelData.style
                                color: isActive ? theme.accentSecondary : theme.pill
                                border.color: isActive ? theme.accentSecondaryBorder : theme.pillBorder
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        if (modelData.style !== "") {
                                            projectButtonStyle = modelData.style
                                        }
                                    }
                                }
                                Item {
                                    anchors.fill: parent
                                    visible: modelData.icon !== ""
                                    Column {
                                        anchors.centerIn: parent
                                        spacing: 1
                                        Image {
                                            source: modelData.icon
                                            width: baseFont
                                            height: baseFont
                                            fillMode: Image.PreserveAspectFit
                                        }
                                        Text {
                                            text: modelData.label
                                            color: theme.text
                                            font.pixelSize: baseFont - 6
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                    }
                                }
                                Text {
                                    anchors.centerIn: parent
                                    visible: modelData.icon === "" && modelData.label !== ""
                                    text: modelData.label
                                    color: theme.text
                                    font.pixelSize: baseFont - 2
                                }
                            }
                        }
                        Rectangle {
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
                    }
                }
            }

            RowLayout {
                id: verticalSecondLevelContent
                Layout.fillWidth: true
                Layout.fillHeight: false
                Layout.preferredHeight: systemPanel.implicitHeight
                spacing: 12
                visible: level2VerticalView
                Rectangle {
                    id: systemPanel
                    Layout.fillWidth: true
                    Layout.fillHeight: false
                    Layout.preferredHeight: systemPanel.implicitHeight
                    radius: 8
                    color: theme.panelAlt
                    border.color: theme.pillBorder
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            Row {
                                spacing: 6
                                Rectangle {
                                    width: compactButtonHeight
                                    height: compactButtonHeight
                                    radius: 4
                                    color: theme.pill
                                    border.color: theme.accentSecondaryBorder
                                    Text {
                                        anchors.centerIn: parent
                                        text: level2VerticalView ? "H" : "V"
                                        color: theme.text
                                        font.pixelSize: baseFont - 2
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: level2VerticalView = !level2VerticalView
                                    }
                                }
                                Repeater {
                                    model: [
                                        { label: "t", style: "text" },
                                        { label: "k", style: "smallIcon" }
                                    ]
                                    delegate: Rectangle {
                                        width: compactButtonHeight
                                        height: compactButtonHeight
                                        radius: 4
                                        property bool isActive: standardButtonStyle === modelData.style
                                        color: isActive ? theme.accentSecondary : theme.pill
                                        border.color: isActive ? theme.accentSecondaryBorder : theme.pillBorder
                                        Text {
                                            anchors.centerIn: parent
                                            text: modelData.label
                                            color: theme.text
                                            font.pixelSize: baseFont - 2
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: standardButtonStyle = modelData.style
                                        }
                                    }
                                }
                            }
                            Item { Layout.fillWidth: true }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: verticalParentSpacing
                            Repeater {
                                model: visibleParentPathsFor(standardPath, systemPanel.height)
                                delegate: ProjectButton {
                                    width: parent.width
                                    label: lastPathSegment(modelData)
                                    style: standardButtonStyle
                                    compactHeight: compactButtonHeight
                                    largeHeight: largeButtonHeight
                                    largePadding: largeButtonPadding
                                    iconSmall: iconSizeSmall
                                    iconLarge: iconSizeLarge
                                    iconSource: iconFolder
                                    fillColor: theme.pill
                                    strokeColor: theme.pillBorder
                                    textColor: theme.text
                                    textSize: baseFont
                                    renaming: false
                                    renameEnabled: false
                                    onActivate: {
                                        standardPath = modelData
                                    }
                                }
                            }
                        }
                        ProjectButton {
                            width: parent.width
                            label: lastPathSegment(standardPath)
                            style: standardButtonStyle
                            compactHeight: compactButtonHeight
                            largeHeight: largeButtonHeight
                            largePadding: largeButtonPadding
                            iconSmall: iconSizeSmall
                            iconLarge: iconSizeLarge
                            iconSource: iconFolder
                            fillColor: theme.accentPrimary
                            strokeColor: theme.accentPrimary
                            textColor: theme.accentPrimaryText
                            textSize: baseFont + 1
                            textBold: true
                            renaming: false
                            renameEnabled: false
                            onActivate: {
                                standardPath = rootPathOf(standardPath)
                            }
                        }
                        Flickable {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            contentWidth: width
                            clip: true
                            Column {
                                width: parent.width
                                spacing: 6
                                Repeater {
                                    model: standardFolders
                                    delegate: ProjectButton {
                                        x: 16
                                        width: parent.width - 16
                                        label: modelData
                                        style: standardButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: theme.pill
                                        strokeColor: theme.pillBorder
                                        textColor: theme.textSoft
                                        textSize: baseFont
                                        renaming: false
                                        renameEnabled: false
                                        textLeftInset: standardButtonStyle === "text" ? 16 : 0
                                        onActivate: {
                                            var base = standardPath.endsWith("/") ? standardPath.slice(0, -1) : standardPath
                                            standardPath = base + "/" + modelData
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
            }

            // Standard folder bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 12 + standardTopRow.implicitHeight + (level2FlowOnSecondLine ? (8 + level2BottomRow.implicitHeight) : 0) + 12
                radius: 8
                color: theme.panelAlt
                border.color: theme.pillBorder
                visible: !level2VerticalView
                ColumnLayout {
                    id: standardBarContent
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    RowLayout {
                        id: standardTopRow
                        Layout.fillWidth: true
                        spacing: 10
                        onWidthChanged: scheduleLevel2LayoutUpdate()
                        Rectangle {
                            id: level2ToggleButton
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: 4
                            color: theme.pill
                            border.color: theme.accentSecondaryBorder
                            Text {
                                anchors.centerIn: parent
                                text: level2VerticalView ? "H" : "V"
                                color: theme.text
                                font.pixelSize: baseFont - 2
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: level2VerticalView = !level2VerticalView
                            }
                        }
                        Item {
                            id: level2PathHost
                            Layout.fillWidth: false
                            Layout.preferredWidth: level2PathPreferredWidth
                            Layout.preferredHeight: compactButtonHeight
                            clip: true
                            Row {
                                id: standardPathRow
                                spacing: 6
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: standardPathRow.implicitWidth <= level2PathHost.width ? parent.left : undefined
                                anchors.right: standardPathRow.implicitWidth <= level2PathHost.width ? undefined : parent.right
                                onImplicitWidthChanged: scheduleLevel2LayoutUpdate()
                                Repeater {
                                    model: standardPath.split("/").filter(function(p){ return p.length > 0 })
                                    delegate: ProjectButton {
                                        property bool isCurrent: index === standardPath.split("/").filter(function(p){ return p.length > 0 }).length - 1
                                        label: modelData
                                        style: level2ButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: isCurrent ? theme.accentPrimary : theme.pill
                                        strokeColor: isCurrent ? theme.accentPrimary : theme.pillBorder
                                        textColor: isCurrent ? theme.accentPrimaryText : theme.text
                                        textSize: baseFont
                                        renaming: false
                                        renameEnabled: false
                                        onActivate: {
                                            var parts = standardPath.split("/").filter(function(p){ return p.length > 0 })
                                            var idx = index
                                            standardPath = "/" + parts.slice(0, idx + 1).join("/")
                                        }
                                    }
                                }
                            }
                        }
                        Item {
                            id: level2TopFlowHost
                            Layout.fillWidth: false
                            Layout.preferredWidth: level2FlowPreferredWidth
                            Layout.preferredHeight: compactButtonHeight
                            Layout.alignment: Qt.AlignTop
                            visible: !level2FlowOnSecondLine
                            onWidthChanged: scheduleLevel2LayoutUpdate()
                            Row {
                                id: level2TopFoldersRow
                                spacing: 6
                                onImplicitWidthChanged: scheduleLevel2LayoutUpdate()
                                Repeater {
                                    model: standardFolders
                                    delegate: ProjectButton {
                                        label: modelData
                                        style: level2ButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: theme.pill
                                        strokeColor: theme.pillBorder
                                        textColor: theme.textSoft
                                        textSize: baseFont
                                        renaming: false
                                        renameEnabled: false
                                        onActivate: {
                                            var base = standardPath.endsWith("/") ? standardPath.slice(0, -1) : standardPath
                                            standardPath = base + "/" + modelData
                                        }
                                    }
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Row {
                            id: level2RightButtons
                            Layout.preferredWidth: level2RightButtons.implicitWidth
                            Layout.minimumWidth: level2RightButtons.implicitWidth
                            Layout.maximumWidth: level2RightButtons.implicitWidth
                            spacing: 6
                            Component.onCompleted: {
                                level2RightButtonsWidth = level2RightButtons.implicitWidth
                                scheduleLevel2LayoutUpdate()
                            }
                            onImplicitWidthChanged: {
                                level2RightButtonsWidth = level2RightButtons.implicitWidth
                                scheduleLevel2LayoutUpdate()
                            }
                            Rectangle {
                                width: compactButtonHeight
                                height: compactButtonHeight
                                radius: 4
                                color: theme.pill
                                border.color: theme.pillBorder
                                Image {
                                    anchors.centerIn: parent
                                    source: iconSearch
                                    width: baseFont
                                    height: baseFont
                                    fillMode: Image.PreserveAspectFit
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: searchActive = !searchActive
                                }
                            }
                            Repeater {
                                model: [
                                    { label: "t", style: "text" },
                                    { label: "G", style: "largeIcon" },
                                    { label: "k", style: "smallIcon" }
                                ]
                                delegate: Rectangle {
                                    width: compactButtonHeight
                                    height: compactButtonHeight
                                    radius: 4
                                    property bool isActive: level2ButtonStyle === modelData.style
                                    color: isActive ? theme.accentSecondary : theme.pill
                                    border.color: isActive ? theme.accentSecondaryBorder : theme.pillBorder
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.label
                                        color: theme.text
                                        font.pixelSize: baseFont - 2
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: level2ButtonStyle = modelData.style
                                    }
                                }
                            }
                            Rectangle {
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
                        }
                    }
                    RowLayout {
                        id: level2BottomRow
                        Layout.fillWidth: true
                        spacing: 6
                        visible: level2FlowOnSecondLine
                        implicitHeight: level2BottomFoldersFlow.implicitHeight
                        Layout.preferredHeight: level2FlowOnSecondLine ? level2BottomFoldersFlow.implicitHeight : 0
                        Item {
                            id: level2BottomFlowHost
                            Layout.fillWidth: true
                            Layout.preferredHeight: level2FlowOnSecondLine ? level2BottomFoldersFlow.implicitHeight : 0
                            onWidthChanged: scheduleLevel2LayoutUpdate()
                            Flow {
                                id: level2BottomFoldersFlow
                                width: level2BottomFlowHost.width
                                height: implicitHeight
                                spacing: 6
                                flow: Flow.LeftToRight
                                layoutDirection: Qt.LeftToRight
                                Repeater {
                                    model: standardFolders
                                    delegate: ProjectButton {
                                        label: modelData
                                        style: level2ButtonStyle
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                        iconSource: iconFolder
                                        fillColor: theme.pill
                                        strokeColor: theme.pillBorder
                                        textColor: theme.textSoft
                                        textSize: baseFont
                                        renaming: false
                                        renameEnabled: false
                                        onActivate: {
                                            var base = standardPath.endsWith("/") ? standardPath.slice(0, -1) : standardPath
                                            standardPath = base + "/" + modelData
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Files area
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 8
                color: theme.card
                border.color: theme.pillBorder
                visible: true
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Text {
                        text: "Files (Roentgen view placeholder)"
                        color: theme.textMuted
                        font.pixelSize: baseFont
                    }

                    Repeater {
                        model: files
                        delegate: Rectangle {
                            Layout.fillWidth: true
                            height: 36
                            radius: 6
                            color: theme.panelAlt
                            border.color: theme.pillBorder
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left
                                anchors.leftMargin: 12
                                text: modelData
                                color: theme.text
                                font.pixelSize: baseFont
                            }
                        }
                    }
                }
            }
        }
        */
    }
}

