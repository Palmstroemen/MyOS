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

    onShowFoldersChanged: filterChanged(showFolders)

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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
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
                fillColor: root.itemFillColor
                strokeColor: root.itemBorderColor
                textColor: root.text
                textSize: root.baseFont
                largeIconAlignLeft: false
                dragEnabled: root.allowDrags
                    && (!model.isEmbryo)
                    && model.path !== undefined
                    && model.path.length > 0
                dragPayload: model.path ? model.path : ""
                onDoubleActivate: {
                    if (model.isDir) {
                        root.folderActivated(model.name)
                    } else {
                        root.fileActivated(model.name)
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
    }
}
