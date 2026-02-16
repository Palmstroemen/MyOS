import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "Theme/tag_chips.js" as TagChips
import "Theme/panel_colors.js" as PanelColors

Rectangle { // Files panel
    id: root
    property var itemsModel: null
    property int baseFont: 14
    property color text: "#e6e6e6"
    property color textMuted: "#c9ccd7"
    property color panelAlt: "#151821"
    property color pillBorder: "#3a4158"
    property color backgroundColor: "#404040"
    property color itemFillColor: "#151821"
    property color itemBorderColor: "#3a4158"
    property color smallButtonBg: "#3a4258"
    property color smallButtonBorder: "#505a74"
    property color smallButtonActiveBg: "#4a5675"
    property color smallButtonActiveBorder: "#6a779a"
    property color smallButtonText: "#b4bac6"
    property color projectTint: "#7b5bd6"
    property color projectTintBorder: "#7b5bd6"
    property color uPanelTintColor: projectTint
    property real uPanelTintMix: 0.65
    property real projectTintOpacity: 1.0
    property bool allowDrags: true
    property bool halfTransparent: false
    property bool showFolders: false
    property var availableTags: []
    property var selectedTags: []
    property var selectedPaths: []
    property string tagSource: "visible"
    property real templatesBrowserWidth: 0
    property real projectsBrowserWidth: 0
    property string iconFolder: ""
    property string iconFolderOff: ""
    property string iconFile: ""
    property string iconGear: ""
    property string itemStyle: "largeIcon"
    signal folderActivated(string name)
    signal fileActivated(string name)
    signal openMyosFolder()
    signal createProject()
    property bool showMyosButton: false
    property bool showCreateProject: false

    property int compactButtonHeight: 32
    property int largeButtonHeight: 88
    property int largeButtonPadding: 6
    property int iconSizeSmall: 24
    property int iconSizeLarge: 64
    property int smallIconSize: Math.round(compactButtonHeight * 0.6)
    property int topRightButtonSize: Math.max(24, Math.round(Math.max(compactButtonHeight, 32) * 0.85))
    property int topRightIconSize: Math.round(topRightButtonSize * 0.84)
    property int gridSpacing: 8
    property int prefetchThreshold: 200
    property int chipRadiusMedium: TagChips.CHIP_RADIUS_MEDIUM
    property int tagChipRadius: TagChips.TAG_CHIP_RADIUS
    property int tagChipMinHeight: TagChips.TAG_CHIP_MIN_HEIGHT
    property real tagChipHeightFactor: TagChips.TAG_CHIP_HEIGHT_FACTOR
    property real tagChipSelectedFillAlpha: TagChips.TAG_CHIP_SELECTED_FILL_ALPHA
    property real tagChipIdleFillAlpha: TagChips.TAG_CHIP_IDLE_FILL_ALPHA
    property real tagChipSelectedBorderAlpha: TagChips.TAG_CHIP_SELECTED_BORDER_ALPHA
    property real tagChipIdleBorderAlpha: TagChips.TAG_CHIP_IDLE_BORDER_ALPHA
    property real tagFilterIdleBgAlpha: TagChips.TAG_FILTER_IDLE_BG_ALPHA
    property real filesPanelOverlayAlpha: 0.20
    property int sideMixControlHeight: Math.max(54, compactButtonHeight + 22)
    readonly property real uPanelLuma: (0.2126 * backgroundColor.r) + (0.7152 * backgroundColor.g) + (0.0722 * backgroundColor.b)
    readonly property color uPanelColor: PanelColors.uPanelColor(showMyosButton, backgroundColor, uPanelTintColor, uPanelTintMix)
    readonly property color filesPanelOverlayColor: PanelColors.filesOverlayColor(uPanelLuma, filesPanelOverlayAlpha)

    radius: 0
    color: root.uPanelColor
    border.width: 0
    implicitWidth: 0
    implicitHeight: 0
    opacity: halfTransparent ? 0.5 : 1

    signal requestMore()
    signal filterChanged(bool showFolders)
    signal tagToggled(string tag)
    signal requestTagSourceChange(string source)
    signal itemActivated(string path, bool ctrlPressed, bool shiftPressed)
    signal selectionBoxApplied(var paths, bool additive)
    signal moveEntriesRequested(string payload, string targetDir)
    signal createNoteRequested()
    signal moveSelectedIntoNewFolderRequested(var sourcePaths)
    signal renameRequested(var paths)
    signal deleteRequested(var paths)
    signal selectAllRequested()
    signal openRequested(string path)
    signal openWithRequested(string path)

    onShowFoldersChanged: filterChanged(showFolders)

    function selectedPayloadFor(itemPath, itemIsSelected) {
        var paths = []
        if (itemIsSelected && selectedPaths && selectedPaths.length > 0) {
            for (var i = 0; i < selectedPaths.length; i++) {
                var p = selectedPaths[i]
                if (p && p.length > 0) {
                    paths.push(p)
                }
            }
        } else if (itemPath && itemPath.length > 0) {
            paths = [itemPath]
        }
        if (paths.length <= 1) {
            return paths.length === 1 ? paths[0] : ""
        }
        return "__MYOS_PATHS__" + JSON.stringify(paths)
    }

    function selectedFolderPaths() {
        var result = []
        if (!selectedPaths || selectedPaths.length === 0 || !itemsModel) {
            return result
        }
        for (var i = 0; i < selectedPaths.length; i++) {
            var selectedPath = String(selectedPaths[i] || "")
            if (!selectedPath) {
                continue
            }
            for (var j = 0; j < itemsModel.count; j++) {
                var entry = itemsModel.get(j)
                if (!entry) {
                    continue
                }
                var entryPath = String(entry.path || "")
                if (entryPath === selectedPath && entry.isDir) {
                    result.push(selectedPath)
                    break
                }
            }
        }
        return result
    }

    function isPathDirectory(path) {
        if (!itemsModel || !path) {
            return false
        }
        for (var i = 0; i < itemsModel.count; i++) {
            var entry = itemsModel.get(i)
            if (!entry) {
                continue
            }
            if (String(entry.path || "") === path) {
                return !!entry.isDir
            }
        }
        return false
    }

    function selectedPathsForContext(itemPath, itemIsSelected) {
        var result = []
        if (itemIsSelected && selectedPaths && selectedPaths.length > 0) {
            for (var i = 0; i < selectedPaths.length; i++) {
                var p = String(selectedPaths[i] || "")
                if (p) {
                    result.push(p)
                }
            }
            return result
        }
        if (itemPath && itemPath.length > 0) {
            result.push(itemPath)
        }
        return result
    }

    function fileOnlyPaths(paths) {
        var result = []
        for (var i = 0; i < (paths || []).length; i++) {
            var p = String(paths[i] || "")
            if (!p) {
                continue
            }
            if (!isPathDirectory(p)) {
                result.push(p)
            }
        }
        return result
    }

    property string contextTargetPath: ""
    property bool contextTargetIsDir: false
    property var contextTargetSelection: []
    property var contextTargetFileSelection: []

    function openItemContextMenu(itemPath, itemIsDir, itemIsSelected, mouseX, mouseY) {
        contextTargetPath = itemPath || ""
        contextTargetIsDir = !!itemIsDir
        contextTargetSelection = selectedPathsForContext(contextTargetPath, itemIsSelected)
        contextTargetFileSelection = fileOnlyPaths(contextTargetSelection)
        itemContextMenu.x = mouseX
        itemContextMenu.y = mouseY
        itemContextMenu.open()
    }

    Rectangle {
        id: sidePanel
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        anchors.rightMargin: 10
        width: Math.max(110, Math.min(210, Math.round(parent.width * 0.22)))
        radius: 0
        border.width: 0
        color: Qt.rgba(root.panelAlt.r, root.panelAlt.g, root.panelAlt.b, 0.20)
        z: 2

        Column {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 8

            Row {
                width: parent.width
                spacing: 6

                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: Qt.rgba(root.projectTint.r, root.projectTint.g, root.projectTint.b, root.projectTintOpacity)
                    border.color: Qt.rgba(root.projectTintBorder.r, root.projectTintBorder.g, root.projectTintBorder.b, root.projectTintOpacity)
                    visible: root.showCreateProject
                    Text {
                        anchors.centerIn: parent
                        text: "P"
                        color: "#ffffff"
                        font.pixelSize: Math.round(root.baseFont * 0.9)
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.createProject()
                    }
                }

                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: root.smallButtonBg
                    border.color: root.smallButtonBorder
                    visible: root.showMyosButton
                    Image {
                        anchors.centerIn: parent
                        source: root.iconGear
                        width: root.topRightIconSize
                        height: root.topRightIconSize
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: width
                        sourceSize.height: height
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.openMyosFolder()
                    }
                }

                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: root.showFolders ? root.smallButtonActiveBg : root.smallButtonBg
                    border.color: root.showFolders ? root.smallButtonActiveBorder : root.smallButtonBorder
                    Image {
                        anchors.centerIn: parent
                        source: root.showFolders ? root.iconFolder : root.iconFolderOff
                        width: root.topRightIconSize
                        height: root.topRightIconSize
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: width
                        sourceSize.height: height
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: root.showFolders
                        text: "X"
                        color: "#e53935"
                        font.bold: true
                        font.pixelSize: Math.max(14, Math.round(root.topRightButtonSize * 0.70))
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.showFolders = !root.showFolders
                    }
                }
            }

            Rectangle {
                width: parent.width
                height: root.sideMixControlHeight
                radius: root.tagChipRadius
                border.width: 0
                color: Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, 0.25)

                Column {
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 4
                    Text {
                        text: qsTr("U-Farbmix") + ": " + Math.round(root.uPanelTintMix * 100) + "%"
                        color: root.smallButtonText
                        font.pixelSize: Math.max(10, Math.round(root.baseFont * 0.78))
                        elide: Text.ElideRight
                    }
                    Slider {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        from: 0.0
                        to: 1.0
                        stepSize: 0.01
                        value: root.uPanelTintMix
                        onMoved: root.uPanelTintMix = value
                        onValueChanged: root.uPanelTintMix = value
                    }
                }
            }

            Rectangle {
                width: parent.width
                height: Math.max(80, parent.height - root.topRightButtonSize - root.sideMixControlHeight - 28)
                radius: 0
                border.width: 0
                color: "transparent"
                visible: (root.availableTags && root.availableTags.length > 0)

                Column {
                    anchors.fill: parent
                    spacing: 6

                    Row {
                        width: parent.width
                        spacing: 6

                        Rectangle {
                            width: (parent.width - 6) / 2
                            height: root.compactButtonHeight
                            radius: root.tagChipRadius
                            color: root.tagSource === "project"
                                ? root.smallButtonActiveBg
                                : Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, root.tagFilterIdleBgAlpha)
                            border.color: root.tagSource === "project" ? root.smallButtonActiveBorder : root.smallButtonBorder
                            Text {
                                anchors.centerIn: parent
                                text: qsTr("Project")
                                color: root.smallButtonText
                                font.pixelSize: Math.max(10, Math.round(root.baseFont * 0.82))
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: root.requestTagSourceChange("project")
                            }
                        }

                        Rectangle {
                            width: (parent.width - 6) / 2
                            height: root.compactButtonHeight
                            radius: root.tagChipRadius
                            color: root.tagSource === "visible"
                                ? root.smallButtonActiveBg
                                : Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, root.tagFilterIdleBgAlpha)
                            border.color: root.tagSource === "visible" ? root.smallButtonActiveBorder : root.smallButtonBorder
                            Text {
                                anchors.centerIn: parent
                                text: qsTr("Visible")
                                color: root.smallButtonText
                                font.pixelSize: Math.max(10, Math.round(root.baseFont * 0.82))
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: root.requestTagSourceChange("visible")
                            }
                        }
                    }

                    Flickable {
                        width: parent.width
                        height: parent.height - root.compactButtonHeight - 6
                        contentWidth: width
                        contentHeight: tagsColumn.height
                        clip: true

                        Column {
                            id: tagsColumn
                            width: parent.width
                            spacing: 4

                            Repeater {
                                model: root.availableTags ? root.availableTags : []
                                delegate: Rectangle {
                                    width: tagsColumn.width
                                    height: Math.max(root.tagChipMinHeight, Math.round(root.compactButtonHeight * root.tagChipHeightFactor))
                                    radius: root.tagChipRadius
                                    readonly property string tagValue: modelData
                                    readonly property bool selected: root.selectedTags && root.selectedTags.indexOf(tagValue) !== -1
                                    color: selected
                                        ? Qt.rgba(root.projectTint.r, root.projectTint.g, root.projectTint.b, root.tagChipSelectedFillAlpha)
                                        : Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, root.tagChipIdleFillAlpha)
                                    border.color: selected
                                        ? Qt.rgba(root.projectTintBorder.r, root.projectTintBorder.g, root.projectTintBorder.b, root.tagChipSelectedBorderAlpha)
                                        : Qt.rgba(root.smallButtonBorder.r, root.smallButtonBorder.g, root.smallButtonBorder.b, root.tagChipIdleBorderAlpha)

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.left: parent.left
                                        anchors.leftMargin: 8
                                        anchors.right: parent.right
                                        anchors.rightMargin: 6
                                        text: "#" + tagValue
                                        color: selected ? "#ffffff" : root.textMuted
                                        font.pixelSize: Math.max(10, Math.round(root.baseFont * 0.82))
                                        elide: Text.ElideRight
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: root.tagToggled(parent.tagValue)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: filesPanelSurface
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: sidePanel.left
        anchors.leftMargin: 16
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        anchors.rightMargin: 10
        radius: 12
        color: root.filesPanelOverlayColor
        border.width: 0
        z: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        anchors.rightMargin: sidePanel.width + 20
        spacing: 8

        GridView {
            id: filesGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.itemsModel
            cellWidth: root.itemStyle === "largeIcon"
                ? (Math.max(120, root.iconSizeLarge + 36) + root.gridSpacing)
                : width
            cellHeight: root.itemStyle === "largeIcon"
                ? (root.largeButtonHeight + root.gridSpacing)
                : (root.compactButtonHeight + 4)
            delegate: FolderItem {
                readonly property string itemPath: (model.path && model.path.length > 0) ? model.path : ""
                readonly property bool selected: root.selectedPaths && itemPath.length > 0 && root.selectedPaths.indexOf(itemPath) !== -1
                width: filesGrid.cellWidth - root.gridSpacing
                height: filesGrid.cellHeight - (root.itemStyle === "largeIcon" ? root.gridSpacing : 4)
                label: model.name
                style: root.itemStyle
                compactHeight: root.compactButtonHeight
                largeHeight: root.largeButtonHeight
                largePadding: root.largeButtonPadding
                iconSmall: root.iconSizeSmall
                iconLarge: root.iconSizeLarge
                iconSource: "image://theme/" + (model.iconName ? model.iconName : (model.isDir ? "folder" : "text-x-generic"))
                thumbnailSource: model.thumb ? model.thumb : ""
                fillColor: selected ? Qt.rgba(0.58, 0.60, 0.64, 0.34) : root.itemFillColor
                strokeColor: selected ? Qt.rgba(0.74, 0.76, 0.80, 0.92) : root.itemBorderColor
                textColor: root.text
                textSize: root.baseFont
                largeIconAlignLeft: false
                dragEnabled: root.allowDrags
                    && (!model.isEmbryo)
                    && itemPath.length > 0
                dragPayload: root.selectedPayloadFor(itemPath, selected)
                onActivate: function(ctrlPressed, shiftPressed) {
                    root.itemActivated(itemPath, ctrlPressed, shiftPressed)
                }
                onContextMenuRequested: function(mouseX, mouseY, _ctrlPressed) {
                    if (!selected || !root.selectedPaths || root.selectedPaths.length === 0) {
                        root.itemActivated(itemPath, false, false)
                    }
                    var mapped = mapToItem(selectionOverlay, mouseX, mouseY)
                    root.openItemContextMenu(itemPath, model.isDir, selected, mapped.x, mapped.y)
                }
                onDoubleActivate: {
                    if (model.isDir) {
                        root.folderActivated(model.name)
                    } else {
                        if (itemPath && itemPath.length > 0) {
                            root.openRequested(itemPath)
                        } else {
                            root.fileActivated(model.name)
                        }
                    }
                }
                DropArea {
                    anchors.fill: parent
                    enabled: model.isDir && !model.isEmbryo
                    onDropped: {
                        if (!drop || !drop.text || itemPath.length === 0) return
                        root.moveEntriesRequested(drop.text, itemPath)
                        drop.acceptProposedAction()
                    }
                }
            }
            onContentYChanged: {
                if (contentHeight <= height) return
                if ((contentY + height + root.prefetchThreshold) >= contentHeight) {
                    root.requestMore()
                }
            }
        }

        Item {
            id: selectionOverlay
            parent: filesGrid
            anchors.fill: parent
            z: 20

            property bool marqueeActive: false
            property real startX: 0
            property real startY: 0
            property real endX: 0
            property real endY: 0
            property bool additiveSelection: false

            function rectX() { return Math.min(startX, endX) }
            function rectY() { return Math.min(startY, endY) }
            function rectW() { return Math.abs(endX - startX) }
            function rectH() { return Math.abs(endY - startY) }

            function intersects(aX, aY, aW, aH, bX, bY, bW, bH) {
                return aX < (bX + bW) && (aX + aW) > bX && aY < (bY + bH) && (aY + aH) > bY
            }

            function openContextMenu(mouseX, mouseY) {
                filesContextMenu.x = mouseX
                filesContextMenu.y = mouseY
                filesContextMenu.open()
            }

            function collectSelectionPaths() {
                var selected = []
                var rx = rectX()
                var ry = rectY()
                var rw = rectW()
                var rh = rectH()
                var count = filesGrid.count || 0
                for (var i = 0; i < count; i++) {
                    var item = filesGrid.itemAtIndex(i)
                    if (!item || !item.itemPath || item.itemPath.length === 0) {
                        continue
                    }
                    var ix = item.x - filesGrid.contentX
                    var iy = item.y - filesGrid.contentY
                    if (intersects(rx, ry, rw, rh, ix, iy, item.width, item.height)) {
                        selected.push(item.itemPath)
                    }
                }
                return selected
            }

            MouseArea {
                id: selectionArea
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                hoverEnabled: false
                preventStealing: true

                onPressed: function(mouse) {
                    var idx = filesGrid.indexAt(mouse.x + filesGrid.contentX, mouse.y + filesGrid.contentY)
                    if (idx >= 0) {
                        var item = filesGrid.itemAtIndex(idx)
                        if (item && typeof item.hitAcceptsPoint === "function") {
                            var itemLocalX = mouse.x + filesGrid.contentX - item.x
                            var itemLocalY = mouse.y + filesGrid.contentY - item.y
                            if (!item.hitAcceptsPoint(itemLocalX, itemLocalY)) {
                                idx = -1
                            }
                        }
                    }
                    if (mouse.button === Qt.RightButton) {
                        if (idx >= 0) {
                            mouse.accepted = false
                            return
                        }
                        selectionOverlay.openContextMenu(mouse.x, mouse.y)
                        mouse.accepted = true
                        return
                    }
                    if (idx >= 0) {
                        mouse.accepted = false
                        return
                    }
                    selectionOverlay.additiveSelection = (mouse.modifiers & Qt.ControlModifier) !== 0
                    selectionOverlay.marqueeActive = true
                    selectionOverlay.startX = mouse.x
                    selectionOverlay.startY = mouse.y
                    selectionOverlay.endX = mouse.x
                    selectionOverlay.endY = mouse.y
                    filesGrid.interactive = false
                }

                onPositionChanged: function(mouse) {
                    if (!selectionOverlay.marqueeActive) {
                        return
                    }
                    selectionOverlay.endX = mouse.x
                    selectionOverlay.endY = mouse.y
                }

                onReleased: {
                    if (!selectionOverlay.marqueeActive) {
                        return
                    }
                    filesGrid.interactive = true
                    var moved = selectionOverlay.rectW() > 6 || selectionOverlay.rectH() > 6
                    if (moved) {
                        var paths = selectionOverlay.collectSelectionPaths()
                        root.selectionBoxApplied(paths, selectionOverlay.additiveSelection)
                    } else if (!selectionOverlay.additiveSelection) {
                        // Plain click on empty area clears selection.
                        root.selectionBoxApplied([], false)
                    }
                    selectionOverlay.marqueeActive = false
                }

                onDoubleClicked: function(mouse) {
                    var idx = filesGrid.indexAt(mouse.x + filesGrid.contentX, mouse.y + filesGrid.contentY)
                    if (idx >= 0) {
                        mouse.accepted = false
                        return
                    }
                    mouse.accepted = true
                }

                onCanceled: {
                    filesGrid.interactive = true
                    selectionOverlay.marqueeActive = false
                }
            }

            Rectangle {
                visible: selectionOverlay.marqueeActive && (selectionOverlay.rectW() > 1 || selectionOverlay.rectH() > 1)
                x: selectionOverlay.rectX()
                y: selectionOverlay.rectY()
                width: selectionOverlay.rectW()
                height: selectionOverlay.rectH()
                color: Qt.rgba(0.66, 0.69, 0.74, 0.18)
                border.color: Qt.rgba(0.80, 0.82, 0.86, 0.85)
                border.width: 1
                radius: 3
            }
        }
    }

    Menu {
        id: filesContextMenu

        MenuItem {
            text: qsTr("Notiz erstellen")
            onTriggered: root.createNoteRequested()
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("In neuen Ordner verschieben")
            enabled: root.selectedPaths && root.selectedPaths.length > 1
            onTriggered: root.moveSelectedIntoNewFolderRequested(root.selectedPaths)
        }
    }

    Menu {
        id: itemContextMenu

        MenuItem {
            text: qsTr("Oeffnen")
            enabled: (!root.contextTargetIsDir && root.contextTargetFileSelection.length === 1)
            onTriggered: root.openRequested(root.contextTargetFileSelection[0])
        }
        MenuItem {
            text: qsTr("Oeffnen mit ...")
            enabled: (!root.contextTargetIsDir && root.contextTargetFileSelection.length === 1)
            onTriggered: root.openWithRequested(root.contextTargetFileSelection[0])
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Alle markieren")
            enabled: root.itemsModel && root.itemsModel.count > 0
            onTriggered: root.selectAllRequested()
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("Umbenennen")
            enabled: (!root.contextTargetIsDir && root.contextTargetSelection.length === 1)
                     || (root.contextTargetFileSelection.length > 1)
            onTriggered: {
                if (root.contextTargetFileSelection.length > 1) {
                    root.renameRequested(root.contextTargetFileSelection)
                    return
                }
                root.renameRequested([root.contextTargetPath])
            }
        }
        MenuItem {
            text: qsTr("Loeschen")
            enabled: root.contextTargetFileSelection.length > 0
            onTriggered: root.deleteRequested(root.contextTargetFileSelection)
        }
        MenuSeparator {}
        MenuItem {
            text: qsTr("In neuen Ordner verschieben")
            enabled: root.contextTargetSelection.length > 1
            onTriggered: root.moveSelectedIntoNewFolderRequested(root.contextTargetSelection)
        }
    }

    Shortcut {
        sequences: [StandardKey.New]
        onActivated: root.createNoteRequested()
    }
}
