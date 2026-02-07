import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item { // ROOT
    id: root
    property int horizontalPreferredWidth: 640
    property int verticalPreferredWidth: 0
    property int verticalMinWidth: 180
    property int verticalMaxWidth: 560
    property int horizontalPreferredHeight: compactButtonHeight * 2 + (searchActive ? (compactButtonHeight + 8) : 0) + 24
    property int verticalPreferredHeight: 360
    implicitWidth: visible ? verticalAutoWidth : 0
    implicitHeight: visible ? contentHeight : 0
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
    property color smallButtonBg: pill
    property color smallButtonBorder: pillBorder
    property color smallButtonActiveBg: accentSecondary
    property color smallButtonActiveBorder: accentSecondaryBorder
    property color smallButtonText: textSoft
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
    property int wrapSlackOn: 20
    property int wrapSlackOff: 40
    property bool verticalButtonsOnSecondLine: false
    property bool verticalLayoutUpdatePending: false
    property bool debugVerticalWrap: true
    property real verticalAvailableHeight: 0
    property real verticalDesiredHeight: 0
    property real verticalOver: 0
    property bool foldersInSecondColumn: false
    property int verticalAutoWidth: 0
    property int verticalColumnWidth: 0
    property bool verticalWidthUpdatePending: false
    property int contentHeight: 0
    property bool contentHeightUpdatePending: false

    TextMetrics {
        id: labelMetrics
        font.pixelSize: baseFont
    }

    function effectiveStyle() {
        if (!allowLargeIcons && buttonStyle === "largeIcon") return "text"
        return buttonStyle
    }

    function estimateButtonWidth(label, styleName) {
        labelMetrics.text = label
        var textWidth = labelMetrics.width
        if (styleName === "smallIcon") {
            return Math.max(80, textWidth + iconSizeSmall + 30)
        }
        if (styleName === "largeIcon") {
            return Math.max(80, Math.max(iconSizeLarge, textWidth) + 20)
        }
        return Math.max(80, textWidth + 24)
    }

    function calculateVerticalAutoWidth() {
        if (!verticalView) return verticalPreferredWidth > 0 ? verticalPreferredWidth : verticalMinWidth
        var maxWidth = 0
        var pathStyle = (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
        var parts = visibleParentPaths()
        for (var i = 0; i < parts.length; i++) {
            var label = parts[i].split("/").filter(function(p){ return p.length > 0 }).slice(-1)[0]
            maxWidth = Math.max(maxWidth, estimateButtonWidth(label, pathStyle))
        }
        var currentLabel = pathParts().length ? pathParts()[pathParts().length - 1] : "/"
        maxWidth = Math.max(maxWidth, estimateButtonWidth(currentLabel, pathStyle))
        var folderStyle = effectiveStyle()
        for (var f = 0; f < folders.length; f++) {
            maxWidth = Math.max(maxWidth, indent + estimateButtonWidth(folders[f], folderStyle))
        }
        var buttonsWidth = (showModeToggle ? compactButtonHeight + 6 : 0) + verticalButtonsPanel.implicitWidth
        maxWidth = Math.max(maxWidth, buttonsWidth + 12)
        var padded = maxWidth + 32
        var columnWidth = Math.min(verticalMaxWidth, Math.max(verticalMinWidth, padded))
        verticalColumnWidth = columnWidth
        var gap = verticalContentRow ? verticalContentRow.spacing : 12
        return foldersInSecondColumn ? (columnWidth * 2 + gap) : columnWidth
    }

    function calculateContentHeight() {
        if (!mainColumn) return 0
        if (verticalView) {
            return Math.round(verticalMainColumn.childrenRect.height + 24)
        }
        var top = topRow ? topRow.implicitHeight : 0
        var bottom = (bottomRow && bottomRow.visible) ? (bottomRow.implicitHeight + mainColumn.spacing) : 0
        return Math.round(top + bottom + 24)
    }

    function scheduleContentHeightUpdate() {
        if (contentHeightUpdatePending) return
        contentHeightUpdatePending = true
        Qt.callLater(function() {
            contentHeight = calculateContentHeight()
            contentHeightUpdatePending = false
        })
    }

    onVerticalButtonsOnSecondLineChanged: {
        if (verticalButtonsSlotTop) {
            setButtonsParent(verticalButtonsPanel, verticalButtonsSlotTop)
        }
    }

    Component.onCompleted: {
        if (verticalButtonsSlotTop) {
            setButtonsParent(verticalButtonsPanel, verticalButtonsSlotTop)
        }
        scheduleVerticalLayoutUpdate()
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }

    onVisibleChanged: {
        scheduleVerticalLayoutUpdate()
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }

    onVerticalViewChanged: {
        if (!verticalView) {
            verticalButtonsOnSecondLine = false
        }
        scheduleVerticalLayoutUpdate()
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }

    onPathChanged: scheduleVerticalWidthUpdate()
    onFoldersChanged: scheduleVerticalWidthUpdate()
    onButtonStyleChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onIconSizeSmallChanged: scheduleVerticalWidthUpdate()
    onIconSizeLargeChanged: scheduleVerticalWidthUpdate()
    onBaseFontChanged: scheduleVerticalWidthUpdate()
    onCompactButtonHeightChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onLargeButtonHeightChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onLargeButtonPaddingChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onIndentChanged: scheduleVerticalWidthUpdate()
    onShowModeToggleChanged: scheduleVerticalWidthUpdate()
    onShowStyleToggleChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onShowSearchToggleChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onFoldersInSecondColumnChanged: {
        scheduleVerticalWidthUpdate()
        scheduleVerticalLayoutUpdate()
        scheduleContentHeightUpdate()
    }
    onSearchActiveChanged: scheduleContentHeightUpdate()
    onFlowOnSecondLineChanged: scheduleContentHeightUpdate()


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

    function scheduleVerticalWidthUpdate() {
        if (verticalWidthUpdatePending) return
        verticalWidthUpdatePending = true
        Qt.callLater(function() {
            verticalAutoWidth = calculateVerticalAutoWidth()
            verticalPreferredWidth = verticalAutoWidth
            verticalWidthUpdatePending = false
        })
    }

    function scheduleVerticalLayoutUpdate() {
        if (verticalLayoutUpdatePending) return
        verticalLayoutUpdatePending = true
        Qt.callLater(function() {
            updateVerticalButtonsPlacement()
            verticalLayoutUpdatePending = false
        })
    }

    function updateFlowPlacement() {
        if (!topFoldersRow || !topRow || !rightButtonsRow || !pathRow) return
        if (topRow.width <= 0) return
        var toggleWidth = (showModeToggle && modeToggleButton) ? modeToggleButton.width : 0
        var gapCount = showModeToggle ? 4 : 3
        var rightWidth = rightButtonsRow.implicitWidth
        var used = pathRow.implicitWidth + topFoldersRow.implicitWidth + rightWidth + toggleWidth + (topRow.spacing * gapCount)
        var slack = topRow.width - used
        var shouldWrap = flowOnSecondLine ? (slack < wrapSlackOff) : (slack < wrapSlackOn)
        if (flowOnSecondLine !== shouldWrap) flowOnSecondLine = shouldWrap
    }

    function updateVerticalButtonsPlacement() {
        if (!verticalView) return
        if (!verticalMainColumn || !verticalContentRow || !verticalButtonsPanel) return
        if (verticalContentRow.height <= 0) return
        var available = verticalContentRow.height       // verfügbare Höhe
        var desired = verticalMainColumn.implicitHeight // aktuelle Höhe
        var over = desired - available                  // 0 bei Berührung
        verticalAvailableHeight = available
        verticalDesiredHeight = desired
        verticalOver = over
        var remaining = available - desired
        var freeHeight = verticalSpacer ? verticalSpacer.height : remaining
        var rightColumnNeeded = foldersContentRight ? foldersContentRight.implicitHeight : 0
        var shouldWrap = foldersInSecondColumn
            ? (freeHeight < rightColumnNeeded + wrapSlackOff)
            : (freeHeight < rightColumnNeeded + wrapSlackOn)
        if (verticalButtonsOnSecondLine !== shouldWrap) {
            verticalButtonsOnSecondLine = shouldWrap
            foldersInSecondColumn = shouldWrap
        }
    }

    function setButtonsParent(item, newParent) {
        if (item && newParent && item.parent !== newParent) {
            item.parent = newParent
            item.anchors.fill = undefined
            item.x = 0
            item.y = 0
        }
    }


    Rectangle { // buttonsPool (dynamic)
        anchors.fill: parent
        color: panelColor
        border.color: panelBorderColor
        radius: 8
        Item {
            id: buttonsPool
            visible: false
        }

        Item {              // VERTICAL: ButtonsPanel
            id: verticalButtonsPanel
            parent: buttonsPool
            implicitWidth: verticalButtonsContent.implicitWidth
            implicitHeight: verticalButtonsContent.implicitHeight
            width: implicitWidth
            height: compactButtonHeight
            Row {           // VERTICAL: ButtonsContent
                id: verticalButtonsContent
                anchors.fill: parent
                spacing: 6
                Component.onCompleted: scheduleVerticalLayoutUpdate()
                onImplicitWidthChanged: {
                    scheduleVerticalLayoutUpdate()
                    scheduleVerticalWidthUpdate()
                }
                Rectangle { // VERTICAL: search toggle button (Lupe)
                    visible: showSearchToggle
                    width: compactButtonHeight
                    height: compactButtonHeight
                    radius: 4
                    color: smallButtonBg
                    border.color: smallButtonBorder
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
                Repeater {  // VERTICAL: style buttons (t, G, k)
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
                        color: isActive ? smallButtonActiveBg : smallButtonBg
                        border.color: isActive ? smallButtonActiveBorder : smallButtonBorder
                        visible: allowLargeIcons || modelData.style !== "largeIcon"
                        Text {
                            anchors.centerIn: parent
                            text: modelData.label
                            color: smallButtonText
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

        ColumnLayout {  // Which VIEW???:
            id: mainColumn
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            RowLayout { // HORIZONTAL: row 1 (path + folders + right buttons)
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
                    color: smallButtonBg
                    border.color: smallButtonBorder
                    Text {
                        anchors.centerIn: parent
                        text: verticalView ? "H" : "V"
                        color: smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: toggleMode()
                    }
                }

                Item {  // HORIZONTAL: path segment row (breadcrumbs)
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
                Item {  // HORIZONTAL: folders row (top line); hidden if wrapped
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

                Item {  // HORIZONTAL: right button cluster (search + style + optional theme)
                    id: rightButtonsHost
                    Layout.preferredWidth: rightButtonsRow.implicitWidth
                    Layout.minimumWidth: rightButtonsRow.implicitWidth
                    Layout.maximumWidth: rightButtonsRow.implicitWidth
                    Layout.preferredHeight: compactButtonHeight
                    Layout.alignment: Qt.AlignTop | Qt.AlignRight
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
                            color: smallButtonBg
                            border.color: smallButtonBorder
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
                                color: isActive ? smallButtonActiveBg : smallButtonBg
                                border.color: isActive ? smallButtonActiveBorder : smallButtonBorder
                                visible: allowLargeIcons || modelData.style !== "largeIcon"
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.label
                                    color: smallButtonText
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

            RowLayout { // VERTICAL VIEW: main column + right column for buttons
                id: verticalContentRow
                visible: verticalView
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12
                onHeightChanged: scheduleVerticalLayoutUpdate()
                ColumnLayout { // VERTICAL mainColumn
                    id: verticalMainColumn
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 8
                    onImplicitHeightChanged: {
                        scheduleVerticalLayoutUpdate()
                        scheduleContentHeightUpdate()
                    }
                    onChildrenRectChanged: {
                        scheduleVerticalLayoutUpdate()
                        scheduleContentHeightUpdate()
                    }
                    Text {
                        visible: debugVerticalWrap
                        text: "V-wrap: avail=" + Math.round(verticalAvailableHeight) + "\n" +
                              "desired=" + Math.round(verticalDesiredHeight) + "\n" +
                              "over=" + Math.round(verticalOver) + "\n" +
                              "wrap=" + (foldersInSecondColumn ? "yes" : "no")
                        color: "#ff5c5c"
                        font.pixelSize: Math.max(10, baseFont - 4)
                    }
                    Text {
                        visible: debugVerticalWrap
                        text: "FB width=" + Math.round(verticalAutoWidth)
                        color: "#ff5c5c"
                        font.pixelSize: Math.max(10, baseFont - 4)
                    }
                    RowLayout { // VERTICAL VIEW: top row (H/V toggle + inline buttons)
                        id: topRowVertical
                        Layout.fillWidth: true
                        Layout.preferredHeight: compactButtonHeight
                        spacing: 6
                        onWidthChanged: scheduleVerticalLayoutUpdate()
                        Rectangle {
                            id: modeToggleButtonVertical
                            visible: showModeToggle
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: 4
                            color: smallButtonBg
                            border.color: smallButtonBorder
                            Text {
                                anchors.centerIn: parent
                                text: verticalView ? "H" : "V"
                                color: smallButtonText
                                font.pixelSize: baseFont
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: toggleMode()
                            }
                        }
                        Item { Layout.fillWidth: true } // VERTICAL: spacer/feder between H/V toggle and right buttons
                        Item {
                            id: verticalButtonsSlotTop
                            visible: true
                            Layout.preferredWidth: verticalButtonsPanel.implicitWidth
                            Layout.minimumWidth: verticalButtonsPanel.implicitWidth
                            Layout.maximumWidth: verticalButtonsPanel.implicitWidth
                            Layout.preferredHeight: compactButtonHeight
                            Layout.alignment: Qt.AlignRight | Qt.AlignTop
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
                    ColumnLayout { // VERTICAL VIEW: section 1 (parent paths)
                        id: verticalColumn
                        Layout.fillWidth: true
                        spacing: verticalParentSpacing
                        Repeater { // PathButtons
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
                        visible: !foldersInSecondColumn
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
                    Item {
                        visible: foldersInSecondColumn
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Item { id: verticalSpacer; Layout.fillHeight: true; Layout.minimumHeight: 0 }
                }
            ColumnLayout { // VERTICAL: right column for folders
                id: verticalRightColumn
                visible: foldersInSecondColumn
                Layout.preferredWidth: Math.max(verticalButtonsPanel.implicitWidth, verticalColumnWidth)
                Layout.minimumWidth: Math.max(verticalButtonsPanel.implicitWidth, verticalColumnWidth)
                Layout.maximumWidth: Math.max(verticalButtonsPanel.implicitWidth, verticalColumnWidth)
                Layout.fillHeight: true
                spacing: 6
                Rectangle { // Roter Indikator
                    visible: debugVerticalWrap
                    Layout.fillWidth: true
                    Layout.preferredHeight: 14
                    color: "#ff5c5c"
                    radius: 3
                }
                Flickable { // VERTICAL: folders list (right column)
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: foldersContentRight.height
                    clip: true
                    Column {
                        id: foldersContentRight
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
                Item { Layout.fillHeight: true }
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
        }
    }
}
