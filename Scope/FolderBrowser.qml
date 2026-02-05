import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property int horizontalPreferredWidth: 640
    property int verticalPreferredWidth: 320
    property int horizontalPreferredHeight: compactButtonHeight * 2 + (searchActive ? (compactButtonHeight + 8) : 0) + 24
    property int verticalPreferredHeight: 360
    implicitWidth: 0
    implicitHeight: mainColumn ? (mainColumn.implicitHeight + 24) : 0
    property string path: "/"
    property var folders: []
    property bool verticalView: false
    property string buttonStyle: "text"
    property bool allowLargeIcons: true
    property bool showModeToggle: true
    property bool showSearchToggle: false
    property bool showStyleToggle: true
    property bool showThemeToggle: false
    property bool searchActive: false
    property string searchText: ""
    property bool allowRename: false
    property string renameTargetPath: ""
    property string renameDraft: ""
    property int baseFont: 14
    property int compactButtonHeight: 32
    property int largeButtonHeight: 72
    property int largeButtonPadding: 6
    property int iconSizeSmall: 20
    property int iconSizeLarge: 48
    property int maxParents: 4
    property int verticalParentSpacing: 6
    property int indent: 0
    property string iconFolder: ""
    property string iconSearch: ""
    property color panelColor: "#1b1d26"
    property color panelBorderColor: "#3a4158"
    property color panelAltColor: "#151821"
    property color accentPrimary: "#524dbe"
    property color accentPrimaryText: "#ffffff"
    property color pill: "#2a2f40"
    property color pillBorder: "#3a4158"
    property color accentSecondary: "#3b476b"
    property color accentSecondaryBorder: "#58648a"
    property color text: "#e6e6e6"
    property color textSoft: "#cfd3df"
    property color textMuted: "#c9ccd7"
    property color card: "#0f1117"

    signal pathSegmentActivated(int index)
    signal pathSelected(string path)
    signal folderActivated(string name)
    signal toggleMode()
    signal toggleSearch()
    signal toggleTheme()
    signal styleChanged(string style)
    signal renameRequested(string fullPath)
    signal renameTextEdited(string text)
    signal renameAccepted()
    signal renameCanceled()
    signal searchTextEdited(string value)

    property bool flowOnSecondLine: false
    property bool layoutUpdatePending: false

    function effectiveStyle() {
        if (!allowLargeIcons && buttonStyle === "largeIcon") return "text"
        return buttonStyle
    }


    function pathParts() {
        return path.split("/").filter(function(p){ return p.length > 0 })
    }

    function parentPaths() {
        var parts = pathParts()
        var paths = []
        for (var i = 0; i < parts.length - 1; i++) {
            paths.push("/" + parts.slice(0, i + 1).join("/"))
        }
        return paths
    }

    function visibleParentPaths() {
        var parents = parentPaths()
        if (parents.length <= maxParents) return parents
        return parents.slice(Math.max(0, parents.length - maxParents))
    }

    function scheduleLayoutUpdate() {
        if (layoutUpdatePending) return
        layoutUpdatePending = true
        Qt.callLater(function() {
            updateFlowPlacement()
            layoutUpdatePending = false
        })
    }

    function updateFlowPlacement() {
        if (!topFoldersRow || !topRow || !rightButtonsRow || !pathRow) return
        var toggleWidth = (showModeToggle && modeToggleButton) ? modeToggleButton.width : 0
        var gapCount = showModeToggle ? 3 : 2
        var rightWidth = rightButtonsRow.implicitWidth
        var used = pathRow.implicitWidth + topFoldersRow.implicitWidth + rightWidth + toggleWidth + (topRow.spacing * gapCount)
        var slack = topRow.width - used
        var shouldWrap = slack < 20
        if (flowOnSecondLine !== shouldWrap) flowOnSecondLine = shouldWrap
    }


    Rectangle {
        anchors.fill: parent
        color: panelColor
        border.color: panelBorderColor
        radius: 8

        ColumnLayout {
            id: mainColumn
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            RowLayout { // HORIZONTAL VIEW: row 1 (path + folders + right buttons)
                id: topRow
                visible: !verticalView
                Layout.fillWidth: true
                Layout.preferredHeight: effectiveStyle() === "largeIcon" ? largeButtonHeight : compactButtonHeight
                spacing: 6
                onWidthChanged: scheduleLayoutUpdate()

                Rectangle {
                    id: modeToggleButton
                    visible: showModeToggle
                    width: compactButtonHeight
                    height: compactButtonHeight
                    radius: 4
                    color: pill
                    border.color: accentSecondaryBorder
                    Text {
                        anchors.centerIn: parent
                        text: verticalView ? "H" : "V"
                        color: text
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: toggleMode()
                    }
                }

                Item { // HORIZONTAL: path segment row (breadcrumbs)
                    id: pathHost
                    Layout.fillWidth: flowOnSecondLine
                    Layout.preferredWidth: flowOnSecondLine ? 0 : pathRow.implicitWidth
                    Layout.preferredHeight: effectiveStyle() === "largeIcon" ? largeButtonHeight : compactButtonHeight
                    clip: true
                    Row {
                        id: pathRow
                        spacing: 6
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: pathRow.implicitWidth <= pathHost.width ? parent.left : undefined
                        anchors.right: pathRow.implicitWidth <= pathHost.width ? undefined : parent.right
                        onImplicitWidthChanged: scheduleLayoutUpdate()
                        Repeater {
                            model: pathParts()
                            delegate: ProjectButton {
                                property bool isCurrent: index === pathParts().length - 1
                                label: modelData
                                style: effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                iconSource: iconFolder
                                fillColor: isCurrent ? accentPrimary : pill
                                strokeColor: isCurrent ? accentPrimary : pillBorder
                                textColor: isCurrent ? accentPrimaryText : text
                                textSize: baseFont
                                renaming: false
                                renameEnabled: false
                                onActivate: pathSegmentActivated(index)
                            }
                        }
                    }
                }
                Item { // HORIZONTAL: folders row (top line); hidden if wrapped
                    id: topFlowHost
                    Layout.fillWidth: false
                    Layout.preferredWidth: topFoldersRow.implicitWidth
                    Layout.preferredHeight: compactButtonHeight
                    Layout.alignment: Qt.AlignTop
                    visible: !flowOnSecondLine
                    onWidthChanged: scheduleLayoutUpdate()
                    Row {
                        id: topFoldersRow
                        spacing: 6
                        onImplicitWidthChanged: scheduleLayoutUpdate()
                        Repeater {
                            model: folders
                            delegate: ProjectButton {
                                label: modelData
                                style: effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                iconSource: iconFolder
                                fillColor: accentSecondary
                                strokeColor: accentSecondaryBorder
                                textColor: textSoft
                                textSize: baseFont
                                renaming: allowRename && renameTargetPath === (modelData.indexOf("/") === 0 ? modelData : (path + "/" + modelData))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(modelData.indexOf("/") === 0 ? modelData : (path + "/" + modelData))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(modelData)
                            }
                        }
                    }
                }
                Item { Layout.fillWidth: true } // HORIZONTAL: spacer/feder between folders and right buttons

                Item { // HORIZONTAL: right button cluster (search + style + optional theme)
                    id: rightButtonsHost
                    Layout.preferredWidth: rightButtonsRow.implicitWidth
                    Layout.minimumWidth: rightButtonsRow.implicitWidth
                    Layout.maximumWidth: rightButtonsRow.implicitWidth
                    Layout.preferredHeight: compactButtonHeight
                    Layout.alignment: Qt.AlignTop
                    Row {
                        id: rightButtonsRow
                        anchors.fill: parent
                        spacing: 6
                        Component.onCompleted: scheduleLayoutUpdate()
                        onImplicitWidthChanged: scheduleLayoutUpdate()
                        Rectangle {
                            visible: showSearchToggle && searchActive && !verticalView
                            width: 200
                            height: compactButtonHeight
                            radius: 4
                            color: card
                            border.color: pillBorder
                            TextField {
                                anchors.fill: parent
                                anchors.margins: 4
                                text: searchText
                                placeholderText: "Search      + deep    # all"
                                font.pixelSize: baseFont
                                selectByMouse: true
                                color: root.text
                                placeholderTextColor: root.textMuted
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 6
                                rightPadding: 6
                                topPadding: 1
                                bottomPadding: 0
                                background: Rectangle { color: "transparent" }
                                onTextChanged: {
                                    root.searchText = text
                                    root.searchTextEdited(text)
                                }
                                onVisibleChanged: {
                                    if (visible && searchActive) {
                                        forceActiveFocus()
                                        selectAll()
                                    }
                                }
                                Keys.onEscapePressed: {
                                    root.searchText = ""
                                    root.searchActive = false
                                }
                            }
                        }
                        Rectangle { // HORIZONTAL: search toggle button (Lupe)
                            visible: showSearchToggle
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: 4
                            color: pill
                            border.color: pillBorder
                            Image {
                                anchors.centerIn: parent
                                source: Qt.resolvedUrl(iconSearch)
                                width: baseFont
                                height: baseFont
                                fillMode: Image.PreserveAspectFit
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: toggleSearch()
                            }
                        }
                        Repeater { // HORIZONTAL: style buttons (t, G, k)
                            model: showStyleToggle ? [
                                { label: "t", style: "text" },
                                { label: "G", style: "largeIcon" },
                                { label: "k", style: "smallIcon" }
                            ] : []
                            delegate: Rectangle {
                                width: compactButtonHeight
                                height: compactButtonHeight
                                radius: 4
                                property bool isActive: buttonStyle === modelData.style
                                color: isActive ? accentSecondary : pill
                                border.color: isActive ? accentSecondaryBorder : pillBorder
                                visible: allowLargeIcons || modelData.style !== "largeIcon"
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.label
                                    color: text
                                    font.pixelSize: baseFont
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: styleChanged(modelData.style)
                                }
                            }
                        }
                    }
                }

            }

            RowLayout { // VERTICAL VIEW: top row (H/V toggle + right-side buttons)
                id: topRowVertical
                visible: verticalView
                Layout.fillWidth: true
                Layout.preferredHeight: compactButtonHeight
                spacing: 6
                Rectangle {
                    visible: showModeToggle
                    width: compactButtonHeight
                    height: compactButtonHeight
                    radius: 4
                    color: pill
                    border.color: accentSecondaryBorder
                    Text {
                        anchors.centerIn: parent
                        text: verticalView ? "H" : "V"
                        color: text
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: toggleMode()
                    }
                }
                Item { Layout.fillWidth: true } // VERTICAL: spacer/feder between H/V toggle and right buttons
                Row {
                    spacing: 6
                    Rectangle { // VERTICAL: search toggle button (Lupe)
                        visible: showSearchToggle
                        width: compactButtonHeight
                        height: compactButtonHeight
                        radius: 4
                        color: pill
                        border.color: pillBorder
                        Image {
                            anchors.centerIn: parent
                            source: iconSearch
                            width: baseFont
                            height: baseFont
                            fillMode: Image.PreserveAspectFit
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: toggleSearch()
                        }
                    }
                    Repeater { // VERTICAL: style buttons (t, G, k)
                        model: showStyleToggle ? [
                            { label: "t", style: "text" },
                            { label: "G", style: "largeIcon" },
                            { label: "k", style: "smallIcon" }
                        ] : []
                        delegate: Rectangle {
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: 4
                            property bool isActive: buttonStyle === modelData.style
                            color: isActive ? accentSecondary : pill
                            border.color: isActive ? accentSecondaryBorder : pillBorder
                            visible: allowLargeIcons || modelData.style !== "largeIcon"
                            Text {
                                anchors.centerIn: parent
                                text: modelData.label
                                color: text
                                font.pixelSize: baseFont
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: styleChanged(modelData.style)
                            }
                        }
                    }
                }
            }

            Item { // SEARCH FIELD (vertical view)
                visible: searchActive && verticalView
                Layout.fillWidth: true
                Layout.preferredHeight: compactButtonHeight
                Rectangle {
                    anchors.fill: parent
                    radius: 4
                    color: card
                    border.color: pillBorder
                    TextField {
                        anchors.fill: parent
                        anchors.margins: 4
                        text: searchText
                        placeholderText: "Search      + deep    # all"
                        font.pixelSize: baseFont
                        selectByMouse: true
                        color: root.text
                        placeholderTextColor: root.textMuted
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 6
                        rightPadding: 6
                        topPadding: 1
                        bottomPadding: 0
                        background: Rectangle { color: "transparent" }
                        onTextChanged: {
                            root.searchText = text
                            root.searchTextEdited(text)
                        }
                        onVisibleChanged: {
                            if (visible && searchActive) {
                                forceActiveFocus()
                                selectAll()
                            }
                        }
                        Keys.onEscapePressed: {
                            root.searchText = ""
                            root.searchActive = false
                        }
                    }
                }
            }

            RowLayout { // HORIZONTAL VIEW: row 2 (wrapped folders flow)
                id: bottomRow
                visible: !verticalView && flowOnSecondLine
                Layout.fillWidth: true
                spacing: 6
                implicitHeight: bottomFoldersFlow.implicitHeight
                Layout.preferredHeight: flowOnSecondLine ? bottomFoldersFlow.implicitHeight : 0
                Item {
                    id: bottomFlowHost
                    Layout.fillWidth: true
                    Layout.preferredHeight: flowOnSecondLine ? bottomFoldersFlow.implicitHeight : 0
                    Flow {
                        id: bottomFoldersFlow
                        width: bottomFlowHost.width
                        height: implicitHeight
                        spacing: 6
                        flow: Flow.LeftToRight
                        layoutDirection: Qt.LeftToRight
                        Repeater {
                            model: folders
                            delegate: ProjectButton {
                                label: modelData
                                style: effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                iconSource: iconFolder
                                fillColor: accentSecondary
                                strokeColor: accentSecondaryBorder
                                textColor: textSoft
                                textSize: baseFont
                                renaming: allowRename && renameTargetPath === (modelData.indexOf("/") === 0 ? modelData : (path + "/" + modelData))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(modelData.indexOf("/") === 0 ? modelData : (path + "/" + modelData))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(modelData)
                            }
                        }
                    }
                }
            }

            ColumnLayout { // VERTICAL VIEW: section 1 (parent paths)
                id: verticalColumn
                visible: verticalView
                Layout.fillWidth: true
                spacing: verticalParentSpacing
                Repeater {
                    model: visibleParentPaths()
                    delegate: ProjectButton {
                        width: parent.width
                        label: modelData.split("/").filter(function(p){ return p.length > 0 }).slice(-1)[0]
                        style: (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
                        compactHeight: compactButtonHeight
                        largeHeight: largeButtonHeight
                        largePadding: largeButtonPadding
                        iconSmall: iconSizeSmall
                        iconLarge: iconSizeLarge
                        iconSource: iconFolder
                        fillColor: pill
                        strokeColor: pillBorder
                        textColor: text
                        textSize: baseFont
                        renaming: false
                        renameEnabled: false
                        onActivate: pathSelected(modelData)
                    }
                }
            }

            ProjectButton { // VERTICAL VIEW: section 2 (current path highlight)
                id: cwpButton
                visible: verticalView
                width: parent.width
                label: pathParts().length ? pathParts()[pathParts().length - 1] : "/"
                style: (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
                compactHeight: compactButtonHeight
                largeHeight: largeButtonHeight
                largePadding: largeButtonPadding
                iconSmall: iconSizeSmall
                iconLarge: iconSizeLarge
                iconSource: iconFolder
                fillColor: accentPrimary
                strokeColor: accentPrimary
                textColor: accentPrimaryText
                textSize: baseFont + 1
                textBold: true
                renaming: false
                renameEnabled: false
                onActivate: {}
            }

            Flickable { // VERTICAL VIEW: section 3 (folders list, scrollable)
                id: foldersColumn
                visible: verticalView
                Layout.fillWidth: true
                Layout.fillHeight: false
                Layout.preferredHeight: foldersContent.implicitHeight
                contentWidth: width
                contentHeight: foldersContent.implicitHeight
                clip: true
                Column {
                    id: foldersContent
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: folders
                        delegate: ProjectButton {
                            x: indent
                            width: parent.width - indent
                            label: modelData
                            style: effectiveStyle()
                            largeIconAlignLeft: true
                            compactHeight: compactButtonHeight
                            largeHeight: largeButtonHeight
                            largePadding: largeButtonPadding
                            iconSmall: iconSizeSmall
                            iconLarge: iconSizeLarge
                            iconSource: iconFolder
                            fillColor: accentSecondary
                            strokeColor: accentSecondaryBorder
                            textColor: textSoft
                            textSize: baseFont
                            textLeftInset: effectiveStyle() === "text" ? indent : 0
                            renaming: allowRename && renameTargetPath === (modelData.indexOf("/") === 0 ? modelData : (path + "/" + modelData))
                            renameEnabled: allowRename
                            renameText: renameDraft
                            onRenameRequested: renameRequested(modelData.indexOf("/") === 0 ? modelData : (path + "/" + modelData))
                            onRenameTextEdited: renameTextEdited(text)
                            onRenameAccepted: renameAccepted()
                            onRenameCanceled: renameCanceled()
                            onActivate: folderActivated(modelData)
                        }
                    }
                }
            }
            Item { Layout.fillHeight: true; visible: verticalView }
        }
    }
}
