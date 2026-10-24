import QtQuick 2.15
import QtQuick.Controls 2.15
import "js/DropUtils.js" as DropUtils
import "Theme/tag_chips.js" as TagChips

Rectangle {
    // An italic "P" in the style of the text badges, top right, for projects that already
    // carry an image badge (projects without one show the "P" as their text badge).
    component ProjectBadge: Text {
        visible: root.projectBadge && root.batchSource !== ""
        anchors.right: parent.right
        anchors.top: parent.top
        text: "P"
        color: "#000000"
        font.bold: true
        font.italic: true
        font.pixelSize: Math.max(8, Math.round(parent.height * 0.32))
    }

    id: root
    property string label: ""
    property string style: "text" // text | smallIcon | largeIcon
    property int compactHeight: 32
    property int largeHeight: 88
    property int iconSmall: 24
    property int iconLarge: 64
    property int largePadding: 3
    property string iconSource: ""
    property string iconSourceHover: ""
    property string thumbnailSource: ""
    property string batchSource: ""
    property string batchText: ""
    /// The folder is a project: a small "P" at the top right of its icon.
    property bool projectBadge: false
    /// The text badge drawn: the folder's own, else "P" for a project without a badge.
    readonly property string shownBatchText: batchText || (projectBadge && !batchSource ? "P" : "")
    readonly property bool shownBatchIsProjectP: !batchText && projectBadge && !batchSource
    /// X-ray view: the folder this file is seen through ("Rechnungen/2024"); a large, faint
    /// folder (xrayFolderSource) lies behind the file's icon, without a name.
    property string xrayVia: ""
    property string xrayFolderSource: ""
    component XrayFolder: Image {
        visible: root.xrayVia !== "" && root.xrayFolderSource !== ""
        z: -1
        anchors.centerIn: parent
        // A little higher: clear of the name below, clearly above the file's icon.
        anchors.verticalCenterOffset: -Math.round(height * 0.05)
        width: parent.width * 1.6
        height: parent.height * 1.6
        source: root.xrayFolderSource
        opacity: 0.3
        fillMode: Image.PreserveAspectFit
        sourceSize.width: width
        sourceSize.height: height
    }
    ToolTip.visible: xrayVia !== "" && hitArea.containsMouse
    ToolTip.delay: 600
    ToolTip.text: qsTr("in %1").arg(xrayVia)
    /// Behind the name (e.g. the project's colour in the FilesPanel); transparent: none.
    property color labelBackground: "transparent"
    component LabelBackground: Rectangle {
        z: -1
        visible: root.labelBackground.a > 0
        color: Qt.rgba(root.labelBackground.r, root.labelBackground.g, root.labelBackground.b, 0.45)
        radius: 3
        height: parent.contentHeight + 2
        y: (parent.height - height) / 2
    }
    property color fillColor: "#3b476b"
    property color strokeColor: "#58648a"
    // Nur bei bewusst halbtransparentem Fill (0 < a < 1) Icons mitschattieren; bei transparent (a=0) oder opak (a=1) Icons voll sichtbar
    readonly property real iconOpacity: (typeof fillColor.a === "number" && fillColor.a > 0 && fillColor.a < 1) ? fillColor.a : 1
    property color textColor: "#cfd3df"
    property int textSize: 14
    property int largeTextSize: textSize
    property bool textBold: false
    property bool largeTextBold: textBold
    property bool dimmedStyle: false
    property int textYOffset: 0
    property bool renaming: false
    property bool renameEnabled: false
    property string renameText: ""
    property string _renameEditText: ""
    onRenamingChanged: if (renaming) _renameEditText = renameText
    property int textLeftInset: 0
    property bool largeIconAlignLeft: false
    /// List style ("smallIcon") only: columns [{text, width, align, x}] with x from the row
    /// start; columns may sit left and right of the name. Geometry matches the FilesPanel
    /// header. nameOffsetX moves icon and name right of the left columns; nameColumnWidth
    /// (0 = unlimited) is the width of icon plus name, longer names are elided.
    property var detailColumns: []
    property int nameOffsetX: 0
    property int nameColumnWidth: 0
    property bool dragEnabled: false
    property bool allowDrops: false
    property string dragPayload: ""
    property bool flatBottomCorners: false
    /// Narrow button (minimal view): in "smallIcon" the icon forms the left edge, as high
    /// as the button; only a little room after the name.
    property bool edgeIcon: false
    readonly property int smallIconBox: edgeIcon ? compactHeight : iconSmall
    property bool tabHoverDropEnabled: false
    property int tabHoverDropPx: 7
    readonly property bool hoverActive: hitArea.containsMouse
    property real batchBottomMargin: hoverActive ? TagChips.BATCH_BOTTOM_MARGIN_HOVER : TagChips.BATCH_BOTTOM_MARGIN_DEFAULT
    property bool tabPinned: false
    property bool showPin: false
    property string iconPin: ""
    property real tabDropOffset: (tabHoverDropEnabled && (hoverActive || tabPinned)) ? tabHoverDropPx : 0
    property bool isCwdMainPanelItem: false
    property bool hitAreaFullButton: false
    property bool pendingSingleClick: false
    property bool pendingSingleClickCtrl: false
    property bool pendingSingleClickShift: false
    signal activate(bool ctrlPressed, bool shiftPressed)
    signal doubleActivate()
    signal hoverEntered()
    signal contextMenuRequested(real x, real y, bool ctrlPressed)
    signal renameRequested()
    signal renameTextEdited(string text)
    signal renameAccepted(string newName)
    signal renameCanceled()
    signal dropReceived(string payload)

    property var onDrop: null
    readonly property bool containsDrag: (typeof dropArea !== "undefined" && dropArea) ? Boolean(dropArea.containsDrag) : false

    function _dropPayload(drop) {
        return DropUtils.payloadText(drop)
    }

    function dispatchPendingSingleClick() {
        if (!pendingSingleClick) {
            return
        }
        pendingSingleClick = false
        root.activate(pendingSingleClickCtrl, pendingSingleClickShift)
    }

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
        var glyphX = (textItem.horizontalAlignment === Text.AlignLeft) ? 0 : Math.max(0, (textItem.width - glyphW) / 2)
        var glyphY = Math.max(0, (textItem.height - glyphH) / 2)
        return local.x >= glyphX && local.x <= (glyphX + glyphW)
            && local.y >= glyphY && local.y <= (glyphY + glyphH)
    }

    function hitAcceptsPoint(px, py) {
        if (renaming) {
            return true
        }
        if (hitAreaFullButton) {
            return px >= 0 && px <= width && py >= 0 && py <= height
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
    Behavior on batchBottomMargin {
        NumberAnimation {
            duration: 120
            easing.type: Easing.OutCubic
        }
    }
    height: style === "largeIcon" ? largeHeight : compactHeight
    color: fillColor
    border.color: strokeColor

    Rectangle {
        // Selected-tab overlay: subtle white fade from top to bottom.
        visible: root.dimmedStyle
        anchors.fill: parent
        radius: root.radius
        border.width: 0
        color: "transparent"
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.15) }
            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.0) }
        }
    }

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
        z: 0
    }
    Rectangle {
        visible: root.flatBottomCorners
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: 1
        height: Math.max(1, root.radius)
        color: root.strokeColor
        z: 1
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
        onActiveChanged: {
            if (!active && dragEnabled) {
                root.Drag.drop()
            }
        }
    }

    Drag.active: dragEnabled && dragHandler.active
    Drag.hotSpot.x: width / 2
    Drag.hotSpot.y: height / 2
    Drag.mimeData: (dragEnabled && dragPayload.length > 0) ? { "text/plain": dragPayload } : {}
    Drag.supportedActions: Qt.MoveAction

    implicitWidth: {
        if (edgeIcon && style !== "largeIcon") {
            var tight = style === "smallIcon" ? smallIconBox + 4 + textMeasure.width + 8 : textMeasure.width + 16
            return Math.max(2 * compactHeight, tight)
        }
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
        anchors.leftMargin: (root.edgeIcon ? 0 : 6) + root.nameOffsetX
        anchors.verticalCenter: parent.verticalCenter
        spacing: root.edgeIcon ? 4 : 6
        visible: style === "smallIcon"
        Item {
            width: root.smallIconBox
            height: root.smallIconBox
            readonly property bool hasBatch: Boolean(batchSource || shownBatchText)
            XrayFolder {}
            // Small icon: when batch exists, show only batch at full icon size (no folder + overlay).
            Image {
                id: smallIconImage
                anchors.fill: parent
                visible: !parent.hasBatch
                source: thumbnailSource !== "" ? thumbnailSource : (hoverActive && iconSourceHover ? iconSourceHover : iconSource)
                opacity: root.iconOpacity
                fillMode: Image.PreserveAspectFit
                sourceSize.width: width
                sourceSize.height: height
            }
            Item {
                visible: parent.hasBatch
                anchors.fill: parent
                Rectangle {
                    anchors.fill: parent
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: "#eeeeee"
                }
                Image {
                    visible: batchSource
                    anchors.fill: parent
                    source: batchSource
                    fillMode: Image.PreserveAspectFit
                    sourceSize.width: width
                    sourceSize.height: height
                }
                Text {
                    visible: shownBatchText && !batchSource
                    anchors.centerIn: parent
                    text: shownBatchText
                    color: "#000000"
                    font.bold: true
                    font.italic: true
                    font.pixelSize: Math.max(8, parent.height * 0.85)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            ProjectBadge {}
        }
        Text {
            id: smallIconLabel
            text: label
            color: textColor
            font.pixelSize: textSize
            font.bold: textBold
            // Beside the button-high icon the name is centred; the row is as high as the icon.
            y: (root.edgeIcon ? Math.round((root.smallIconBox - height) / 2) : 0) + textYOffset
            visible: !renaming
            // Leave room for the detail column instead of running into it.
            // The name ends where the next column starts (long names are elided).
            width: root.nameColumnWidth > 0
                ? Math.min(implicitWidth, Math.max(0, root.nameColumnWidth - iconSmall - 18))
                : implicitWidth
            elide: Text.ElideRight
            LabelBackground {
                x: -4
                width: parent.width + 8
            }
        }
    }

    Item {
        id: smallIconDetails
        // root.* throughout: inside a Text, a bare "style" would be Text.style.
        visible: root.style === "smallIcon" && root.detailColumns.length > 0 && !root.renaming
        anchors.left: parent.left
        anchors.leftMargin: 6
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        Repeater {
            model: root.detailColumns
            delegate: Text {
                x: modelData.x
                width: modelData.width
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: root.textYOffset
                horizontalAlignment: modelData.align === "right" ? Text.AlignRight : Text.AlignLeft
                text: modelData.text
                color: root.textColor
                opacity: 0.7
                font.pixelSize: Math.max(9, Math.round(root.textSize * 0.85))
                elide: modelData.align === "right" ? Text.ElideLeft : Text.ElideRight
            }
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
        Item {
            width: iconLarge
            height: iconLarge
            anchors.left: largeIconAlignLeft ? parent.left : undefined
            anchors.leftMargin: largeIconAlignLeft ? 6 : 0
            anchors.horizontalCenter: largeIconAlignLeft ? undefined : parent.horizontalCenter
            XrayFolder {}
            Image {
                id: largeIconImage
                anchors.fill: parent
                source: thumbnailSource !== "" ? thumbnailSource : (hoverActive && iconSourceHover ? iconSourceHover : iconSource)
                opacity: root.iconOpacity
                fillMode: Image.PreserveAspectFit
                sourceSize.width: width
                sourceSize.height: height
            }
            Item {
                visible: batchSource || shownBatchText
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                height: parent.height * TagChips.BATCH_HEIGHT_FRAC
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * root.batchBottomMargin
                // No background here: the batch sits on the folder icon, a light box behind
                // it would be wider than the folder (the small icon keeps its box: there the
                // batch replaces the folder).
                Image {
                    visible: batchSource
                    anchors.centerIn: parent
                    width: parent.height
                    height: parent.height
                    source: batchSource
                    fillMode: Image.PreserveAspectFit
                }
                Text {
                    visible: shownBatchText && !batchSource
                    anchors.centerIn: parent
                    // The project's P sits a little right of centre.
                    anchors.horizontalCenterOffset: root.shownBatchIsProjectP ? parent.width * 0.18 : 0
                    text: shownBatchText
                    color: "#000000"
                    font.bold: true
                    font.italic: true
                    font.pixelSize: Math.max(8, parent.height * 0.85)
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            ProjectBadge {}
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
            LabelBackground {
                width: Math.min(parent.width, parent.contentWidth + 8)
                x: root.largeIconAlignLeft ? -4 : (parent.width - width) / 2
            }
        }
    }

    TextField {
        anchors.fill: parent
        anchors.margins: 4
        visible: renaming && style === "text"
        text: root._renameEditText
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
        onTextChanged: {
            root._renameEditText = text
            root.renameTextEdited(text)
        }
        onVisibleChanged: {
            if (visible) {
                forceActiveFocus()
                selectAll()
            }
        }
        Keys.onReturnPressed: renameAccepted(root._renameEditText)
        Keys.onEscapePressed: renameCanceled()
    }

    TextField {
        anchors.fill: parent
        anchors.margins: 4
        // Starts where the name starts (left columns may come first in the list).
        anchors.leftMargin: 4 + root.nameOffsetX
        visible: renaming && style === "smallIcon"
        text: root._renameEditText
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
        onTextChanged: {
            root._renameEditText = text
            root.renameTextEdited(text)
        }
        onVisibleChanged: {
            if (visible) {
                forceActiveFocus()
                selectAll()
            }
        }
        Keys.onReturnPressed: renameAccepted(root._renameEditText)
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
        text: root._renameEditText
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
        onTextChanged: {
            root._renameEditText = text
            root.renameTextEdited(text)
        }
        onVisibleChanged: {
            if (visible) {
                forceActiveFocus()
                selectAll()
            }
        }
        Keys.onReturnPressed: renameAccepted(root._renameEditText)
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
            var hit = root.hitAcceptsPoint(mouse.x, mouse.y)
            if (!hit) {
                mouse.accepted = false
                return
            }
            if (mouse.button === Qt.RightButton) {
                root.contextMenuRequested(mouse.x, mouse.y, (mouse.modifiers & Qt.ControlModifier) !== 0)
                return
            }
            pendingSingleClickCtrl = (mouse.modifiers & Qt.ControlModifier) !== 0
            pendingSingleClickShift = (mouse.modifiers & Qt.ShiftModifier) !== 0
            pendingSingleClick = true
            singleClickTimer.restart()
        }
        onDoubleClicked: function(mouse) {
            if (renaming) return
            var hitOk = root.hitAcceptsPoint(mouse.x, mouse.y)
            if (!hitOk) {
                mouse.accepted = false
                return
            }
            pendingSingleClick = false
            singleClickTimer.stop()
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

    Timer {
        id: singleClickTimer
        interval: 220
        repeat: false
        onTriggered: {
            dispatchPendingSingleClick()
        }
    }

    DropArea {
        id: dropArea
        z: 50
        anchors.fill: parent
        enabled: root.allowDrops
        onDropped: function(drop) {
            var payload = root._dropPayload(drop)
            root.dropReceived(payload)
            if (root.onDrop) {
                root.onDrop(payload)
            }
            drop.acceptProposedAction()
        }
    }

    Image {
        visible: root.showPin && String(root.iconPin || "").length > 0
        z: 60
        source: root.iconPin
        width: Math.min(root.compactHeight * 0.5, 18)
        height: width
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: 6
        fillMode: Image.PreserveAspectFit
    }
}
