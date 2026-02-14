import QtQuick 2.15
import QtQuick.Layouts 1.15

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
    property real projectTintOpacity: 1.0
    property bool allowDrags: true
    property bool halfTransparent: false
    property bool showFolders: false
    property var availableTags: []
    property var selectedTags: []
    property var selectedPaths: []
    property string tagSource: "project"
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
    property int gridSpacing: 8
    property int prefetchThreshold: 200

    radius: 8
    color: backgroundColor
    border.color: pillBorder
    implicitWidth: 0
    implicitHeight: 0
    opacity: halfTransparent ? 0.5 : 1

    signal requestMore()
    signal filterChanged(bool showFolders)
    signal tagToggled(string tag)
    signal requestTagSourceChange(string source)
    signal itemActivated(string path, bool ctrlPressed)
    signal selectionBoxApplied(var paths, bool additive)
    signal moveEntriesRequested(string payload, string targetDir)

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

    Column {
        id: cornerButtons
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 8
        anchors.rightMargin: 8
        spacing: 6
        z: 2

        Rectangle {
            radius: 6
            width: root.compactButtonHeight
            height: root.compactButtonHeight
            color: root.showFolders ? root.smallButtonActiveBg : root.smallButtonBg
            border.color: root.showFolders ? root.smallButtonActiveBorder : root.smallButtonBorder
            Image {
                anchors.centerIn: parent
                source: root.showFolders ? root.iconFolder : root.iconFolderOff
                width: root.smallIconSize
                height: root.smallIconSize
                fillMode: Image.PreserveAspectFit
                sourceSize.width: width
                sourceSize.height: height
            }
            MouseArea {
                anchors.fill: parent
                onClicked: root.showFolders = !root.showFolders
            }
        }

        Rectangle {
            radius: 6
            width: root.compactButtonHeight
            height: root.compactButtonHeight
            color: root.smallButtonBg
            border.color: root.smallButtonBorder
            visible: root.showMyosButton
            Image {
                anchors.centerIn: parent
                source: root.iconGear
                width: root.smallIconSize
                height: root.smallIconSize
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
            radius: 6
            width: root.compactButtonHeight
            height: root.compactButtonHeight
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
    }

    Rectangle {
        id: tagBar
        anchors.top: cornerButtons.bottom
        anchors.right: parent.right
        anchors.topMargin: 8
        anchors.rightMargin: 8
        width: Math.max(96, Math.min(180, Math.round(parent.width * 0.22)))
        height: Math.max(80, parent.height - cornerButtons.height - 24)
        visible: (root.availableTags && root.availableTags.length > 0)
        radius: 8
        color: Qt.rgba(root.panelAlt.r, root.panelAlt.g, root.panelAlt.b, 0.36)
        border.color: Qt.rgba(root.pillBorder.r, root.pillBorder.g, root.pillBorder.b, 0.6)
        z: 2

        Column {
            anchors.fill: parent
            anchors.margins: 6
            spacing: 6

            Row {
                width: parent.width
                spacing: 6

                Rectangle {
                    width: (parent.width - 6) / 2
                    height: root.compactButtonHeight
                    radius: 6
                    color: root.tagSource === "project" ? root.smallButtonActiveBg : Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, 0.65)
                    border.color: root.tagSource === "project" ? root.smallButtonActiveBorder : root.smallButtonBorder
                    Text {
                        anchors.centerIn: parent
                        text: "Project"
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
                    radius: 6
                    color: root.tagSource === "visible" ? root.smallButtonActiveBg : Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, 0.65)
                    border.color: root.tagSource === "visible" ? root.smallButtonActiveBorder : root.smallButtonBorder
                    Text {
                        anchors.centerIn: parent
                        text: "Visible"
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
                            height: Math.max(22, Math.round(root.compactButtonHeight * 0.84))
                            radius: 6
                            readonly property string tagValue: modelData
                            readonly property bool selected: root.selectedTags && root.selectedTags.indexOf(tagValue) !== -1
                            color: selected
                                ? Qt.rgba(root.projectTint.r, root.projectTint.g, root.projectTint.b, 0.70)
                                : Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, 0.45)
                            border.color: selected
                                ? Qt.rgba(root.projectTintBorder.r, root.projectTintBorder.g, root.projectTintBorder.b, 0.9)
                                : Qt.rgba(root.smallButtonBorder.r, root.smallButtonBorder.g, root.smallButtonBorder.b, 0.7)

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

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.topMargin: 16
        anchors.bottomMargin: 16
        anchors.rightMargin: tagBar.visible ? (tagBar.width + 16) : 16
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
                onActivate: function(ctrlPressed) {
                    root.itemActivated(itemPath, ctrlPressed)
                }
                onDoubleActivate: {
                    if (model.isDir) {
                        root.folderActivated(model.name)
                    } else {
                        root.fileActivated(model.name)
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
            anchors.fill: filesGrid
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
                acceptedButtons: Qt.LeftButton
                hoverEnabled: false
                preventStealing: true

                onPressed: function(mouse) {
                    var idx = filesGrid.indexAt(mouse.x + filesGrid.contentX, mouse.y + filesGrid.contentY)
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
                    }
                    selectionOverlay.marqueeActive = false
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
}
