import QtQuick 2.15
import QtQuick.Controls 2.15
import "Theme/tag_chips.js" as TagChips

// The tools row at the top of M's dropdown below the CWD: what would hide behind a menu lies
// here as buttons (Designdocument Perspective Resolver MVP.md, E4). It only shows the state
// handed in and says what is wanted; the host does it. M is becoming a tool of its own, docked
// at the top of the screen, so there is no switch to the full view here.
Row {
    id: root
    spacing: 4

    property int buttonSize: 28
    property int baseFont: 13
    property color pill: "#2c3f5d"
    property color pillBorder: "#5f7297"
    property color pillActive: "#496a97"
    property color textColor: "#e8efff"
    property real emptyOpacity: 0.45

    property bool clipboardHasItems: false
    property bool darkTheme: true
    property string language: "de"
    property bool hiddenShown: false

    signal openClipboard()
    signal clipboardDrop(var drop)
    signal switchTheme()
    signal switchLanguage()
    signal toggleHidden()
    signal openSetup()

    component Tool: Rectangle {
        id: tool
        property string label: ""
        property string iconSource: ""
        property string tip: ""
        property bool checked: false
        signal activated()
        width: root.buttonSize
        height: root.buttonSize
        radius: TagChips.CHIP_RADIUS_COMPACT
        color: checked || toolArea.containsMouse ? root.pillActive : root.pill
        border.color: root.pillBorder
        Text {
            visible: tool.iconSource === ""
            anchors.centerIn: parent
            text: tool.label
            color: root.textColor
            font.pixelSize: root.baseFont
            font.bold: true
        }
        Image {
            visible: tool.iconSource !== ""
            anchors.fill: parent
            anchors.margins: 3
            source: tool.iconSource
            fillMode: Image.PreserveAspectFit
        }
        MouseArea {
            id: toolArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: tool.activated()
        }
        ToolTip.visible: toolArea.containsMouse && tool.tip !== ""
        ToolTip.delay: 600
        ToolTip.text: tool.tip
    }

    Tool {
        objectName: "toolClipboard"
        label: "C"
        tip: qsTr("Clipboard - drop here to collect")
        opacity: root.clipboardHasItems ? 1.0 : root.emptyOpacity
        onActivated: root.openClipboard()
        DropArea {
            anchors.fill: parent
            onDropped: function(drop) { root.clipboardDrop(drop) }
        }
    }
    Tool {
        objectName: "toolTheme"
        label: "◐"
        tip: root.darkTheme ? qsTr("Light") : qsTr("Dark")
        onActivated: root.switchTheme()
    }
    Tool {
        objectName: "toolLanguage"
        label: root.language.toUpperCase()
        tip: qsTr("Language")
        onActivated: root.switchLanguage()
    }
    Tool {
        objectName: "toolHidden"
        label: ".*"
        checked: root.hiddenShown
        tip: qsTr("Show hidden folders")
        onActivated: root.toggleHidden()
    }
    Tool {
        objectName: "toolSetup"
        label: "⚙"
        tip: qsTr("Setup")
        onActivated: root.openSetup()
    }
}
