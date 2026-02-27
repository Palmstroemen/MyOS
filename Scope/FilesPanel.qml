import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "Theme/tag_chips.js" as TagChips
import "Theme/tag_chip_style.js" as TagChipStyle
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
    property real uPanelTintMix: 0.50
    property real projectTintOpacity: 1.0
    property bool allowDrags: true
    property bool halfTransparent: false
    property bool showFolders: false
    property var availableTags: []
    property var folderTags: []
    property var fileTags: []
    property var folderTagColors: ({})
    property var fileTagColors: ({})
    property var tagSuggestions: []
    property var selectedTags: []
    property var selectedPaths: []
    property string tagSource: "visible"
    /** Bindung an Fenster-Sprache, damit Tag-Beschriftungen bei Sprachumschaltung neu übersetzt werden. */
    property string uiLanguage: ""
    property bool isTagIndexing: false
    property int folderSizeBytes: 0
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
    signal leaveMyosFolder()
    signal createProject()
    property bool showMyosButton: false
    property bool showLeaveMyosButton: false
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
    property int tagChipLeftRadius: TagChipStyle.CHIP_LEFT_RADIUS
    property int tagChipRightRadius: TagChipStyle.CHIP_RIGHT_RADIUS
    property int tagChipPadV: TagChipStyle.CHIP_PADDING_V
    property int tagChipPadH: TagChipStyle.CHIP_PADDING_H
    property int tagChipMargin: TagChipStyle.CHIP_MARGIN
    // Explicit chip sizing for PostFix-like proportions (independent from compact buttons).
    property int tagChipHeightPx: Math.max(18, Math.round(baseFont * 1.25))
    property int tagChipFontPx: Math.max(9, Math.round(baseFont * 0.74))
    property int tagSectionLabelPx: Math.max(9, Math.round(baseFont * 0.74))
    property int tagInputHeightPx: Math.max(tagChipHeightPx, 22)
    property int sidePanelInnerMargin: 8
    property int sidePanelButtonSpacing: 6
    readonly property int sidePanelDesiredInnerWidth: (2 * topRightButtonSize) + sidePanelButtonSpacing
    readonly property int sidePanelDesiredWidth: sidePanelDesiredInnerWidth + (2 * sidePanelInnerMargin)
    readonly property string longestTagForMeasure: {
        var folder = root.folderTags || []
        var file = root.fileTags || []
        var best = ""
        for (var i = 0; i < folder.length; i++) {
            var t = String(folder[i])
            if (t.length > best.length) best = t
        }
        for (var j = 0; j < file.length; j++) {
            var u = String(file[j])
            if (u.length > best.length) best = u
        }
        return best
    }
    property real filesPanelOverlayAlpha: 0.20
    readonly property real uPanelLuma: (0.2126 * backgroundColor.r) + (0.7152 * backgroundColor.g) + (0.0722 * backgroundColor.b)
    readonly property color uPanelColor: PanelColors.uPanelColor(showMyosButton, backgroundColor, uPanelTintColor, uPanelTintMix)
    readonly property color filesPanelOverlayColor: PanelColors.filesOverlayColor(uPanelLuma, filesPanelOverlayAlpha)

    radius: 0
    color: root.uPanelColor
    border.width: 0
    implicitWidth: 280
    implicitHeight: 200
    opacity: halfTransparent ? 0.5 : 1

    signal requestMore()
    signal filterChanged(bool showFolders)
    signal tagToggled(string tag)
    signal requestTagSourceChange(string source)
    signal addFolderTagRequested(string tag)
    signal removeFolderTagRequested(string tag)
    signal folderTagColorRequested(string tag, string color)
    signal itemActivated(string path, bool ctrlPressed, bool shiftPressed)
    signal selectionBoxApplied(var paths, bool additive)
    signal emptyAreaClicked()
    signal moveEntriesRequested(string payload, string targetDir)
    signal createNoteRequested()
    signal createFolderRequested(string basePath)
    signal moveSelectedIntoNewFolderRequested(var sourcePaths)
    signal renameRequested(var paths)
    signal deleteRequested(var paths)
    signal selectAllRequested()
    signal openRequested(string path)
    signal openWithRequested(string path)

    onShowFoldersChanged: filterChanged(showFolders)
    property string folderTagColorTarget: ""

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
        width: Math.max(74, Math.max(root.sidePanelDesiredWidth, sidePanelTagContentWidth))
        radius: 0
        border.width: 0
        color: "transparent"
        z: 2

        Text {
            id: measureTag
            visible: false
            font.pixelSize: root.tagChipFontPx
            text: "  #" + root.longestTagForMeasure
        }
        readonly property int sidePanelTagContentWidth: measureTag.implicitWidth + root.tagChipPadH * 2 + 6 + 15 + (2 * root.sidePanelInnerMargin)

        Column {
            anchors.fill: parent
            anchors.margins: root.sidePanelInnerMargin
            spacing: root.sidePanelInnerMargin

            Row {
                width: parent.width
                spacing: root.sidePanelButtonSpacing

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
                    visible: root.showMyosButton && !root.showLeaveMyosButton
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
                    color: root.smallButtonBg
                    border.color: root.smallButtonBorder
                    visible: root.showLeaveMyosButton
                    Text {
                        anchors.centerIn: parent
                        text: "↑"
                        color: root.smallButtonText
                        font.pixelSize: Math.round(root.topRightButtonSize * 0.75)
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.leaveMyosFolder()
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
                height: Math.max(80, parent.height - root.topRightButtonSize - 20)
                radius: 0
                border.width: 0
                color: "transparent"
                visible: true

                Column {
                    anchors.fill: parent
                    spacing: 6

                    Flickable {
                        id: tagsFlick
                        width: parent.width
                        height: parent.height
                        contentWidth: width
                        contentHeight: tagsColumn.height
                        clip: true

                        Column {
                            id: tagsColumn
                            width: parent.width
                            spacing: 4

                            Text {
                                width: parent.width
                                text: (root.uiLanguage ? "" : "") + qsTr("Ordnertags")
                                color: root.smallButtonText
                                font.pixelSize: root.tagSectionLabelPx
                                elide: Text.ElideRight
                            }

                            readonly property bool hasSelectedTags: root.selectedTags && root.selectedTags.length > 0

                            Repeater {
                                model: root.folderTags ? root.folderTags : []
                                delegate: Rectangle {
                                    property int deleteZonePx: 15
                                    property bool chipHovered: false
                                    x: root.tagChipMargin
                                    width: Math.max(20, tagsColumn.width - (2 * root.tagChipMargin))
                                    height: root.tagChipHeightPx
                                    radius: root.tagChipRightRadius
                                    readonly property string tagValue: modelData
                                    readonly property bool selected: root.selectedTags && root.selectedTags.indexOf(tagValue) !== -1
                                    readonly property bool dimmed: tagsColumn.hasSelectedTags && !selected
                                    readonly property color customTagColor: {
                                        var map = root.folderTagColors || ({})
                                        var raw = map[tagValue]
                                        return raw ? Qt.color(raw) : "transparent"
                                    }
                                    readonly property color baseTagColor: customTagColor !== "transparent" ? customTagColor : Qt.color("#ffd54f")
                                    color: selected
                                        ? Qt.rgba(baseTagColor.r, baseTagColor.g, baseTagColor.b, 1.0)
                                        : Qt.rgba(baseTagColor.r, baseTagColor.g, baseTagColor.b, 1.0)
                                    opacity: dimmed ? 0.75 : 1.0
                                    border.width: 1
                                    border.color: selected
                                        ? Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_HOVER_ALPHA)
                                        : Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_IDLE_ALPHA)

                                    // QtQuick 2.15 Rectangle has only uniform radius. Mask left side to keep it square.
                                    Rectangle {
                                        anchors.left: parent.left
                                        anchors.top: parent.top
                                        anchors.bottom: parent.bottom
                                        width: Math.max(6, root.tagChipRightRadius - 2)
                                        color: parent.color
                                        border.width: parent.border.width
                                        border.color: parent.border.color
                                    }

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.left: parent.left
                                        anchors.leftMargin: root.tagChipPadH
                                        anchors.right: removeXBtn.left
                                        anchors.rightMargin: parent.chipHovered ? 2 : 6
                                        text: (selected ? "✓ " : "  ") + "#" + tagValue
                                        color: TagChipStyle.textColorForBg(parent.color)
                                        font.pixelSize: root.tagChipFontPx
                                        elide: Text.ElideNone
                                        horizontalAlignment: Text.AlignRight
                                    }
                                    Text {
                                        id: removeXBtn
                                        anchors.right: parent.right
                                        anchors.rightMargin: 2
                                        anchors.verticalCenter: parent.verticalCenter
                                        width: parent.chipHovered ? parent.deleteZonePx : 0
                                        text: "×"
                                        color: "#e53935"
                                        font.pixelSize: Math.round(root.tagChipFontPx * 1.2)
                                        font.bold: true
                                        horizontalAlignment: Text.AlignHCenter
                                        opacity: parent.chipHovered ? 1.0 : 0.0
                                        visible: width > 0
                                        Behavior on width { NumberAnimation { duration: 90 } }
                                        Behavior on opacity { NumberAnimation { duration: 90 } }
                                    }
                                    MouseArea {
                                        anchors.fill: parent
                                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                                        hoverEnabled: true
                                        onEntered: {
                                            parent.border.width = 2
                                            parent.chipHovered = true
                                        }
                                        onExited: {
                                            parent.border.width = 1
                                            parent.chipHovered = false
                                        }
                                        onClicked: function(mouse) {
                                            var inDeleteZone = mouse.button === Qt.LeftButton
                                                && Number(mouse.x || 0) >= (parent.width - parent.deleteZonePx)
                                            if (inDeleteZone) {
                                                root.removeFolderTagRequested(parent.tagValue)
                                                return
                                            }
                                            if (mouse.button === Qt.RightButton) {
                                                var p = mapToItem(root, mouse.x, mouse.y)
                                                root.folderTagColorTarget = parent.tagValue
                                                folderTagColorMenu.x = p.x
                                                folderTagColorMenu.y = p.y
                                                folderTagColorMenu.open()
                                                return
                                            }
                                            root.tagToggled(parent.tagValue)
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                width: parent.width
                                height: root.tagInputHeightPx
                                radius: root.tagChipRadius
                                color: Qt.rgba(1, 1, 1, 0.10)
                                border.color: Qt.rgba(root.smallButtonBorder.r, root.smallButtonBorder.g, root.smallButtonBorder.b, 0.45)
                                z: 20

                                TextField {
                                    id: newFolderTagInput
                                    property bool suppressCompletion: false
                                    anchors.fill: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8
                                    topPadding: 0
                                    bottomPadding: 0
                                    leftPadding: 0
                                    rightPadding: 0
                                    font.pixelSize: root.tagChipFontPx
                                    clip: true
                                    selectByMouse: true
                                    placeholderText: (root.uiLanguage ? "" : "") + qsTr("Neuer Ordnertag ...")
                                    color: root.text
                                    background: Item {}
                                    onTextEdited: suppressCompletion = false
                                    onAccepted: {
                                        var value = String(text || "").trim()
                                        if (value.length > 0) {
                                            root.addFolderTagRequested(value)
                                            text = ""
                                        }
                                        suppressCompletion = true
                                        focus = false
                                    }
                                }

                                Rectangle {
                                    id: tagSuggestionDropdown
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.bottom
                                    anchors.topMargin: 2
                                    z: 30
                                    radius: root.tagChipRadius
                                    color: Qt.rgba(root.smallButtonBg.r, root.smallButtonBg.g, root.smallButtonBg.b, 0.96)
                                    border.color: root.smallButtonBorder
                                    clip: true

                                    property var completionModel: {
                                        var src = root.tagSuggestions || []
                                        var needle = String(newFolderTagInput.text || "").trim().toLowerCase()
                                        var out = []
                                        for (var i = 0; i < src.length; i++) {
                                            var candidate = String(src[i] || "").trim()
                                            if (!candidate.length) continue
                                            var lower = candidate.toLowerCase()
                                            if (needle.length === 0 || lower.indexOf(needle) === 0) {
                                                out.push(candidate)
                                            }
                                            if (out.length >= 8) break
                                        }
                                        return out
                                    }
                                    visible: newFolderTagInput.activeFocus
                                        && !newFolderTagInput.suppressCompletion
                                        && completionModel.length > 0
                                    height: Math.min(8, completionModel.length) * Math.max(root.tagChipMinHeight, root.tagChipHeightPx - 2) + 2

                                    Column {
                                        id: completionColumn
                                        anchors.fill: parent
                                        anchors.margins: 1
                                        spacing: 0

                                        Repeater {
                                            model: tagSuggestionDropdown.completionModel
                                            delegate: Rectangle {
                                                x: root.tagChipMargin
                                                width: Math.max(20, completionColumn.width - (2 * root.tagChipMargin))
                                                height: Math.max(root.tagChipMinHeight, root.tagChipHeightPx - 2)
                                                radius: root.tagChipRightRadius
                                                readonly property string tagValue: String(modelData || "")
                                                readonly property color suggestionColor: {
                                                    var f = root.fileTagColors || ({})
                                                    var c = f[tagValue]
                                                    if (c) return Qt.color(c)
                                                    var d = root.folderTagColors || ({})
                                                    c = d[tagValue]
                                                    if (c) return Qt.color(c)
                                                    return Qt.color("#ffd54f")
                                                }
                                                color: completionHover.containsMouse
                                                    ? Qt.rgba(suggestionColor.r, suggestionColor.g, suggestionColor.b, 0.85)
                                                    : Qt.rgba(suggestionColor.r, suggestionColor.g, suggestionColor.b, 1.0)
                                                border.width: completionHover.containsMouse ? 2 : 1
                                                border.color: completionHover.containsMouse
                                                    ? Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_HOVER_ALPHA)
                                                    : Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_IDLE_ALPHA)

                                                Rectangle {
                                                    anchors.left: parent.left
                                                    anchors.top: parent.top
                                                    anchors.bottom: parent.bottom
                                                    width: Math.max(6, root.tagChipRightRadius - 2)
                                                    color: parent.color
                                                    border.width: parent.border.width
                                                    border.color: parent.border.color
                                                }

                                                Text {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    anchors.left: parent.left
                                                    anchors.leftMargin: root.tagChipPadH
                                                    anchors.right: parent.right
                                                    anchors.rightMargin: root.tagChipPadH
                                                    text: "+ #" + tagValue
                                                    color: TagChipStyle.textColorForBg(parent.color)
                                                    font.pixelSize: root.tagChipFontPx
                                                    elide: Text.ElideRight
                                                    horizontalAlignment: Text.AlignRight
                                                }

                                                MouseArea {
                                                    id: completionHover
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    onClicked: {
                                                        var suggestion = String(modelData || "").trim()
                                                        if (suggestion.length > 0) {
                                                            root.addFolderTagRequested(suggestion)
                                                        }
                                                        newFolderTagInput.text = ""
                                                        newFolderTagInput.suppressCompletion = true
                                                        newFolderTagInput.focus = false
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            Item {
                                id: fileTagsSection
                                width: parent.width
                                height: fileTagsSectionColumn.height

                                Column {
                                    id: fileTagsSectionColumn
                                    width: parent.width
                                    spacing: 4

                                    Text {
                                        width: parent.width
                                        text: (root.uiLanguage ? "" : "") + qsTr("Filetags")
                                        color: root.smallButtonText
                                        font.pixelSize: root.tagSectionLabelPx
                                        elide: Text.ElideRight
                                    }

                                    Item {
                                        id: fileTagsListSurface
                                        width: parent.width
                                        height: fileTagsListColumn.height

                                        Column {
                                            id: fileTagsListColumn
                                            width: parent.width
                                            spacing: 4

                                            Repeater {
                                                model: root.fileTags ? root.fileTags : []
                                                delegate: Rectangle {
                                                    x: root.tagChipMargin
                                                    width: Math.max(20, tagsColumn.width - (2 * root.tagChipMargin))
                                                    height: root.tagChipHeightPx
                                                    radius: root.tagChipRightRadius
                                                    readonly property string tagValue: modelData
                                                    readonly property bool selected: root.selectedTags && root.selectedTags.indexOf(tagValue) !== -1
                                                    readonly property bool dimmed: tagsColumn.hasSelectedTags && !selected
                                                    readonly property color customTagColor: {
                                                        var map = root.fileTagColors || ({})
                                                        var raw = map[tagValue]
                                                        return raw ? Qt.color(raw) : "transparent"
                                                    }
                                                    readonly property color baseTagColor: customTagColor !== "transparent" ? customTagColor : Qt.color("#ffd54f")
                                                    color: selected
                                                        ? Qt.rgba(baseTagColor.r, baseTagColor.g, baseTagColor.b, 1.0)
                                                        : Qt.rgba(baseTagColor.r, baseTagColor.g, baseTagColor.b, 1.0)
                                                    opacity: dimmed ? 0.75 : 1.0
                                                    border.width: 1
                                                    border.color: selected
                                                        ? Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_HOVER_ALPHA)
                                                        : Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_IDLE_ALPHA)

                                                    Rectangle {
                                                        anchors.left: parent.left
                                                        anchors.top: parent.top
                                                        anchors.bottom: parent.bottom
                                                        width: Math.max(6, root.tagChipRightRadius - 2)
                                                        color: parent.color
                                                        border.width: parent.border.width
                                                        border.color: parent.border.color
                                                    }

                                                    Text {
                                                        anchors.verticalCenter: parent.verticalCenter
                                                        anchors.left: parent.left
                                                        anchors.leftMargin: root.tagChipPadH
                                                        anchors.right: parent.right
                                                        anchors.rightMargin: root.tagChipPadH
                                                        text: (selected ? "✓  " : "    ") + "#" + tagValue
                                                        color: TagChipStyle.textColorForBg(parent.color)
                                                        font.pixelSize: root.tagChipFontPx
                                                        elide: Text.ElideNone
                                                        horizontalAlignment: Text.AlignRight
                                                    }
                                                    MouseArea {
                                                        anchors.fill: parent
                                                        hoverEnabled: true
                                                        onEntered: parent.border.width = 2
                                                        onExited: parent.border.width = 1
                                                        onClicked: root.tagToggled(parent.tagValue)
                                                    }
                                                }
                                            }

                                            Rectangle {
                                                id: indexingPseudoTag
                                                x: root.tagChipMargin
                                                width: Math.max(20, tagsColumn.width - (2 * root.tagChipMargin))
                                                height: root.tagChipHeightPx
                                                radius: root.tagChipRightRadius
                                                visible: root.isTagIndexing
                                                color: "#ffd54f"
                                                border.width: 1
                                                border.color: Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_IDLE_ALPHA)
                                                opacity: 0.45

                                                Rectangle {
                                                    anchors.left: parent.left
                                                    anchors.top: parent.top
                                                    anchors.bottom: parent.bottom
                                                    width: Math.max(6, root.tagChipRightRadius - 2)
                                                    color: parent.color
                                                    border.width: parent.border.width
                                                    border.color: parent.border.color
                                                }

                                                Text {
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    anchors.left: parent.left
                                                    anchors.leftMargin: root.tagChipPadH
                                                    anchors.right: parent.right
                                                    anchors.rightMargin: root.tagChipPadH
                                                    text: (root.uiLanguage ? "" : "") + qsTr("… parse tags")
                                                    color: root.textMuted
                                                    font.pixelSize: root.tagChipFontPx
                                                    elide: Text.ElideRight
                                                    horizontalAlignment: Text.AlignRight
                                                }

                                                SequentialAnimation on opacity {
                                                    running: indexingPseudoTag.visible
                                                    loops: Animation.Infinite
                                                    NumberAnimation { from: 0.20; to: 0.65; duration: 450 }
                                                    NumberAnimation { from: 0.65; to: 0.20; duration: 450 }
                                                }
                                            }
                                        }
                                    }
                                }

                                Rectangle {
                                    x: -6
                                    y: -6
                                    width: parent.width + 12
                                    height: parent.height + 12
                                    color: Qt.rgba(1, 1, 1, 0.20)
                                    radius: root.tagChipRadius
                                    visible: (root.fileTags && root.fileTags.length > 0) || root.isTagIndexing
                                    z: 6
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
                readonly property bool isFolder: !!(model.isDir)
                readonly property bool selected: root.selectedPaths && itemPath.length > 0 && root.selectedPaths.indexOf(itemPath) !== -1
                width: filesGrid.cellWidth - root.gridSpacing
                height: filesGrid.cellHeight - (root.itemStyle === "largeIcon" ? root.gridSpacing : 4)
                label: {
                    var baseName = String(model.name || "")
                    var group = String(model.filterGroup || "")
                    if (group.length > 0) {
                        return "[" + group + "] " + baseName
                    }
                    if (model.filterActive && model.originPath) {
                        var origin = String(model.originPath || "")
                        return baseName + "  •  " + origin
                    }
                    return baseName
                }
                style: root.itemStyle
                compactHeight: root.compactButtonHeight
                largeHeight: root.largeButtonHeight
                largePadding: root.largeButtonPadding
                iconSmall: root.iconSizeSmall
                iconLarge: root.iconSizeLarge
                iconSource: "image://theme/" + (model.iconName ? model.iconName : (model.isDir ? "folder" : "text-x-generic"))
                iconSourceHover: model.isDir
                    ? (root.iconFolder || "image://theme/folder-open")
                    : ("image://theme/" + (model.iconName ? model.iconName : "text-x-generic") + "#active")
                batchSource: model.isDir && model.batch ? model.batch : ""
                batchText: model.isDir && model.batchText ? model.batchText : ""
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
                    onDropped: function(drop) {
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

            DropArea {
                anchors.fill: parent
                onDropped: function(drop) {
                    if (!drop || !drop.text) return
                    var contentX = filesGrid.contentX || 0
                    var contentY = filesGrid.contentY || 0
                    var idx = filesGrid.indexAt(drop.x + contentX, drop.y + contentY)
                    if (idx >= 0) {
                        var item = filesGrid.itemAtIndex(idx)
                        if (item && item.isFolder && item.itemPath && item.itemPath.length > 0) {
                            root.moveEntriesRequested(drop.text, item.itemPath)
                        }
                    }
                    drop.acceptProposedAction()
                }
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
                        // Plain click on empty area clears selection and resets CTD to CWD.
                        root.selectionBoxApplied([], false)
                        root.emptyAreaClicked()
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

    Menu {
        id: folderTagColorMenu

        function applyColor(hexColor) {
            if (!root.folderTagColorTarget || root.folderTagColorTarget.length === 0) {
                return
            }
            root.folderTagColorRequested(root.folderTagColorTarget, hexColor)
        }

        MenuItem { text: qsTr("Farbe: Rot"); onTriggered: folderTagColorMenu.applyColor("#d64f4f") }
        MenuItem { text: qsTr("Farbe: Orange"); onTriggered: folderTagColorMenu.applyColor("#d68b39") }
        MenuItem { text: qsTr("Farbe: Gelb"); onTriggered: folderTagColorMenu.applyColor("#c9b332") }
        MenuItem { text: qsTr("Farbe: Gruen"); onTriggered: folderTagColorMenu.applyColor("#4ea35a") }
        MenuItem { text: qsTr("Farbe: Cyan"); onTriggered: folderTagColorMenu.applyColor("#3ca2a6") }
        MenuItem { text: qsTr("Farbe: Blau"); onTriggered: folderTagColorMenu.applyColor("#4c72d9") }
        MenuItem { text: qsTr("Farbe: Violett"); onTriggered: folderTagColorMenu.applyColor("#8a58cf") }
        MenuItem { text: qsTr("Farbe: Grau"); onTriggered: folderTagColorMenu.applyColor("#7b7f89") }
    }

    Shortcut {
        sequences: [StandardKey.New]
        onActivated: root.createNoteRequested()
    }
}
