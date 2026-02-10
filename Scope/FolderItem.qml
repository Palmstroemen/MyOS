import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    property string label: ""
    property string style: "text" // text | smallIcon | largeIcon
    property int compactHeight: 32
    property int largeHeight: 88
    property int iconSmall: 24
    property int iconLarge: 64
    property int largePadding: 6
    property string iconSource: ""
    property string thumbnailSource: ""
    property color fillColor: "#3b476b"
    property color strokeColor: "#58648a"
    property color textColor: "#cfd3df"
    property int textSize: 14
    property int largeTextSize: textSize
    property bool textBold: false
    property bool largeTextBold: textBold
    property bool renaming: false
    property bool renameEnabled: false
    property string renameText: ""
    property int textLeftInset: 0
    property bool largeIconAlignLeft: false
    signal activate()
    signal doubleActivate()
    signal renameRequested()
    signal renameTextEdited(string text)
    signal renameAccepted()
    signal renameCanceled()

    radius: 6
    height: style === "largeIcon" ? largeHeight : compactHeight
    color: fillColor
    border.color: strokeColor

    implicitWidth: {
        var base = textMeasure.width + 24
        if (style === "smallIcon") {
            return Math.max(80, base + iconSmall + 6)
        }
        if (style === "largeIcon") {
            return Math.max(80, Math.max(iconLarge, textMeasure.width) + 20)
        }
        return Math.max(80, base)
    }

    Item {
        anchors.fill: parent
        visible: !renaming && style === "text"
        Text {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: textLeftInset
            anchors.right: parent.right
            anchors.rightMargin: textLeftInset
            horizontalAlignment: textLeftInset > 0 ? Text.AlignLeft : Text.AlignHCenter
            text: label
            color: textColor
            font.pixelSize: textSize
            font.bold: textBold
        }
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 6
        anchors.verticalCenter: parent.verticalCenter
        spacing: 6
        visible: style === "smallIcon"
        Image {
            source: thumbnailSource !== "" ? thumbnailSource : iconSource
            width: iconSmall
            height: iconSmall
            fillMode: Image.PreserveAspectFit
            sourceSize.width: width
            sourceSize.height: height
        }
        Text {
            text: label
            color: textColor
            font.pixelSize: textSize
            font.bold: textBold
            visible: !renaming
        }
    }

    Column {
        anchors.top: parent.top
        anchors.topMargin: largePadding
        anchors.left: largeIconAlignLeft ? parent.left : undefined
        anchors.leftMargin: largeIconAlignLeft ? 6 : 0
        anchors.horizontalCenter: largeIconAlignLeft ? undefined : parent.horizontalCenter
        width: parent.width
        spacing: 2
        visible: style === "largeIcon"
        Image {
            source: thumbnailSource !== "" ? thumbnailSource : iconSource
            width: iconLarge
            height: iconLarge
            fillMode: Image.PreserveAspectFit
            anchors.left: largeIconAlignLeft ? parent.left : undefined
            anchors.leftMargin: largeIconAlignLeft ? 6 : 0
            anchors.horizontalCenter: largeIconAlignLeft ? undefined : parent.horizontalCenter
            sourceSize.width: width
            sourceSize.height: height
        }
        Text {
            text: label
            color: textColor
            font.pixelSize: largeTextSize
            font.bold: largeTextBold
            horizontalAlignment: largeIconAlignLeft ? Text.AlignLeft : Text.AlignHCenter
            width: parent.width
            visible: !renaming
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
    }

    TextField {
        anchors.fill: parent
        anchors.margins: 4
        visible: renaming && style === "text"
        text: renameText
        font.pixelSize: textSize
        horizontalAlignment: Text.AlignHCenter
        selectByMouse: true
        color: textColor
        placeholderTextColor: textColor
        verticalAlignment: Text.AlignVCenter
        leftPadding: 6
        rightPadding: 6
        topPadding: 1
        bottomPadding: 0
        background: Rectangle { color: "transparent" }
        onTextChanged: renameTextEdited(text)
        onVisibleChanged: {
            if (visible) {
                forceActiveFocus()
                selectAll()
            }
        }
        Keys.onReturnPressed: renameAccepted()
        Keys.onEscapePressed: renameCanceled()
    }

    TextField {
        anchors.fill: parent
        anchors.margins: 4
        visible: renaming && style === "smallIcon"
        text: renameText
        font.pixelSize: textSize
        horizontalAlignment: Text.AlignLeft
        selectByMouse: true
        color: textColor
        placeholderTextColor: textColor
        verticalAlignment: Text.AlignVCenter
        leftPadding: iconSmall + 12
        rightPadding: 6
        topPadding: 1
        bottomPadding: 0
        background: Rectangle { color: "transparent" }
        onTextChanged: renameTextEdited(text)
        onVisibleChanged: {
            if (visible) {
                forceActiveFocus()
                selectAll()
            }
        }
        Keys.onReturnPressed: renameAccepted()
        Keys.onEscapePressed: renameCanceled()
    }

    TextField {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 6
        anchors.rightMargin: 6
        anchors.bottomMargin: largePadding
        height: 24
        visible: renaming && style === "largeIcon"
        text: renameText
        font.pixelSize: largeTextSize
        horizontalAlignment: Text.AlignHCenter
        selectByMouse: true
        color: textColor
        placeholderTextColor: textColor
        verticalAlignment: Text.AlignVCenter
        leftPadding: 6
        rightPadding: 6
        topPadding: 1
        bottomPadding: 0
        background: Rectangle { color: "transparent" }
        onTextChanged: renameTextEdited(text)
        onVisibleChanged: {
            if (visible) {
                forceActiveFocus()
                selectAll()
            }
        }
        Keys.onReturnPressed: renameAccepted()
        Keys.onEscapePressed: renameCanceled()
    }

    Text {
        id: textMeasure
        text: label
        visible: false
        font.pixelSize: style === "largeIcon" ? largeTextSize : textSize
        font.bold: textBold
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (renaming) return
            root.activate()
        }
        onDoubleClicked: {
            if (renaming) return
            root.doubleActivate()
        }
        onPressAndHold: {
            if (renameEnabled) root.renameRequested()
        }
    }
}
