import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    width: 1400
    height: 900
    visible: true
    title: "Scope - MyOS GUI Stub"

    property int baseFont: Math.max(14, Qt.application.font.pixelSize + 2)
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
    property var searchInputRef: null
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
        property color textMuted: darkTheme ? "#c9ccd7" : "#3b4152"
        property color textSoft: darkTheme ? "#cfd3df" : "#2b3140"
        property color highlight: accentPrimary
    }

    property string cwp: "/Projekte/Haus/Dach"
    property var subProjects: []
    property string standardPath: "/finanz/Ausgangsrechnungen/2025"
    property var standardFolders: ["01", "02", "03", "04", "05"]
    property var userFolders: ["myFolder", "myOtherFolder"]
    property var files: ["Rechnung_001.pdf", "Angebot_Alpha.docx", "Note.md"]

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

    property int maxVerticalParents: 4
    property int verticalParentSpacing: 6

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
        var approxNeeded = parents.length * (compactButtonHeight + verticalParentSpacing)
        var reserve = (compactButtonHeight + verticalParentSpacing) * 6
        if (leftProjectPanel && (approxNeeded + reserve) > leftProjectPanel.height) {
            return parents.slice(Math.max(0, parents.length - maxVerticalParents))
        }
        return parents
    }

    function createSubproject(name) {
        var trimmed = name.trim().replace(/\s+/g, " ")
        if (trimmed.length === 0) return false
        if (demoData.addChild(cwp, trimmed)) {
            setCwp(cwp)
            updateFlowPlacement()
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
        rightButtonsWidth = topRightButtons ? topRightButtons.implicitWidth : rightButtonsWidth
        searchWidth = searchActive ? 520 : 0
        topButtonsWidth = rightButtonsWidth + searchWidth + 6
        setCwp(cwp)
        updateFlowPlacement()
    }
    property bool newSubprojectEditing: false
    property string newSubprojectDraft: ""
    property bool flowOnSecondLine: false
    property real availableTopWidth: 0
    property real cwpPreferredWidth: 0
    property real flowPreferredWidth: 0
    property bool layoutUpdatePending: false
    property real rightButtonsWidth: 0
    property real searchWidth: 0
    property real topButtonsWidth: 0
    property bool searchActive: false
    property string searchText: ""
    property bool renameActive: false
    property string renameTargetPath: ""
    property string renameDraft: ""

    onSubProjectsChanged: updateFlowPlacement()
    onNewSubprojectEditingChanged: updateFlowPlacement()
    onProjectButtonStyleChanged: {
        rightButtonsWidth = topRightButtons ? topRightButtons.implicitWidth : rightButtonsWidth
        topButtonsWidth = rightButtonsWidth + searchWidth + 6
        scheduleLayoutUpdate()
    }
    onSearchTextChanged: updateSubProjects()
    onSearchActiveChanged: {
        searchWidth = searchActive ? 520 : 0
        rightButtonsWidth = topRightButtons ? topRightButtons.implicitWidth : rightButtonsWidth
        topButtonsWidth = rightButtonsWidth + searchWidth + 6
        if (!searchActive) {
            searchText = ""
        } else {
            Qt.callLater(function() {
                if (searchInputRef) {
                    searchInputRef.forceActiveFocus()
                    searchInputRef.selectAll()
                }
            })
        }
        scheduleLayoutUpdate()
    }
    onSearchWidthChanged: {
        topButtonsWidth = rightButtonsWidth + searchWidth + 6
        scheduleLayoutUpdate()
    }

    function scheduleLayoutUpdate() {
        if (layoutUpdatePending) return
        layoutUpdatePending = true
        Qt.callLater(function() {
            layoutUpdatePending = false
            updateFlowPlacement()
        })
    }

    function updateFlowPlacement() {
        if (!topSubprojectRow || !topProjectRow || !topRightButtons || !cwpRow) return
        var available = topProjectRow.width - topButtonsWidth - (topProjectRow.spacing * 2)
        if (available < 0) available = 0
        if (availableTopWidth !== available) {
            availableTopWidth = available
        }
        if (available === 0) {
            if (!flowOnSecondLine) flowOnSecondLine = true
            if (cwpPreferredWidth !== cwpRow.implicitWidth) cwpPreferredWidth = cwpRow.implicitWidth
            if (flowPreferredWidth !== 0) flowPreferredWidth = 0
            return
        }
        var shouldWrap = (cwpRow.implicitWidth + topSubprojectRow.implicitWidth) > available
        if (flowOnSecondLine !== shouldWrap) flowOnSecondLine = shouldWrap
        if (shouldWrap) {
            if (cwpPreferredWidth !== available) cwpPreferredWidth = available
            if (flowPreferredWidth !== 0) flowPreferredWidth = 0
        } else {
            var newCwp = Math.min(cwpRow.implicitWidth, available - topSubprojectRow.implicitWidth)
            var newFlow = Math.max(0, available - newCwp)
            if (cwpPreferredWidth !== newCwp) cwpPreferredWidth = newCwp
            if (flowPreferredWidth !== newFlow) flowPreferredWidth = newFlow
        }
    }

    Component {
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

        RowLayout {
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
                                    Text {
                                        anchors.centerIn: parent
                                        text: modelData.label
                                        color: theme.text
                                        font.pixelSize: baseFont - 2
                                    }
                                }
                            }
                            Rectangle {
                                width: compactButtonHeight
                                height: compactButtonHeight
                                radius: 4
                                color: theme.pill
                                border.color: theme.pillBorder
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
                                style: "text"
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
                        style: "text"
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
                                    width: parent.width
                                    property string fullPath: modelData.indexOf("/") === 0 ? modelData : (cwp + "/" + modelData)
                                    label: displaySubprojectLabel(modelData)
                                    style: "text"
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
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 8

                // Project bar
                Rectangle {
                    visible: !verticalProjectView
                    Layout.fillWidth: true
                    Layout.preferredHeight: 12 + topProjectRow.implicitHeight + (flowOnSecondLine ? (8 + bottomProjectRow.implicitHeight) : 0) + 12
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

            // Standard folder bar
            Rectangle {
                Layout.fillWidth: true
                height: 56
                radius: 8
                color: theme.panelAlt
                border.color: theme.pillBorder
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 10
                    Text {
                        text: standardPath + " /"
                        color: theme.textMuted
                        font.pixelSize: baseFont + 2
                        Layout.fillWidth: true
                        elide: Text.ElideLeft
                    }
                    Repeater {
                        model: standardFolders
                        delegate: Rectangle {
                            radius: 6
                            height: 28
                            color: theme.pill
                            border.color: theme.pillBorder
                            Text {
                                anchors.centerIn: parent
                                text: modelData
                                color: theme.textSoft
                                font.pixelSize: baseFont
                            }
                            implicitWidth: 48
                        }
                    }
                    Rectangle {
                        radius: 6
                        height: 28
                        color: theme.action
                        border.color: theme.actionBorder
                        Text {
                            anchors.centerIn: parent
                            text: "new Standardfolder"
                            color: theme.text
                            font.pixelSize: baseFont - 1
                        }
                        implicitWidth: 160
                    }
                }
            }

            // Free folders bar
            Rectangle {
                Layout.fillWidth: true
                height: 48
                radius: 8
                color: theme.panelAlt2
                border.color: theme.pillBorder
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 10
                    Repeater {
                        model: userFolders
                        delegate: Rectangle {
                            radius: 6
                            height: 26
                            color: theme.pill
                            border.color: theme.pillBorder
                            Text {
                                anchors.centerIn: parent
                                text: modelData
                                color: theme.textSoft
                                font.pixelSize: baseFont - 1
                            }
                            implicitWidth: 90
                        }
                    }
                    Rectangle {
                        radius: 6
                        height: 26
                        color: theme.action
                        border.color: theme.actionBorder
                        Text {
                            anchors.centerIn: parent
                            text: "new Folder"
                            color: theme.text
                            font.pixelSize: baseFont - 1
                        }
                        implicitWidth: 110
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
    }
}
}
