import QtQuick 2.15
import QtQuick.Controls 2.15
import "Theme/tag_chips.js" as TagChips

Rectangle {
    id: root
    property string label: ""
    property string style: "text" // text | smallIcon | largeIcon
    property int compactHeight: 32
    property int largeHeight: 88
    property int iconSmall: 24
    property int iconLarge: 64
    property int largePadding: 3
    property string iconSource: ""
    property string thumbnailSource: ""
    property color fillColor: "#3b476b"
    property color strokeColor: "#58648a"
    property color textColor: "#cfd3df"
    property int textSize: 14
    property int largeTextSize: textSize
    property bool textBold: false
    property bool largeTextBold: textBold
    property int textYOffset: 0
    property bool renaming: false
    property bool renameEnabled: false
    property string renameText: ""
    property int textLeftInset: 0
    property bool largeIconAlignLeft: false
    property bool dragEnabled: false
    property string dragPayload: ""
    property bool flatBottomCorners: false
    property bool tabHoverDropEnabled: false
    property int tabHoverDropPx: 7
    readonly property bool hoverActive: hitArea.containsMouse
    property bool tabPinned: false
    property real tabDropOffset: (tabHoverDropEnabled && (hoverActive || tabPinned)) ? tabHoverDropPx : 0
    signal activate(bool ctrlPressed, bool shiftPressed)
    signal doubleActivate()
    signal hoverEntered()
    signal contextMenuRequested(real x, real y, bool ctrlPressed)
    signal renameRequested()
    signal renameTextEdited(string text)
    signal renameAccepted()
    signal renameCanceled()

    function _containsItemPoint(item, px, py) {
        if (!item || !item.visible) {
            return false
        }
        var local = root.mapToItem(item, px, py)
        return local.x >= 0 && local.y >= 0 && local.x <= item.width && local.y <= item.height
    }

    function _containsTextGlyph(textItem, px, py) {
        if (!textItem || !textItem.visible) {
            return false
        }
        var local = root.mapToItem(textItem, px, py)
        var glyphW = Math.max(1, Math.min(textItem.width, textItem.paintedWidth || textItem.width))
        var glyphH = Math.max(1, Math.min(textItem.height, textItem.paintedHeight || textItem.height))
        var glyphX = Math.max(0, (textItem.width - glyphW) / 2)
        var glyphY = Math.max(0, (textItem.height - glyphH) / 2)
        return local.x >= glyphX && local.x <= (glyphX + glyphW)
            && local.y >= glyphY && local.y <= (glyphY + glyphH)
    }

    function hitAcceptsPoint(px, py) {
        if (renaming) {
            return true
        }
        if (style === "text") {
            return _containsTextGlyph(textLabel, px, py)
        }
        if (style === "smallIcon") {
            return _containsItemPoint(smallIconImage, px, py) || _containsTextGlyph(smallIconLabel, px, py)
        }
        if (style === "largeIcon") {
            return _containsItemPoint(largeIconImage, px, py) || _containsTextGlyph(largeIconLabel, px, py)
        }
        return false
    }

    function twoLineLabel(text, maxChars) {
        if (!text) return ""
        var clean = String(text)
        var dotIndex = clean.lastIndexOf(".")
        if (dotIndex > 0 && dotIndex < clean.length - 1) {
            clean = clean.slice(0, dotIndex)
        }
        if (clean.length <= maxChars) {
            return clean
        }
        if (clean.length <= (maxChars * 2)) {
            var breakIdx = clean.lastIndexOf(" ", maxChars)
            if (breakIdx < Math.max(1, maxChars - 6)) {
                breakIdx = clean.indexOf(" ", maxChars)
            }
            if (breakIdx > 0 && breakIdx < clean.length - 1) {
                return clean.slice(0, breakIdx) + "\n" + clean.slice(breakIdx + 1)
            }
            return clean.slice(0, maxChars) + "\n" + clean.slice(maxChars)
        }
        var head = clean.slice(0, maxChars)
        var tail = clean.slice(Math.max(0, clean.length - maxChars))
        return head + "...\n..." + tail
    }

    radius: TagChips.CHIP_RADIUS_MEDIUM
    transform: [
        Translate { y: root.tabDropOffset }
    ]
    Behavior on tabDropOffset {
        NumberAnimation {
            duration: 170
            easing.type: Easing.OutCubic
        }
    }
    height: style === "largeIcon" ? largeHeight : compactHeight
    color: fillColor
    border.color: strokeColor

    Rectangle {
        // Optional "tab" mode: visually flatten lower corners.
        visible: root.flatBottomCorners && root.radius > 0
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: root.radius
        color: root.fillColor
        border.width: 0
    }
    Rectangle {
        visible: root.flatBottomCorners
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: root.strokeColor
        z: 2
    }
    Rectangle {
        visible: root.flatBottomCorners
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: 1
        height: Math.max(1, root.radius)
        color: root.strokeColor
        z: 2
    }
    Rectangle {
        visible: root.flatBottomCorners
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 1
        height: Math.max(1, root.radius)
        color: root.strokeColor
        z: 2
    }

    DragHandler {
        id: dragHandler
        enabled: dragEnabled
    }

    Drag.active: dragEnabled && dragHandler.active
    Drag.hotSpot.x: width / 2
    Drag.hotSpot.y: height / 2
    Drag.mimeData: (dragEnabled && dragPayload.length > 0) ? { "text/plain": dragPayload } : {}
    Drag.supportedActions: Qt.MoveAction

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
            id: textLabel
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: textYOffset
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
            id: smallIconImage
            source: thumbnailSource !== "" ? thumbnailSource : iconSource
            width: iconSmall
            height: iconSmall
            fillMode: Image.PreserveAspectFit
            sourceSize.width: width
            sourceSize.height: height
        }
        Text {
            id: smallIconLabel
            text: label
            color: textColor
            font.pixelSize: textSize
            font.bold: textBold
            y: textYOffset
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
            id: largeIconImage
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
            id: largeIconLabel
            text: twoLineLabel(label, 16)
            color: textColor
            font.pixelSize: largeTextSize
            font.bold: largeTextBold
            horizontalAlignment: largeIconAlignLeft ? Text.AlignLeft : Text.AlignHCenter
            width: parent.width
            visible: !renaming
            wrapMode: Text.NoWrap
            y: textYOffset
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
        id: hitArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        onClicked: function(mouse) {
            if (renaming) return
            if (!root.hitAcceptsPoint(mouse.x, mouse.y)) {
                mouse.accepted = false
                return
            }
            if (mouse.button === Qt.RightButton) {
                root.contextMenuRequested(mouse.x, mouse.y, (mouse.modifiers & Qt.ControlModifier) !== 0)
                return
            }
            root.activate(
                (mouse.modifiers & Qt.ControlModifier) !== 0,
                (mouse.modifiers & Qt.ShiftModifier) !== 0
            )
        }
        onDoubleClicked: function(mouse) {
            if (renaming) return
            if (!root.hitAcceptsPoint(mouse.x, mouse.y)) {
                mouse.accepted = false
                return
            }
            root.doubleActivate()
        }
        onEntered: root.hoverEntered()
        onPositionChanged: function(mouse) {
            if (tabHoverDropEnabled && containsMouse && !renaming) {
                root.hoverEntered()
            }
        }
        onPressAndHold: {
            if (renameEnabled) root.renameRequested()
        }
    }
}
