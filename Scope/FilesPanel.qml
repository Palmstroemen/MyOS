import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle { // Files panel
    id: root
    property var files: []
    property int baseFont: 14
    property color text: "#e6e6e6"
    property color textMuted: "#c9ccd7"
    property color panelAlt: "#151821"
    property color pillBorder: "#3a4158"
    property color backgroundColor: "#404040"
    property color itemFillColor: "#151821"
    property color itemBorderColor: "#3a4158"
    property bool halfTransparent: false
    property real templatesBrowserWidth: 0
    property real projectsBrowserWidth: 0
    property string iconSource: ""
    property string itemStyle: "largeIcon"
    property int compactButtonHeight: 32
    property int largeButtonHeight: 88
    property int largeButtonPadding: 6
    property int iconSizeSmall: 24
    property int iconSizeLarge: 64

    radius: 8
    color: backgroundColor
    border.color: pillBorder
    implicitWidth: 0
    implicitHeight: 0
    opacity: halfTransparent ? 0.5 : 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        Flow {
            Layout.fillWidth: true
            spacing: 8
            width: parent.width
            Repeater {
                model: root.files
                delegate: FolderItem {
                    label: modelData
                    style: root.itemStyle
                    compactHeight: root.compactButtonHeight
                    largeHeight: root.largeButtonHeight
                    largePadding: root.largeButtonPadding
                    iconSmall: root.iconSizeSmall
                    iconLarge: root.iconSizeLarge
                    iconSource: root.iconSource
                    fillColor: root.itemFillColor
                    strokeColor: root.itemBorderColor
                    textColor: root.text
                    textSize: root.baseFont
                    largeIconAlignLeft: false
                }
            }
        }
    }
}
