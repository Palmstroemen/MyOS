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
    property color backgroundColor: "#b0b0b0"
    property bool halfTransparent: false
    property real templatesBrowserWidth: 0
    property real projectsBrowserWidth: 0
    property int itemHeight: 36
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

        Text {
            text: "Files Panel"
            color: root.textMuted
            font.pixelSize: root.baseFont
        }
        Text {
            text: "FB widths: T=" + Math.round(root.templatesBrowserWidth) +
                  " P=" + Math.round(root.projectsBrowserWidth)
            color: root.text
            font.pixelSize: Math.max(10, root.baseFont - 2)
        }
        Repeater {
            model: root.files
            delegate: Rectangle {
                Layout.fillWidth: true
                height: root.itemHeight
                radius: 6
                color: root.panelAlt
                border.color: root.pillBorder
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 12
                    text: modelData
                    color: root.text
                    font.pixelSize: root.baseFont
                }
            }
        }
    }
}
