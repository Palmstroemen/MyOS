import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "Theme/tag_chips.js" as TagChips
import "Theme/tag_chip_style.js" as TagChipStyle
import "Theme/panel_colors.js" as PanelColors
import "js/DropUtils.js" as DropUtils
import "js/FormatUtils.js" as FormatUtils

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
    /// Mix für Panel-Hintergrund mit CWP-/Projektfarbe (0…1). Wird von main mit 0.65 gesetzt.
    property real uPanelTintMix: 0.65
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
    /// ACL filter panel (left, "set by the system"): principals of the listed folder, see
    /// ScopeApi.acl_summary. Shown only when the project has an ACLs.md.
    property bool aclPanelVisible: false
    property var aclPrincipals: []
    property int aclEntryCount: 0
    property string selectedAclPrincipal: ""
    signal aclPrincipalToggled(string id)
    /// Size of the listed folder from the live measurement; < 0 while unknown.
    property real folderSizeBytes: -1
    property bool folderSizeComplete: false
    /// Folder sizes of this listing were asked for (hover/click); file sizes are always shown.
    property bool folderSizesActive: false
    property bool folderSizesMeasuring: false
    /// Pointer rested on the size column head or the sidebar total: measure folder sizes.
    signal folderSizesRequested()
    /// Dwell time before hovering starts a measurement (a pointer just passing by does not).
    property int folderSizesHoverDelayMs: 300
    property real templatesBrowserWidth: 0
    property real projectsBrowserWidth: 0
    property string iconFolder: ""
    property string iconFolderOff: ""
    property string iconFolderXray: ""
    property string iconFile: ""
    property string iconGear: ""
    /// "largeIcon" (tiles) or "smallIcon" (list with right-aligned size column).
    property string itemStyle: "largeIcon"
    /// Visible list view columns (ids); the name column is always shown.
    property var listColumns: ["modified", "size"]
    readonly property int listDetailFontPx: Math.max(9, Math.round(baseFont * 0.85))
    property string sortKey: "name"
    property bool sortAscending: true

    /// Row geometry for header, rows and hover areas: { nameX, columns: [{.., x}] }, x from
    /// the start of a row's content (6 px inside the row).
    readonly property var listLayout: FormatUtils.placeListColumns(visibleListColumns, listDetailFontPx, listNameColumnWidth)

    /// The visible size column ({id, width, align, side, x}) or null when hidden.
    readonly property var sizeColumn: {
        for (var i = 0; i < listLayout.columns.length; i++) {
            if (listLayout.columns[i].id === "size") return listLayout.columns[i]
        }
        return null
    }

    // Name column: as wide as the longest name, so the other columns move up to the
    // names instead of sitting at the far right; at least 12 em, and narrow enough for
    // all columns to fit (long names are then elided).
    property real longestNameWidth: 0
    property int _measuredNameCount: 0
    readonly property int listNameColumnWidth: {
        var minimum = 12 * baseFont
        var available = filesGrid.width - gridSpacing - 12
            - FormatUtils.sideWidth(visibleListColumns, "left", listDetailFontPx)
            - FormatUtils.sideWidth(visibleListColumns, "right", listDetailFontPx)
        var wanted = longestNameWidth + iconSizeSmall + 30
        return Math.round(Math.max(minimum, Math.min(wanted, available)))
    }

    FontMetrics {
        id: nameMetrics
        font.pixelSize: root.baseFont
    }

    /// Track the widest name incrementally as rows are appended (the model fills in chunks).
    function measureNames() {
        var model = itemsModel
        if (!model) return
        if (model.count < _measuredNameCount) {
            longestNameWidth = 0
            _measuredNameCount = 0
        }
        var widest = longestNameWidth
        for (var i = _measuredNameCount; i < model.count; i++) {
            widest = Math.max(widest, nameMetrics.advanceWidth(String(model.get(i).name || "")))
        }
        longestNameWidth = widest
        _measuredNameCount = model.count
    }

    Connections {
        target: root.itemsModel
        function onCountChanged() { root.measureNames() }
    }

    function sortArrow(key) {
        return sortKey === key ? (sortAscending ? " ▲" : " ▼") : ""
    }
    readonly property var visibleListColumns: FormatUtils.visibleListColumns(listColumns, listDetailFontPx)

    function listColumnTitle(id) {
        if (id === "size") return qsTr("Größe")
        if (id === "modified") return qsTr("Geändert")
        if (id === "type") return qsTr("Typ")
        if (id === "tags") return qsTr("Tags")
        if (id === "accessed") return qsTr("Zugriff")
        if (id === "permissions") return qsTr("Berechtigungen")
        if (id === "owner") return qsTr("Besitzer")
        if (id === "group") return qsTr("Gruppe")
        return id
    }

    function toggleListColumn(id) {
        var next = []
        for (var i = 0; i < FormatUtils.LIST_COLUMNS.length; i++) {
            var colId = FormatUtils.LIST_COLUMNS[i].id
            var on = listColumns.indexOf(colId) !== -1
            if (colId === id) on = !on
            if (on) next.push(colId)
        }
        listColumnsChangeRequested(next)
    }
    /// Folder currently listed (may be an unborn embryo); target for drops on free panel space.
    property string currentPath: ""
    signal folderActivated(string name)
    /// Unified navigation intent (double-click = CWD+CTD). gesture: "double", source: "filesPanel".
    signal navigationRequested(string path, string gesture, string source)
    signal fileActivated(string name)
    signal openMyosFolder()
    signal leaveMyosFolder()
    signal createProject()
    signal createMyosAndEnter()
    signal xrayClicked()
    /// Side panel button: switch between tiles and list.
    signal itemStyleToggleRequested()
    /// Header context menu: new set of visible list columns (ids, see FormatUtils.LIST_COLUMNS).
    signal listColumnsChangeRequested(var columns)
    /// Header click: sort by this key ("name", "modified", "size"); main flips the direction.
    signal sortRequested(string key)
    property bool showLeaveMyosButton: false
    property bool hasProjectInCwp: false
    property bool hasMyosDirInCwp: false
    /** Farbe für den P-Button wenn CWD nicht in einem Projekt liegt (Wurzelprojekt-Farbe). */
    property color pButtonActiveColor: "#7b5bd6"

    property int compactButtonHeight: 32
    property int largeButtonHeight: 88
    property int largeButtonPadding: 6
    property int iconSizeSmall: 24
    property int iconSizeLarge: 64
    property int smallIconSize: Math.round(compactButtonHeight * 0.6)
    property int topRightButtonSize: Math.max(24, Math.round(Math.max(compactButtonHeight, 32) * 0.85))
    property int topRightIconSize: Math.round(topRightButtonSize * 0.84)
    property int gridSpacing: 8
    /** Rahmen um das runde Panel (Hintergrund sichtbar). Halbiert für schlankeren Rahmen. */
    property int filesPanelFrameMargin: 8
    property int filesPanelFrameMarginRight: 5
    /** Zusätzlicher Innenabstand des Grids zum Panel. */
    property int filesPanelContentPadding: 4
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
    // uPanelTintColor kommt gebunden aus main (filesPanelTintColor).
    readonly property color uPanelColor: PanelColors.uPanelColor(true, backgroundColor, uPanelTintColor, uPanelTintMix)
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

    /// Keeps the ghost image of the dragged item alive for the duration of a drag.
    property var fileDragGrabResult: null

    /// Start a file drag for the item under pressPos (filesGrid coordinates).
    /// Payload, size and look are copied into fileDragProxy, so the drag no longer
    /// depends on the delegate.
    function beginFileDrag(pressPos) {
        var gridX = pressPos.x + filesGrid.contentX
        var gridY = pressPos.y + filesGrid.contentY
        var idx = filesGrid.indexAt(gridX, gridY)
        var item = idx >= 0 ? filesGrid.itemAtIndex(idx) : null
        if (!item || !item.canDrag) return
        var localX = gridX - item.x
        var localY = gridY - item.y
        if (!item.hitAcceptsPoint(localX, localY)) return
        var payload = selectedPayloadFor(item.itemPath, item.selected)
        if (payload.length === 0) return
        fileDragProxy.dragPayload = payload
        fileDragProxy.width = item.width
        fileDragProxy.height = item.height
        fileDragProxy.Drag.hotSpot.x = localX
        fileDragProxy.Drag.hotSpot.y = localY
        fileDragProxy.ghostSource = ""
        item.grabToImage(function(result) {
            root.fileDragGrabResult = result
            if (fileDragProxy.Drag.active) fileDragProxy.ghostSource = result.url
        })
        moveFileDrag(filesGrid.mapToItem(null, pressPos.x, pressPos.y))
        fileDragProxy.Drag.active = true
    }

    function moveFileDrag(scenePos) {
        if (!fileDragProxy.parent) return
        var p = fileDragProxy.parent.mapFromItem(null, scenePos.x, scenePos.y)
        fileDragProxy.x = p.x - fileDragProxy.Drag.hotSpot.x
        fileDragProxy.y = p.y - fileDragProxy.Drag.hotSpot.y
    }

    function endFileDrag(dropIt) {
        if (fileDragProxy.Drag.active) {
            if (dropIt) {
                fileDragProxy.Drag.drop()
            } else {
                fileDragProxy.Drag.cancel()
            }
            fileDragProxy.Drag.active = false
        }
        fileDragProxy.dragPayload = ""
        fileDragProxy.ghostSource = ""
        fileDragGrabResult = null
    }

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

    // Rights on a chip (as in PostFix): read is an arrow out of the document ("◂" left of
    // the name), write an arrow into it ("▸" right of it); execute and change stay
    // letters on the left.
    function aclRightsLetters(rights) {
        var letters = { execute: "x", change: "c", delete: "d" }
        var out = []
        for (var i = 0; i < (rights || []).length; i++) {
            if (letters[rights[i]]) out.push(letters[rights[i]])
        }
        return out.join(" ")
    }

    /// Space between a chip's name and each arrow (px, equal on both sides).
    readonly property int aclArrowGap: 4

    function aclHas(rights, right) {
        return (rights || []).indexOf(right) !== -1
    }

    function aclRightsNames(rights) {
        var names = { read: qsTr("Lesen"), write: qsTr("Schreiben"), execute: qsTr("Ausführen"), change: qsTr("Rechte ändern"), delete: qsTr("Löschen") }
        var out = []
        for (var i = 0; i < (rights || []).length; i++) {
            out.push(names[rights[i]] || rights[i])
        }
        return out.join(", ")
    }

    function aclChipTip(p) {
        if (p.section === "exception") {
            return qsTr("Kein Zugriff auf diesen Ordner, aber auf %1 von %2 Einträgen").arg(p.count).arg(aclEntryCount)
        }
        var tip = qsTr("Hier: %1").arg(aclRightsNames(p.rights))
        if (p.partial) tip += "\n" + qsTr("Kein Zugriff auf %1 von %2 Einträgen").arg(aclEntryCount - p.count).arg(aclEntryCount)
        return tip
    }

    function aclSection(section) {
        var out = []
        for (var i = 0; i < (aclPrincipals || []).length; i++) {
            if (aclPrincipals[i].section === section) out.push(aclPrincipals[i])
        }
        return out
    }

    readonly property string longestAclNameForMeasure: {
        var best = ""
        for (var i = 0; i < (aclPrincipals || []).length; i++) {
            var n = String(aclPrincipals[i].name || "")
            if (n.length > best.length) best = n
        }
        return best
    }

    // ACL filter panel: left of the list, mirroring the tag filter on the right. Who may
    // access the listed folder on top, who may access only some of its entries below.
    // Clicking a chip shows only the entries that role or person has rights on.
    Rectangle {
        id: aclPanel
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        anchors.leftMargin: 10
        visible: root.aclPanelVisible
        width: visible ? Math.max(74, Math.min(14 * root.baseFont, aclContentWidth)) : 0
        color: "transparent"
        z: 2

        FontMetrics {
            id: aclArrowMetrics
            font.pixelSize: root.tagChipFontPx
        }
        Text {
            id: measureAcl
            visible: false
            font.pixelSize: root.tagChipFontPx
            text: "✓ x c d  ◂ " + root.longestAclNameForMeasure + "  ▸"
        }
        readonly property int aclContentWidth: measureAcl.implicitWidth + root.tagChipPadH * 2 + 6 + (2 * root.sidePanelInnerMargin)

        Flickable {
            anchors.fill: parent
            anchors.margins: root.sidePanelInnerMargin
            contentWidth: width
            contentHeight: aclColumn.height
            clip: true

            Column {
                id: aclColumn
                width: parent.width
                spacing: 4
                readonly property bool hasSelection: root.selectedAclPrincipal.length > 0

                Repeater {
                    model: [
                        { section: "folder", title: qsTr("Zugriff") },
                        { section: "exception", title: qsTr("Ausnahmen") }
                    ]
                    delegate: Column {
                        readonly property var chips: root.aclSection(modelData.section)
                        width: aclColumn.width
                        spacing: 4
                        visible: chips.length > 0
                        topPadding: index > 0 ? 6 : 0

                        Text {
                            width: parent.width
                            text: modelData.title
                            color: root.smallButtonText
                            font.pixelSize: root.tagSectionLabelPx
                            elide: Text.ElideRight
                        }

                        Repeater {
                            model: parent.chips
                            delegate: Rectangle {
                                id: aclChip
                                readonly property bool selected: root.selectedAclPrincipal === modelData.id
                                // Same greys as PostFix's ACL sidebar: people lighter than groups.
                                readonly property color baseColor: modelData.kind === "user" ? "#d6d6d6" : "#b5b5b5"
                                x: root.tagChipMargin
                                width: Math.max(20, aclColumn.width - (2 * root.tagChipMargin))
                                height: root.tagChipHeightPx
                                radius: root.tagChipRightRadius
                                color: baseColor
                                // Others are dimmed while one is selected (texts only: the corner
                                // mask would show through a dimmed chip).
                                readonly property real textOpacity: aclColumn.hasSelection && !selected ? 0.55 : 1.0
                                border.width: selected || aclChipMouse.containsMouse ? 2 : 1
                                border.color: selected
                                    ? Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_HOVER_ALPHA)
                                    : Qt.rgba(0, 0, 0, TagChipStyle.CHIP_BORDER_IDLE_ALPHA)

                                // Square left edge (towards the system side), rounded right edge
                                // pointing into the list, as in PostFix. Unlike the tag chips the
                                // text starts on the left, so the mask draws only the outer border
                                // (a framed mask would put a line through the rights).
                                Item {
                                    readonly property real bw: aclChip.border.width
                                    readonly property color bc: aclChip.border.color
                                    width: aclChip.radius
                                    height: aclChip.height
                                    Rectangle { anchors.fill: parent; color: aclChip.color }
                                    Rectangle { width: parent.width; height: parent.bw; color: parent.bc }
                                    Rectangle { y: parent.height - parent.bw; width: parent.width; height: parent.bw; color: parent.bc }
                                    Rectangle { width: parent.bw; height: parent.height; color: parent.bc }
                                }

                                Text {
                                    id: aclRightsText
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left
                                    anchors.leftMargin: root.tagChipPadH
                                    // x/c here; for exceptions the number of entries instead.
                                    text: (aclChip.selected ? "✓ " : "") + (modelData.section === "exception"
                                        ? String(modelData.count)
                                        : root.aclRightsLetters(modelData.rights) + (modelData.partial ? " *" : ""))
                                    color: "#555555"
                                    opacity: aclChip.textOpacity
                                    font.pixelSize: Math.max(8, root.tagChipFontPx - 1)
                                }
                                // Arrows sit aclArrowGap from the name on both sides; the write
                                // slot stays when empty, so names line up.
                                Text {
                                    id: aclReadArrow
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.right: aclNameText.left
                                    anchors.rightMargin: root.aclArrowGap
                                    text: root.aclHas(modelData.rights, "read") ? "◂" : ""
                                    color: "#333333"
                                    opacity: aclChip.textOpacity
                                    font.pixelSize: root.tagChipFontPx
                                }
                                Text {
                                    id: aclNameText
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.right: aclWriteArrow.left
                                    anchors.rightMargin: root.aclArrowGap
                                    // As wide as the name, elided only when the chip is too narrow.
                                    width: Math.max(0, Math.min(implicitWidth, aclWriteArrow.x - root.aclArrowGap
                                        - (aclRightsText.x + aclRightsText.width + 6 + aclArrowMetrics.advanceWidth("◂") + root.aclArrowGap)))
                                    text: modelData.name
                                    color: "#333333"
                                    opacity: aclChip.textOpacity
                                    font.pixelSize: root.tagChipFontPx
                                    elide: Text.ElideLeft
                                    horizontalAlignment: Text.AlignRight
                                }
                                Text {
                                    id: aclWriteArrow
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.right: parent.right
                                    anchors.rightMargin: root.tagChipPadH
                                    width: Math.ceil(aclArrowMetrics.advanceWidth("▸"))
                                    text: root.aclHas(modelData.rights, "write") ? "▸" : ""
                                    color: "#333333"
                                    opacity: aclChip.textOpacity
                                    font.pixelSize: root.tagChipFontPx
                                    horizontalAlignment: Text.AlignRight
                                }
                                MouseArea {
                                    id: aclChipMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.aclPrincipalToggled(modelData.id)
                                }
                                ToolTip.visible: aclChipMouse.containsMouse
                                ToolTip.delay: 600
                                ToolTip.text: root.aclChipTip(modelData)
                            }
                        }
                    }
                }
            }
        }
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

            // Zeile 1: P-Button + Edit/Exit-Button
            Row {
                width: parent.width
                spacing: root.sidePanelButtonSpacing

                // P-Button: immer sichtbar, ausgegraut wenn bereits Projektordner; sonst stark in Projektfarbe
                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: root.hasProjectInCwp ? root.smallButtonBg : root.pButtonActiveColor
                    border.color: root.hasProjectInCwp ? root.smallButtonBorder : root.pButtonActiveColor
                    opacity: root.hasProjectInCwp ? 0.5 : 1
                    Text {
                        anchors.centerIn: parent
                        text: "P"
                        color: root.hasProjectInCwp ? root.smallButtonText : "#ffffff"
                        font.pixelSize: Math.round(root.baseFont * 0.9)
                        font.bold: true
                    }
                    MouseArea {
                        anchors.fill: parent
                        enabled: !root.hasProjectInCwp
                        onClicked: root.createProject()
                    }
                }

                // Edit-Button / Exit-Button: immer sichtbar, halbtransparent wenn kein .MyOS
                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: root.smallButtonBg
                    border.color: root.smallButtonBorder
                    visible: !root.showLeaveMyosButton
                    opacity: root.hasMyosDirInCwp ? 1 : 0.5
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
                        onClicked: root.hasMyosDirInCwp ? root.openMyosFolder() : root.createMyosAndEnter()
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
            }

            // Zeile 2: Ordner ein-/ausblenden + X-Ray
            Row {
                width: parent.width
                spacing: root.sidePanelButtonSpacing

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

                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: root.smallButtonBg
                    border.color: root.smallButtonBorder
                    Image {
                        anchors.centerIn: parent
                        source: root.iconFolderXray || root.iconFolderOff
                        width: root.topRightIconSize
                        height: root.topRightIconSize
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: width
                        sourceSize.height: height
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.xrayClicked()
                    }
                }
            }

            // Zeile 3: Kacheln/Liste umschalten (Icon zeigt die Ansicht, zu der gewechselt wird)
            Row {
                width: parent.width
                spacing: root.sidePanelButtonSpacing

                Rectangle {
                    radius: root.chipRadiusMedium
                    width: root.topRightButtonSize
                    height: root.topRightButtonSize
                    color: root.smallButtonBg
                    border.color: root.smallButtonBorder
                    Image {
                        anchors.centerIn: parent
                        source: root.itemStyle === "largeIcon"
                            ? Qt.resolvedUrl("Theme/icons/view_list.svg")
                            : Qt.resolvedUrl("Theme/icons/view_tiles.svg")
                        width: root.topRightIconSize
                        height: root.topRightIconSize
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: width
                        sourceSize.height: height
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.itemStyleToggleRequested()
                    }
                }
            }

            Text {
                id: folderSizeLabel
                width: parent.width
                // Off: "Größe –" (hover to measure); measuring: "…" until a first value arrives.
                text: !root.folderSizesActive
                    ? qsTr("Größe") + " –"
                    : (root.folderSizeBytes < 0
                        ? "…"
                        : (root.folderSizeComplete ? "" : "> ") + FormatUtils.formatBytes(root.folderSizeBytes))
                color: root.smallButtonText
                opacity: root.folderSizesActive ? 1.0 : 0.5
                font.pixelSize: root.tagSectionLabelPx
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onContainsMouseChanged: {
                        if (containsMouse && !root.folderSizesActive) sidebarSizeHoverTimer.restart()
                        else sidebarSizeHoverTimer.stop()
                    }
                    onClicked: root.folderSizesRequested()
                }
                Timer {
                    id: sidebarSizeHoverTimer
                    interval: root.folderSizesHoverDelayMs
                    onTriggered: root.folderSizesRequested()
                }
            }

            Rectangle {
                width: parent.width
                height: Math.max(80, parent.height - (3 * root.topRightButtonSize) - root.sidePanelButtonSpacing - (2 * root.sidePanelInnerMargin) - 20
                    - folderSizeLabel.height - root.sidePanelInnerMargin)
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
                                                        // Reset the input first: adding the tag changes the
                                                        // suggestions and destroys this delegate, after which
                                                        // its ids no longer resolve.
                                                        var suggestion = String(modelData || "").trim()
                                                        newFolderTagInput.text = ""
                                                        newFolderTagInput.suppressCompletion = true
                                                        newFolderTagInput.focus = false
                                                        if (suggestion.length > 0) {
                                                            root.addFolderTagRequested(suggestion)
                                                        }
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
                                        visible: root.fileTags && root.fileTags.length > 0
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
        anchors.left: aclPanel.visible ? aclPanel.right : parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: sidePanel.left
        anchors.leftMargin: aclPanel.visible ? root.filesPanelFrameMarginRight : root.filesPanelFrameMargin
        anchors.topMargin: root.filesPanelFrameMargin
        anchors.bottomMargin: root.filesPanelFrameMargin
        anchors.rightMargin: root.filesPanelFrameMarginRight
        radius: 12
        color: root.filesPanelOverlayColor
        border.width: 0
        z: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: (aclPanel.visible ? aclPanel.anchors.leftMargin + aclPanel.width + root.filesPanelFrameMarginRight
                                              : root.filesPanelFrameMargin) + root.filesPanelContentPadding
        anchors.topMargin: root.filesPanelFrameMargin + root.filesPanelContentPadding
        anchors.bottomMargin: root.filesPanelFrameMargin + root.filesPanelContentPadding
        anchors.rightMargin: sidePanel.width + root.filesPanelFrameMarginRight + root.filesPanelContentPadding
        spacing: 8

        // List view header: column titles aligned with the row cells; right-click selects columns.
        Item {
            id: listHeader
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? Math.round(root.listDetailFontPx * 1.8) : 0
            visible: root.itemStyle !== "largeIcon"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 12 + root.iconSizeSmall + root.listLayout.nameX
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Name") + root.sortArrow("name")
                color: root.textMuted
                font.pixelSize: root.listDetailFontPx
                font.bold: true
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -4
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.sortRequested("name")
                }
            }
            Item {
                // Same geometry as the row cells (FolderItem: 6 px inset + column x).
                x: 6
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                Repeater {
                    model: root.listLayout.columns
                    delegate: Text {
                        readonly property bool isSize: modelData.id === "size"
                        x: modelData.x
                        anchors.verticalCenter: parent.verticalCenter
                        width: modelData.width
                        horizontalAlignment: modelData.align === "right" ? Text.AlignRight : Text.AlignLeft
                        // "… " in front: the size head is right-aligned, so the title itself stays put.
                        text: (isSize && root.folderSizesMeasuring ? "… " : "")
                            + root.listColumnTitle(modelData.id)
                            + root.sortArrow(modelData.id)
                        color: root.textMuted
                        // Size head dimmed while folder sizes are off: hovering it measures them.
                        opacity: isSize && !root.folderSizesActive ? 0.5 : 1.0
                        font.pixelSize: root.listDetailFontPx
                        font.bold: true
                        elide: modelData.align === "right" ? Text.ElideLeft : Text.ElideRight
                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: parent.isSize
                            cursorShape: Qt.PointingHandCursor
                            onContainsMouseChanged: {
                                if (parent.isSize && containsMouse && !root.folderSizesActive) sizeHeadHoverTimer.restart()
                                else sizeHeadHoverTimer.stop()
                            }
                            onClicked: {
                                // Without hover (touch, quick click) the click also starts measuring.
                                if (parent.isSize) root.folderSizesRequested()
                                root.sortRequested(modelData.id)
                            }
                        }
                        Timer {
                            id: sizeHeadHoverTimer
                            interval: root.folderSizesHoverDelayMs
                            onTriggered: root.folderSizesRequested()
                        }
                    }
                }
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: root.gridSpacing
                anchors.bottom: parent.bottom
                height: 1
                color: root.itemBorderColor
            }
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onClicked: function(mouse) {
                    listColumnsMenu.popup()
                }
            }
            Menu {
                id: listColumnsMenu
                Repeater {
                    model: FormatUtils.LIST_COLUMNS
                    delegate: MenuItem {
                        text: root.listColumnTitle(modelData.id)
                        checkable: true
                        checked: root.listColumns.indexOf(modelData.id) !== -1
                        onTriggered: root.toggleListColumn(modelData.id)
                    }
                }
            }
        }

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
                // List rows are clickable across their full width, like in any file manager.
                hitAreaFullButton: root.itemStyle !== "largeIcon"
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
                detailColumns: {
                    if (root.itemStyle === "largeIcon") return []
                    var cells = []
                    for (var c = 0; c < root.listLayout.columns.length; c++) {
                        var col = root.listLayout.columns[c]
                        cells.push({ text: FormatUtils.listCellText(col.id, model, root.folderSizesActive),
                            width: col.width, align: col.align, x: col.x })
                    }
                    return cells
                }
                nameOffsetX: root.itemStyle === "largeIcon" ? 0 : root.listLayout.nameX
                nameColumnWidth: root.itemStyle === "largeIcon" ? 0 : root.listNameColumnWidth
                largeIconAlignLeft: false
                // Drags are run by the panel (fileDragHandler), not by the delegate:
                // a list refresh mid-drag would destroy a delegate-owned drag.
                dragEnabled: false
                readonly property bool canDrag: root.allowDrags
                    && (!model.isEmbryo)
                    && itemPath.length > 0
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
                        var fullPath = (itemPath && itemPath.length > 0) ? itemPath : ""
                        if (fullPath.length > 0) root.navigationRequested(fullPath, "double", "filesPanel")
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
                    // Embryos accept drops too; the backend births them on move.
                    enabled: model.isDir
                    onDropped: function(drop) {
                        var payload = DropUtils.payloadText(drop)
                        if (payload.length === 0 || itemPath.length === 0) return
                        root.moveEntriesRequested(payload, itemPath)
                        drop.acceptProposedAction()
                    }
                }
            }
            // File drags start here and outlive the delegates: the hover preview may
            // rebuild the list while a file is held, and the drag must survive that.
            // The handler belongs to the GridView, an ancestor of the rows: on the overlay
            // above them it took every press, so clicks and double-clicks never reached
            // the rows. pressPosition is in grid coordinates, as the overlay's were.
            DragHandler {
                id: fileDragHandler
                target: null
                acceptedButtons: Qt.LeftButton
                enabled: root.allowDrags
                onActiveChanged: {
                    if (active) {
                        root.beginFileDrag(centroid.pressPosition)
                    } else {
                        root.endFileDrag(true)
                    }
                }
                onCentroidChanged: {
                    if (active) root.moveFileDrag(centroid.scenePosition)
                }
                onCanceled: root.endFileDrag(false)
            }
            onContentYChanged: {
                if (contentHeight <= height) return
                if ((contentY + height + root.prefetchThreshold) >= contentHeight) {
                    root.requestMore()
                }
            }
        }

        // Resting the pointer on the size column (not only its head) asks for folder sizes.
        // A HoverHandler only watches: clicks, selection and drags still reach the rows.
        Item {
            parent: filesGrid
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            x: root.sizeColumn ? 6 + root.sizeColumn.x : 0
            width: root.sizeColumn ? root.sizeColumn.width : 0
            visible: root.itemStyle !== "largeIcon" && root.sizeColumn !== null && !root.folderSizesActive
            HoverHandler {
                id: sizeColumnHover
                onHoveredChanged: {
                    if (hovered) sizeColumnHoverTimer.restart()
                    else sizeColumnHoverTimer.stop()
                }
            }
            Timer {
                id: sizeColumnHoverTimer
                interval: root.folderSizesHoverDelayMs
                onTriggered: root.folderSizesRequested()
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
                    var payload = DropUtils.payloadText(drop)
                    if (payload.length === 0) return
                    var contentX = filesGrid.contentX || 0
                    var contentY = filesGrid.contentY || 0
                    var idx = filesGrid.indexAt(drop.x + contentX, drop.y + contentY)
                    var item = idx >= 0 ? filesGrid.itemAtIndex(idx) : null
                    var targetDir = (item && item.isFolder && item.itemPath && item.itemPath.length > 0)
                        ? item.itemPath
                        : root.currentPath
                    if (!targetDir || targetDir.length === 0) return
                    root.moveEntriesRequested(payload, targetDir)
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

    // Drag source while a file is held. Lives in the window overlay so it is drawn
    // above all panels and is independent of the (rebuildable) file list.
    Item {
        id: fileDragProxy
        parent: Overlay.overlay
        z: 1000
        visible: Drag.active
        /// Read by drop targets via drop.source.dragPayload (see FolderBrowser.dropPayloadText).
        property string dragPayload: ""
        property alias ghostSource: fileDragGhost.source
        Image {
            id: fileDragGhost
            anchors.fill: parent
            opacity: 0.85
        }
        Drag.dragType: Drag.Internal
        Drag.supportedActions: Qt.MoveAction
        Drag.mimeData: ({ "text/plain": fileDragProxy.dragPayload })
    }
}
