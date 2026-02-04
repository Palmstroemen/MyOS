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
    property int iconSizeSmall: Math.round(baseFont * 1.5)
    property int iconSizeLarge: 64
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
    }

    function setCwp(path) {
        cwp = path
        subProjects = demoData.childrenOf(path)
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

    Component.onCompleted: {
        Qt.application.windowIcon = Qt.resolvedUrl(iconFolder)
        rightButtonsWidth = topRightButtons ? topRightButtons.implicitWidth : rightButtonsWidth
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

    onSubProjectsChanged: updateFlowPlacement()
    onNewSubprojectEditingChanged: updateFlowPlacement()
    onProjectButtonStyleChanged: {
        rightButtonsWidth = topRightButtons ? topRightButtons.implicitWidth : rightButtonsWidth
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
        var available = topProjectRow.width - topRightButtons.implicitWidth - (topProjectRow.spacing * 2)
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

    Rectangle {
        anchors.fill: parent
        color: theme.bg

        ColumnLayout {
            anchors.fill: parent
            spacing: 8
            anchors.margins: 16

            // Project bar
            Rectangle {
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
                        Layout.preferredHeight: projectButtonStyle === "largeIcon" ? (iconSizeLarge + 24) : 32
                        spacing: 6
                        onWidthChanged: scheduleLayoutUpdate()
                        Item {
                            id: cwpHost
                            Layout.fillWidth: false
                            Layout.preferredHeight: projectButtonStyle === "largeIcon" ? (iconSizeLarge + 24) : 32
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
                                    delegate: Rectangle {
                                        radius: 6
                                        property bool isCurrent: index === cwp.split("/").filter(function(p){ return p.length > 0 }).length - 1
                                        property bool isLarge: projectButtonStyle === "largeIcon"
                                        height: isLarge ? (iconSizeLarge + 24) : 30
                                        color: isCurrent ? theme.accentPrimary : theme.pill
                                        border.color: isCurrent ? theme.accentPrimary : theme.pillBorder
                                        implicitWidth: {
                                            var base = textMeasure.width + 20
                                            if (projectButtonStyle === "smallIcon") {
                                                return Math.max(60, base + iconSizeSmall + 6)
                                            }
                                            if (projectButtonStyle === "largeIcon") {
                                                return Math.max(60, Math.max(iconSizeLarge, textMeasure.width) + 20)
                                            }
                                            return Math.max(60, base)
                                        }
                                        Item {
                                            anchors.fill: parent
                                            visible: projectButtonStyle === "text"
                                            Text {
                                                anchors.centerIn: parent
                                                text: modelData
                                                color: isCurrent ? theme.accentPrimaryText : theme.text
                                                font.pixelSize: baseFont + 1
                                                font.bold: isCurrent
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
                                                text: modelData
                                                color: isCurrent ? theme.accentPrimaryText : theme.text
                                                font.pixelSize: baseFont + 1
                                                font.bold: isCurrent
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
                                                text: modelData
                                                color: isCurrent ? theme.accentPrimaryText : theme.text
                                                font.pixelSize: baseFont - 1
                                                font.bold: isCurrent
                                                horizontalAlignment: Text.AlignHCenter
                                                width: parent.width
                                            }
                                        }
                                        Text { id: textMeasure; text: modelData; visible: false; font.pixelSize: baseFont + 1 }
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                var parts = cwp.split("/").filter(function(p){ return p.length > 0 })
                                                var idx = index
                                                var newPath = "/" + parts.slice(0, idx + 1).join("/")
                                                setCwp(newPath)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Item {
                            id: topFlowHost
                            Layout.fillWidth: false
                            Layout.preferredHeight: projectButtonStyle === "largeIcon" ? (iconSizeLarge + 24) : 32
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
                                delegate: Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? (iconSizeLarge + 24) : 32
                                    color: theme.accentSecondary
                                    border.color: theme.accentSecondaryBorder
                                    implicitWidth: {
                                        var base = textItem.width + 24
                                        if (projectButtonStyle === "smallIcon") {
                                            return Math.max(80, base + iconSizeSmall + 6)
                                        }
                                        if (projectButtonStyle === "largeIcon") {
                                            return Math.max(80, Math.max(iconSizeLarge, textItem.width) + 20)
                                        }
                                        return Math.max(80, base)
                                    }
                                    Item {
                                        anchors.fill: parent
                                        visible: projectButtonStyle === "text"
                                        Text {
                                            anchors.centerIn: parent
                                            text: modelData
                                            color: theme.textSoft
                                            font.pixelSize: baseFont
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
                                            text: modelData
                                            color: theme.textSoft
                                            font.pixelSize: baseFont
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
                                            text: modelData
                                            color: theme.textSoft
                                            font.pixelSize: baseFont - 1
                                            horizontalAlignment: Text.AlignHCenter
                                            width: parent.width
                                        }
                                    }
                                    Text { id: textItem; text: modelData; visible: false; font.pixelSize: baseFont }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            var newPath = cwp + "/" + modelData
                                            setCwp(newPath)
                                        }
                                    }
                                }
                                }
                                Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? (iconSizeLarge + 24) : 32
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
                                    delegate: Rectangle {
                                        radius: 6
                                        property bool isLarge: projectButtonStyle === "largeIcon"
                                        height: isLarge ? (iconSizeLarge + 24) : 32
                                        color: theme.accentSecondary
                                        border.color: theme.accentSecondaryBorder
                                        implicitWidth: {
                                            var base = textItem.width + 24
                                            if (projectButtonStyle === "smallIcon") {
                                                return Math.max(80, base + iconSizeSmall + 6)
                                            }
                                            if (projectButtonStyle === "largeIcon") {
                                                return Math.max(80, Math.max(iconSizeLarge, textItem.width) + 20)
                                            }
                                            return Math.max(80, base)
                                        }
                                        Item {
                                            anchors.fill: parent
                                            visible: projectButtonStyle === "text"
                                            Text {
                                                anchors.centerIn: parent
                                                text: modelData
                                                color: theme.textSoft
                                                font.pixelSize: baseFont
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
                                                text: modelData
                                                color: theme.textSoft
                                                font.pixelSize: baseFont
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
                                            text: modelData
                                            color: theme.textSoft
                                            font.pixelSize: baseFont - 1
                                            horizontalAlignment: Text.AlignHCenter
                                            width: parent.width
                                        }
                                    }
                                        Text { id: textItem; text: modelData; visible: false; font.pixelSize: baseFont }
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                var newPath = cwp + "/" + modelData
                                                setCwp(newPath)
                                            }
                                        }
                                    }
                                }
                                Rectangle {
                                    radius: 6
                                    property bool isLarge: projectButtonStyle === "largeIcon"
                                    height: isLarge ? (iconSizeLarge + 24) : 32
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
                    width: rightButtonsWidth
                    height: topProjectRow.Layout.preferredHeight
                    clip: true
                    Row {
                        id: topRightButtons
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 6
                        Component.onCompleted: {
                            rightButtonsWidth = topRightButtons.implicitWidth
                            scheduleLayoutUpdate()
                        }
                        Repeater {
                            model: [
                                { label: "", icon: iconSearch, style: "" },
                                { label: "t", icon: "", style: "text" },
                                { label: "k", icon: "", style: "smallIcon" },
                                { label: "G", icon: "", style: "largeIcon" }
                            ]
                            delegate: Rectangle {
                                width: 30
                                height: 30
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
                            height: 32
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
