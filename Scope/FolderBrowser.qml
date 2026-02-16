import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "Theme/tag_chips.js" as TagChips

Item { // ROOT
    id: root
    property int horizontalPreferredWidth: 640
    property int verticalPreferredWidth: 0
    property int verticalMinWidth: 120
    property int verticalMaxWidth: 560
    property int horizontalPreferredHeight: compactButtonHeight * 2 + (searchActive ? (compactButtonHeight + 8) : 0) + 12
    property int verticalPreferredHeight: 360
    implicitWidth: visible ? (verticalView ? verticalAutoWidth : horizontalPreferredWidth) : 0
    implicitHeight: visible ? contentHeight : 0
    property string path: "/"
    property string pathDisplayPrefix: ""
    property var folders: []
    property var childrenProvider: null
    property var pathColorFunction: null    
    property bool verticalView: false
    property string buttonStyle: "text"
    property bool allowLargeIcons: true
    property bool showModeToggle: true
    property bool showSearchToggle: false
    property bool showStyleToggle: true
    property bool showThemeToggle: false
    property bool showEmbryos: true
    property bool showEmbryoToggle: true
    property bool searchActive: false
    property string searchText: ""
    property bool allowRename: false
    property bool allowDrags: false
    property bool allowDrops: false
    property string renameTargetPath: ""
    property string renameDraft: ""
    property int baseFont: 14
    property int compactButtonHeight: 32
    property int largeButtonHeight: 72
    property int largeButtonPadding: 6
    property int buttonTextYOffset: Math.round(compactButtonHeight * 0.05)
    property int iconSizeSmall: 20
    property int iconSizeLarge: 48
    property int maxParents: 4
    property int verticalParentSpacing: 6
    property int indent: 0
    property string iconFolder: ""
    property string iconSearch: ""
    property color panelColor: "#1b1d26"
    property color panelBorderColor: "#3a4158"
    property color panelAltColor: "#151821"
    property color accentPrimary: "#524dbe"
    property color accentPrimaryText: "#ffffff"
    property color pill: "#2a2f40"
    property color pillBorder: "#3a4158"
    property color smallButtonBg: pill
    property color smallButtonBorder: pillBorder
    property color smallButtonActiveBg: accentSecondary
    property color smallButtonActiveBorder: accentSecondaryBorder
    property color smallButtonText: textSoft
    property color accentSecondary: "#3b476b"
    property color accentSecondaryBorder: "#58648a"
    property color text: "#e6e6e6"
    property color textSoft: "#cfd3df"
    property color textMuted: "#c9ccd7"
    property color card: "#0f1117"
    property color projectTint: "#7b5bd6"
    property color projectTintBorder: "#7b5bd6"
    property color pathButtonFill: pill
    property color pathButtonBorder: pillBorder
    property color folderButtonFill: pill
    property color folderButtonBorder: pillBorder
    property bool tintPathAsProject: false
    property real cwdOpacity: 1.0
    property real pathProjectOpacity: 0.7
    property real folderProjectOpacity: 0.55
    property real embryoOpacity: 0.4
    readonly property color currentPathFillColor: {
        var custom = pathColorFunction ? pathColorFunction(path, true) : null
        if (custom && custom.fill !== undefined) {
            return custom.fill
        }
        return accentPrimary
    }

    signal pathSegmentActivated(int index)
    signal pathSelected(string path)
    signal folderActivated(string name)
    signal toggleMode()
    signal toggleSearch()
    signal toggleTheme()
    signal styleChanged(string style)
    signal toggleEmbryos()
    signal renameRequested(string fullPath)
    signal renameTextEdited(string text)
    signal renameAccepted()
    signal renameCanceled()
    signal searchTextEdited(string value)
    signal moveEntryRequested(string sourcePath, string targetDir)

    property bool flowOnSecondLine: false
    property bool layoutUpdatePending: false
    property bool debugLayout: false
    property int wrapSlackOn: 10
    property int wrapSlackOff: 60
    property bool verticalButtonsOnSecondLine: false
    property bool verticalLayoutUpdatePending: false
    property bool debugVerticalWrap: true
    property bool foldersInSecondColumn: false
    property int verticalAutoWidth: 0
    property int verticalColumnWidth: 0
    property int verticalRightColumnWidth: 0
    property bool verticalWidthUpdatePending: false
    property int contentHeight: 0
    property bool contentHeightUpdatePending: false
    property bool contentHeightSettlePending: false
    property int cwdTabDrop: 4
    property int cwdVerticalRightOverflow: 10
    property bool previewEnabled: true
    property bool previewFocusBackground: false
    property var previewRows: []
    property var previewActivePaths: []
    property var previewAnchorCenters: []
    property real previewDimOpacity: 1.0
    property bool previewDebugBg: false
    property int previewRowSpacing: 1
    property real previewShadeSliderMix: 0.65
    readonly property real previewRowShadeMix: Math.max(0, Math.min(1, 1 - previewShadeSliderMix))
    property int previewExpandDurationMs: 300
    property int previewCollapseDurationMs: 700
    property int contentHeightAnimDurationMs: 110
    property int previewTabDropPx: 4
    property bool previewHeightSyncPending: false
    property string previewLastHoverKey: ""

    TextMetrics {
        id: labelMetrics
        font.pixelSize: baseFont
    }

    function effectiveStyle() {
        if (!allowLargeIcons && buttonStyle === "largeIcon") return "text"
        return buttonStyle
    }

    function estimateButtonWidth(label, styleName) {
        labelMetrics.text = String(label === undefined || label === null ? "" : label)
        var textWidth = labelMetrics.width
        if (styleName === "smallIcon") {
            return Math.max(80, textWidth + iconSizeSmall + 30)
        }
        if (styleName === "largeIcon") {
            return Math.max(80, Math.max(iconSizeLarge, textWidth) + 20)
        }
        return Math.max(80, textWidth + 24)
    }

    function itemName(item) {
        return (item && item.name) ? item.name : item
    }

    function itemIsProject(item) {
        return item && item.isProject === true
    }

    function itemIsEmbryo(item) {
        return item && item.isEmbryo === true
    }

    function normalizeColor(value) {
        if (!value) return null
        if (typeof value === "string") {
            var hex = value.trim()
            if (hex.length === 4) {
                var r = parseInt(hex[1] + hex[1], 16) / 255
                var g = parseInt(hex[2] + hex[2], 16) / 255
                var b = parseInt(hex[3] + hex[3], 16) / 255
                return { r: r, g: g, b: b }
            }
            if (hex.length === 7) {
                var r6 = parseInt(hex.slice(1, 3), 16) / 255
                var g6 = parseInt(hex.slice(3, 5), 16) / 255
                var b6 = parseInt(hex.slice(5, 7), 16) / 255
                return { r: r6, g: g6, b: b6 }
            }
        }
        if (value.r !== undefined && value.g !== undefined && value.b !== undefined) {
            return value
        }
        return null
    }

    function _hexByte(value) {
        var n = Math.max(0, Math.min(255, Math.round(Number(value) * 255)))
        var text = n.toString(16).toUpperCase()
        return text.length < 2 ? ("0" + text) : text
    }

    function colorToHex(value, fallback) {
        var base = normalizeColor(value) || normalizeColor(fallback)
        if (!base) {
            return "#000000"
        }
        return "#" + _hexByte(base.r) + _hexByte(base.g) + _hexByte(base.b)
    }

    function colorWithAlpha(value, alpha, fallback) {
        var base = normalizeColor(value) || normalizeColor(fallback)
        if (!base) return Qt.rgba(1, 1, 1, alpha)
        return Qt.rgba(base.r, base.g, base.b, alpha)
    }

    function blendColors(topColor, bottomColor, mix) {
        var top = normalizeColor(topColor)
        var bottom = normalizeColor(bottomColor)
        var t = Math.max(0, Math.min(1, Number(mix)))
        if (!top && !bottom) return panelColor
        if (!top) return Qt.rgba(bottom.r, bottom.g, bottom.b, 1)
        if (!bottom) return Qt.rgba(top.r, top.g, top.b, 1)
        var inv = 1 - t
        return Qt.rgba(
            top.r * inv + bottom.r * t,
            top.g * inv + bottom.g * t,
            top.b * inv + bottom.b * t,
            1
        )
    }

    function folderFillColor(item) {
        if (itemIsProject(item)) {
            if (item && item.color) {
                return colorWithAlpha(item.color, folderProjectOpacity, projectTint)
            }
            return folderButtonFill
        }
        if (itemIsEmbryo(item)) {
            return colorWithAlpha(item.color, embryoOpacity, projectTint)
        }
        return folderButtonFill
    }

    function folderStrokeColor(item) {
        if (itemIsProject(item)) {
            if (item && item.color) {
                return colorWithAlpha(item.color, folderProjectOpacity, projectTintBorder)
            }
            return folderButtonBorder
        }
        if (itemIsEmbryo(item)) {
            return colorWithAlpha(item.color, embryoOpacity, projectTintBorder)
        }
        return folderButtonBorder
    }

    function currentRowHeight() {
        return effectiveStyle() === "largeIcon" ? largeButtonHeight : compactButtonHeight
    }

    function calculateVerticalAutoWidth() {
        if (!verticalView) return verticalPreferredWidth > 0 ? verticalPreferredWidth : verticalMinWidth
        var maxWidth = 0
        var pathStyle = (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
        var parts = visibleParentPaths()
        for (var i = 0; i < parts.length; i++) {
            var label = parts[i].split("/").filter(function(p){ return p.length > 0 }).slice(-1)[0]
            maxWidth = Math.max(maxWidth, estimateButtonWidth(label, pathStyle))
        }
        var displayParts = pathPartsDisplay()
        var currentLabel = displayParts.length ? displayParts[displayParts.length - 1] : "/"
        maxWidth = Math.max(maxWidth, estimateButtonWidth(currentLabel, pathStyle))
        var folderStyle = effectiveStyle()
        if (!foldersInSecondColumn) {
            for (var f = 0; f < folders.length; f++) {
                maxWidth = Math.max(maxWidth, estimateButtonWidth(itemName(folders[f]), folderStyle))
            }
        }
        var buttonsWidth = (showModeToggle ? compactButtonHeight + 6 : 0) + verticalButtonsPanel.implicitWidth
        maxWidth = Math.max(maxWidth, buttonsWidth + 12)
        var padded = maxWidth + 32
        var columnWidth = Math.min(verticalMaxWidth, Math.max(verticalMinWidth, padded))
        var rightWidth = calculateFoldersColumnWidth()
        verticalColumnWidth = columnWidth
        verticalRightColumnWidth = rightWidth
        var gap = verticalContentRow ? verticalContentRow.spacing : 12
        return foldersInSecondColumn ? (columnWidth + rightWidth + gap) : columnWidth
    }

    function calculateFoldersColumnWidth() {
        if (!folders || folders.length === 0) return verticalMinWidth
        var maxWidth = 0
        var folderStyle = effectiveStyle()
        for (var f = 0; f < folders.length; f++) {
            maxWidth = Math.max(maxWidth, estimateButtonWidth(itemName(folders[f]), folderStyle))
        }
        var padded = maxWidth + 32
        return Math.max(verticalMinWidth, padded)
    }

    function calculateContentHeight() {
        if (!mainColumn) return 0
        if (verticalView) {
            return Math.round(verticalMainColumn.childrenRect.height + 12)
        }
        var top = topRow ? topRow.implicitHeight : 0
        var bottom = (bottomRow && bottomRow.visible) ? (bottomRow.implicitHeight + mainColumn.spacing) : 0
        var preview = (previewStack && previewStack.visible)
            ? (previewStack.height + mainColumn.spacing)
            : 0
        return Math.round(top + bottom + preview + 0)
    }

    function scheduleContentHeightUpdate() {
        if (contentHeightUpdatePending) return
        contentHeightUpdatePending = true
        Qt.callLater(function() {
            contentHeightUpdatePending = false
            if (contentHeightSettlePending) {
                return
            }
            contentHeightSettlePending = true
            Qt.callLater(function() {
                contentHeightSettlePending = false
                var settledHeight = calculateContentHeight()
                if (Math.abs(contentHeight - settledHeight) >= 1) {
                    contentHeight = settledHeight
                }
            })
        })
    }

    function isPreviewPathActive(level, fullPath) {
        if (!previewActivePaths || level < 0 || level >= previewActivePaths.length) {
            return false
        }
        return String(previewActivePaths[level] || "") === String(fullPath || "")
    }

    function previewPathForLevel(level) {
        if (!previewActivePaths || level < 0 || level >= previewActivePaths.length) {
            return ""
        }
        return String(previewActivePaths[level] || "")
    }

    function _debugPreviewBgState(label) {
        if (!(previewDebugBg || debugLayout)) {
            return
        }
        var colors = []
        var formatted = []
        for (var i = 0; i < previewRows.length; i++) {
            var row = previewRows[i]
            if (!row) {
                colors.push("null")
                formatted.push("L" + String(i + 1) + ": null")
                continue
            }
            var colorText = colorToHex(row.color, panelColor)
            colors.push(colorText)
            formatted.push("L" + String(i + 1) + ": " + colorText)
        }
        console.log("Debug:", formatted.join(", "))
        console.log(
            "[preview-bg]",
            String(label || ""),
            "focus=", previewFocusBackground,
            "active=", JSON.stringify(previewActivePaths || []),
            "rows=", previewRows.length,
            "colors=", JSON.stringify(colors)
        )
    }

    function _samePathArray(a, b) {
        if (a === b) {
            return true
        }
        if (!a || !b || a.length !== b.length) {
            return false
        }
        for (var i = 0; i < a.length; i++) {
            if (String(a[i] || "") !== String(b[i] || "")) {
                return false
            }
        }
        return true
    }

    function _setPreviewActivePath(level, basePath) {
        var nextActive = previewActivePaths.slice(0, level)
        nextActive.push(basePath)
        if (_samePathArray(previewActivePaths, nextActive)) {
            return
        }
        previewActivePaths = nextActive
    }

    onVerticalButtonsOnSecondLineChanged: {
        if (verticalButtonsSlotTop) {
            setButtonsParent(verticalButtonsPanel, verticalButtonsSlotTop)
        }
    }

    Component.onCompleted: {
        if (verticalButtonsSlotTop) {
            setButtonsParent(verticalButtonsPanel, verticalButtonsSlotTop)
        }
        resetPreview()
        scheduleVerticalLayoutUpdate()
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
        initialLayoutSyncTimer.restart()
    }

    onVisibleChanged: {
        scheduleVerticalLayoutUpdate()
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }

    onVerticalViewChanged: {
        if (!verticalView) {
            verticalButtonsOnSecondLine = false
        }
        scheduleVerticalLayoutUpdate()
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }

    onPathChanged: {
        resetPreview()
        scheduleVerticalWidthUpdate()
    }
    onFoldersChanged: {
        resetPreview()
        scheduleVerticalWidthUpdate()
    }
    onButtonStyleChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onIconSizeSmallChanged: scheduleVerticalWidthUpdate()
    onIconSizeLargeChanged: scheduleVerticalWidthUpdate()
    onBaseFontChanged: scheduleVerticalWidthUpdate()
    onCompactButtonHeightChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onLargeButtonHeightChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onLargeButtonPaddingChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onIndentChanged: scheduleVerticalWidthUpdate()
    onShowModeToggleChanged: scheduleVerticalWidthUpdate()
    onShowStyleToggleChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onShowSearchToggleChanged: {
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onFoldersInSecondColumnChanged: {
        scheduleVerticalWidthUpdate()
        scheduleVerticalLayoutUpdate()
        scheduleContentHeightUpdate()
    }
    onSearchActiveChanged: scheduleContentHeightUpdate()
    onFlowOnSecondLineChanged: scheduleContentHeightUpdate()
    onPreviewEnabledChanged: {
        resetPreview()
        scheduleContentHeightUpdate()
    }
    onPreviewRowsChanged: {
        scheduleContentHeightUpdate()
        _debugPreviewBgState("rowsChanged")
    }
    onPreviewFocusBackgroundChanged: _debugPreviewBgState("focusToggle")

    Timer {
        id: initialLayoutSyncTimer
        interval: 40
        repeat: false
        onTriggered: {
            root.scheduleVerticalLayoutUpdate()
            root.scheduleVerticalWidthUpdate()
            root.scheduleContentHeightUpdate()
        }
    }

    Timer {
        id: previewHeightSyncTimer
        interval: 16
        repeat: false
        onTriggered: {
            root.previewHeightSyncPending = false
            root.scheduleContentHeightUpdate()
        }
    }


    function pathPartsFull() {
        return path.split("/").filter(function(p){ return p.length > 0 })
    }

    function prefixParts() {
        if (!pathDisplayPrefix || pathDisplayPrefix.length === 0) return []
        var prefix = pathDisplayPrefix
        if (prefix.endsWith("/") && prefix.length > 1) {
            prefix = prefix.slice(0, -1)
        }
        if (prefix === path) {
            return prefix.split("/").filter(function(p){ return p.length > 0 })
        }
        if (path.indexOf(prefix + "/") === 0) {
            return prefix.split("/").filter(function(p){ return p.length > 0 })
        }
        return []
    }

    function pathPartsDisplay() {
        var fullParts = pathPartsFull()
        var prefix = prefixParts()
        if (prefix.length === 0) return fullParts
        var remainder = fullParts.slice(prefix.length)
        var root = prefix[prefix.length - 1]
        if (remainder.length === 0) return [root]
        return [root].concat(remainder)
    }

    function getPathSegmentColor(fullPath, isCurrent) {
        // Resolve effective path color directly; do not depend on current folder list.
        if (pathColorFunction) {
            var direct = pathColorFunction(String(fullPath || ""), !!isCurrent)
            if (direct && direct.fill !== undefined) {
                return {
                    fill: direct.fill,
                    stroke: (direct.stroke !== undefined) ? direct.stroke : direct.fill
                };
            }
        }
        // Prüfe, ob dieser Pfad in der folders-Liste vorkommt
        for (var i = 0; i < folders.length; i++) {
            var folder = folders[i];
            var folderPath = typeof folder === 'string' ? folder : folder.path || folder.name;
            
            // Vergleiche den vollen Pfad
            if (fullPath === folderPath || 
                (fullPath.endsWith("/" + folderPath) || fullPath === "/" + folderPath)) {
                if (itemIsProject(folder)) {
                    return {
                        fill: colorWithAlpha(folder.color, isCurrent ? cwdOpacity : pathProjectOpacity, projectTint),
                        stroke: colorWithAlpha(folder.color, isCurrent ? cwdOpacity : pathProjectOpacity, projectTintBorder)
                    };
                }
            }
        }
        
        // Fallback: Standard-Farben
        return {
            fill: isCurrent 
                ? accentPrimary
                : pathButtonFill,
            stroke: isCurrent
                ? accentPrimary
                : pathButtonBorder
        };
    }    
    
    function getFolderPath(folder) {
        if (typeof folder === 'string') return folder;
        return folder.path || folder.name || "";
    }    

    function _resolveFullPath(basePath, item) {
        var raw = String(getFolderPath(item) || "")
        if (!raw) return ""
        if (raw.indexOf("/") === 0) return raw
        var base = String(basePath || "").trim()
        if (!base) {
            base = path
        }
        if (base.length > 1 && base.endsWith("/")) {
            base = base.slice(0, -1)
        }
        return base + "/" + raw
    }

    function _previewColorForItem(item, sourcePath, sourceFillColor) {
        if (sourceFillColor !== undefined && sourceFillColor !== null) {
            return sourceFillColor
        }
        // Keep row background in sync with the hovered folder's own fill color.
        // This mirrors the delegate fillColor used in the preview rows.
        var fill = folderFillColor(item)
        if (fill !== undefined && fill !== null) {
            return fill
        }
        if (pathColorFunction) {
            var custom = pathColorFunction(String(sourcePath || ""), false)
            if (custom && custom.fill !== undefined) {
                return custom.fill
            }
        }
        return panelColor
    }

    function listPreviewChildren(parentPath) {
        if (!childrenProvider) {
            return []
        }
        try {
            var rows = childrenProvider(parentPath)
            return rows || []
        } catch (e) {
            return []
        }
    }

    function resetPreview() {
        previewRows = []
        previewActivePaths = []
        previewAnchorCenters = []
        previewLastHoverKey = ""
    }

    function _samePreviewRows(a, b) {
        if (a === b) {
            return true
        }
        if (!a || !b || a.length !== b.length) {
            return false
        }
        for (var i = 0; i < a.length; i++) {
            var left = a[i]
            var right = b[i]
            if (!left || !right) {
                return false
            }
            if (Number(left.level) !== Number(right.level)) {
                return false
            }
            if (String(left.parentPath || "") !== String(right.parentPath || "")) {
                return false
            }
            var leftColor = normalizeColor(left.color)
            var rightColor = normalizeColor(right.color)
            if (!!leftColor !== !!rightColor) {
                return false
            }
            if (leftColor && rightColor) {
                if (Math.abs(leftColor.r - rightColor.r) > 0.0001
                        || Math.abs(leftColor.g - rightColor.g) > 0.0001
                        || Math.abs(leftColor.b - rightColor.b) > 0.0001) {
                    return false
                }
            }
            var leftEntries = left.entries || []
            var rightEntries = right.entries || []
            if (leftEntries.length !== rightEntries.length) {
                return false
            }
            for (var j = 0; j < leftEntries.length; j++) {
                if (String(itemName(leftEntries[j])) !== String(itemName(rightEntries[j]))) {
                    return false
                }
            }
        }
        return true
    }

    function _setPreviewAnchorCenter(level, centerX) {
        var x = Number(centerX)
        if (!isFinite(x)) {
            return
        }
        var nextCenters = previewAnchorCenters.slice(0, level)
        nextCenters.push(x)
        if (_samePathArray(previewAnchorCenters, nextCenters)) {
            return
        }
        previewAnchorCenters = nextCenters
    }

    function previewAnchorCenterForLevel(level) {
        if (!previewAnchorCenters || level < 0 || level >= previewAnchorCenters.length) {
            return -1
        }
        var x = Number(previewAnchorCenters[level])
        return isFinite(x) ? x : -1
    }

    function _applyPreviewHover(level, basePath, sourceItem, sourceFillColor) {
        var hoverKey = String(level) + "|" + basePath + "|" + String(sourceFillColor)
        if (hoverKey === previewLastHoverKey) {
            return
        }
        previewLastHoverKey = hoverKey
        var children = listPreviewChildren(basePath)
        var nextRows = previewRows.slice(0, level)
        // Collapse deeper rows when the currently hovered item has no children.
        // This prevents stale lower rows from suggesting wrong descendants.
        if (children.length === 0) {
            if (_samePreviewRows(previewRows, nextRows)) {
                return
            }
            previewRows = nextRows
            return
        }

        if (children.length > 0) {
            var rowColor = colorToHex(_previewColorForItem(sourceItem, basePath, sourceFillColor), panelColor)
            nextRows.push({
                level: level,
                parentPath: basePath,
                color: rowColor,
                entries: children
            })
        }

        if (_samePreviewRows(previewRows, nextRows)) {
            return
        }
        previewRows = nextRows
    }

    function updatePreviewFromHover(sourceLevel, sourcePath, sourceItem, sourceFillColor, sourceCenterX) {
        if (!previewEnabled || verticalView) {
            return
        }
        var level = Math.max(0, Number(sourceLevel) || 0)
        var basePath = String(sourcePath || "").trim()
        if (!basePath) {
            return
        }
        // Keep tab feedback immediate even while row animations run.
        _setPreviewActivePath(level, basePath)
        _setPreviewAnchorCenter(level, sourceCenterX)
        _debugPreviewBgState("hoverBeforeApply")
        _applyPreviewHover(level, basePath, sourceItem, sourceFillColor)
        _debugPreviewBgState("hoverAfterApply")
    }
    
    function fullPathForDisplayIndex(index) {
        var fullParts = pathPartsFull()
        var prefix = prefixParts()
        if (prefix.length === 0) {
            return "/" + fullParts.slice(0, index + 1).join("/")
        }
        if (index <= 0) {
            return "/" + prefix.join("/")
        }
        var remainder = fullParts.slice(prefix.length)
        var target = prefix.concat(remainder.slice(0, index))
        return "/" + target.join("/")
    }

    function pathParts() {
        return pathPartsFull()
    }

    function parentPaths() {
        var parts = pathPartsFull()
        var prefix = prefixParts()
        var startIndex = 0
        if (prefix.length > 0) {
            startIndex = Math.max(0, prefix.length - 1)
        }
        var paths = []
        for (var i = startIndex; i < parts.length - 1; i++) {
            paths.push("/" + parts.slice(0, i + 1).join("/"))
        }
        return paths
    }

    function visibleParentPaths() {
        var parents = parentPaths()
        if (parents.length <= maxParents) return parents
        return parents.slice(Math.max(0, parents.length - maxParents))
    }

    function scheduleLayoutUpdate() {
        if (layoutUpdatePending) return
        layoutUpdatePending = true
        Qt.callLater(function() {
            updateFlowPlacement()
            layoutUpdatePending = false
        })
    }

    function scheduleVerticalWidthUpdate() {
        if (verticalWidthUpdatePending) return
        verticalWidthUpdatePending = true
        Qt.callLater(function() {
            verticalAutoWidth = calculateVerticalAutoWidth()
            verticalPreferredWidth = verticalAutoWidth
            verticalWidthUpdatePending = false
        })
    }

    function scheduleVerticalLayoutUpdate() {
        if (verticalLayoutUpdatePending) return
        verticalLayoutUpdatePending = true
        Qt.callLater(function() {
            updateVerticalButtonsPlacement()
            verticalLayoutUpdatePending = false
        })
    }

    function updateFlowPlacement() {
        if (!topFoldersRow || !topRow || !rightButtonsRow || !pathRow) return
        if (topRow.width <= 0) return
        var toggleWidth = (showModeToggle && modeToggleButton) ? modeToggleButton.width : 0
        var gapCount = showModeToggle ? 4 : 3
        var rightWidth = rightButtonsRow.implicitWidth
        var used = pathRow.implicitWidth + topFoldersRow.implicitWidth + rightWidth + toggleWidth + (topRow.spacing * gapCount)
        var slack = topRow.width - used
        var shouldWrap = flowOnSecondLine ? (slack < wrapSlackOff) : (slack < wrapSlackOn)
        if (flowOnSecondLine !== shouldWrap) {
            flowOnSecondLine = shouldWrap
            if (debugLayout) {
                console.log("[folderbrowser] wrap", path, "->", shouldWrap, "row", topRow.width, "used", used, "slack", slack)
            }
        }
    }

    function updateVerticalButtonsPlacement() {
        if (!verticalView) return
        if (!verticalMainColumn || !verticalContentRow) return
        if (verticalContentRow.height <= 0) return
        var freeHeight          = verticalSpacer ? verticalSpacer.height : 0
        var uListHeight         = foldersContentRight ? foldersContentRight.implicitHeight : 0
        var shouldWrap          = foldersInSecondColumn
            ? (freeHeight*2 <= uListHeight + 10)
            : (freeHeight < 1)
        if (verticalButtonsOnSecondLine !== shouldWrap) {
            verticalButtonsOnSecondLine = shouldWrap
            foldersInSecondColumn = shouldWrap
        }
    }

    function setButtonsParent(item, newParent) {
        if (item && newParent && item.parent !== newParent) {
            item.parent = newParent
            item.anchors.fill = undefined
            item.x = 0
            item.y = 0
        }
    }


    Rectangle { // buttonsPool (dynamic)
        anchors.fill: parent
        color: panelColor
        border.width: 0
        radius: 0
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: panelBorderColor
            opacity: 0.45
        }
        Item {
            id: buttonsPool
            visible: false
        }

        Item {              // VERTICAL: ButtonsPanel
            id: verticalButtonsPanel
            parent: buttonsPool
            implicitWidth: verticalButtonsContent.implicitWidth
            implicitHeight: verticalButtonsContent.implicitHeight
            width: implicitWidth
            height: compactButtonHeight
            Row {           // VERTICAL: ButtonsContent
                id: verticalButtonsContent
                anchors.fill: parent
                spacing: 6
                Component.onCompleted: scheduleVerticalLayoutUpdate()
                onImplicitWidthChanged: {
                    scheduleVerticalLayoutUpdate()
                    scheduleVerticalWidthUpdate()
                }
                Rectangle { // VERTICAL: search toggle button (Lupe)
                    visible: showSearchToggle
                    width: compactButtonHeight
                    height: compactButtonHeight
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: pill
                    border.color: pillBorder
                    Image {
                        anchors.centerIn: parent
                        source: iconSearch
                        width: baseFont
                        height: baseFont
                        fillMode: Image.PreserveAspectFit
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: toggleSearch()
                    }
                }
                Rectangle { // VERTICAL: display options menu (style + embryos)
                    visible: showStyleToggle || showEmbryoToggle
                    width: compactButtonHeight
                    height: compactButtonHeight
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: pill
                    border.color: pillBorder
                    Text {
                        anchors.centerIn: parent
                        text: "\u2630"
                        color: textSoft
                        font.pixelSize: baseFont
                        font.bold: true
                    }
                    Menu {
                        id: verticalDisplayMenu
                        y: parent ? parent.height + 4 : 0
                        MenuItem {
                            text: qsTr("t Text")
                            visible: showStyleToggle
                            checkable: true
                            checked: buttonStyle === "text"
                            onTriggered: styleChanged("text")
                        }
                        MenuItem {
                            text: qsTr("G Gross")
                            visible: showStyleToggle && allowLargeIcons
                            checkable: true
                            checked: buttonStyle === "largeIcon"
                            onTriggered: styleChanged("largeIcon")
                        }
                        MenuItem {
                            text: qsTr("k Klein")
                            visible: showStyleToggle
                            checkable: true
                            checked: buttonStyle === "smallIcon"
                            onTriggered: styleChanged("smallIcon")
                        }
                        MenuSeparator {
                            visible: showStyleToggle && showEmbryoToggle
                        }
                        MenuItem {
                            text: qsTr("E Embryos")
                            visible: showEmbryoToggle
                            checkable: true
                            checked: showEmbryos
                            onTriggered: toggleEmbryos()
                        }
                        MenuItem {
                            text: qsTr("Vorschau")
                            checkable: true
                            checked: previewEnabled
                            onTriggered: previewEnabled = !previewEnabled
                        }
                        MenuItem {
                            text: qsTr("Vorschau Fokus-Hintergrund")
                            checkable: true
                            checked: previewFocusBackground
                            onTriggered: previewFocusBackground = !previewFocusBackground
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: verticalDisplayMenu.popup()
                    }
                }
            }
        }

        ColumnLayout {  // Which VIEW???:
            id: mainColumn
            anchors.fill: parent
            anchors.leftMargin: 6
            anchors.rightMargin: verticalView ? 0 : 6
            anchors.topMargin: 3
            anchors.bottomMargin: verticalView ? 3 : 0
            spacing: 4

            RowLayout { // HORIZONTAL: row 1 (path + folders + right buttons)
                id: topRow
                visible: !verticalView
                Layout.fillWidth: true
                Layout.preferredHeight: currentRowHeight()
                Layout.minimumHeight: currentRowHeight()
                Layout.maximumHeight: currentRowHeight()
                height: currentRowHeight()
                spacing: 6
                onWidthChanged: scheduleLayoutUpdate()

                Rectangle {
                    id: modeToggleButton
                    visible: showModeToggle
                    width: compactButtonHeight
                    height: compactButtonHeight
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: smallButtonBg
                    border.color: smallButtonBorder
                    Layout.alignment: Qt.AlignTop
                    Text {
                        anchors.centerIn: parent
                        text: verticalView ? "H" : "V"
                        color: smallButtonText
                        font.pixelSize: baseFont
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: toggleMode()
                    }
                }

                Item {  // HORIZONTAL: path segment row (breadcrumbs)
                    id: pathHost
                    Layout.fillWidth: flowOnSecondLine
                    Layout.preferredWidth: flowOnSecondLine ? 0 : pathRow.implicitWidth
                    Layout.preferredHeight: effectiveStyle() === "largeIcon" ? largeButtonHeight : compactButtonHeight
                    clip: true
                    Row {
                        id: pathRow
                        spacing: 6
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: pathRow.implicitWidth <= pathHost.width ? parent.left : undefined
                        anchors.right: pathRow.implicitWidth <= pathHost.width ? undefined : parent.right
                        onImplicitWidthChanged: scheduleLayoutUpdate()

                        Repeater {
                            model: pathPartsDisplay()
                            delegate: FolderItem {
                                property bool isCurrent: index === (pathPartsDisplay().length - 1)
                                property string fullPathForSegment: fullPathForDisplayIndex(index)
                                y: isCurrent ? root.cwdTabDrop : 0
                                label: itemName(modelData)
                                style: effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                textYOffset: buttonTextYOffset
                                iconSource: iconFolder
                                property var customColors: pathColorFunction ? pathColorFunction(fullPathForSegment, isCurrent) : null
                                fillColor: customColors ? customColors.fill : (isCurrent ? accentPrimary : pathButtonFill)
                                strokeColor: customColors ? customColors.stroke : (isCurrent ? accentPrimary : pathButtonBorder)
                                textColor: isCurrent ? accentPrimaryText : text
                                textSize: baseFont
                                flatBottomCorners: isCurrent
                                renaming: false
                                renameEnabled: false
                                onActivate: pathSegmentActivated(index)
                                DropArea {
                                    anchors.fill: parent
                                    enabled: allowDrops
                                    onDropped: {
                                        if (!drop || !drop.text) return
                                        var targetPath = fullPathForDisplayIndex(index)
                                        if (!targetPath) return
                                        moveEntryRequested(drop.text, targetPath)
                                        drop.acceptProposedAction()
                                    }
                                }
                            }
                        }

                        // Repeater {
                        //     model: pathPartsDisplay()
                        //     delegate: FolderItem {
                        //         property bool isCurrent: index === (pathPartsDisplay().length - 1)
                        //         label: itemName(modelData)
                        //         style: effectiveStyle()
                        //         compactHeight: compactButtonHeight
                        //         largeHeight: largeButtonHeight
                        //         largePadding: largeButtonPadding
                        //         iconSmall: iconSizeSmall
                        //         iconLarge: iconSizeLarge
                        //         textYOffset: buttonTextYOffset
                        //         iconSource: iconFolder
                        //         fillColor: isCurrent
                        //             ? (tintPathAsProject
                        //                 ? colorWithAlpha(projectTint, cwdOpacity, projectTint)
                        //                 : accentPrimary)
                        //             : (tintPathAsProject
                        //                 ? colorWithAlpha(projectTint, pathProjectOpacity, projectTint)
                        //                 : pathButtonFill)
                        //         strokeColor: isCurrent
                        //             ? (tintPathAsProject
                        //                 ? colorWithAlpha(projectTint, cwdOpacity, projectTintBorder)
                        //                 : accentPrimary)
                        //             : (tintPathAsProject
                        //                 ? colorWithAlpha(projectTint, pathProjectOpacity, projectTintBorder)
                        //                 : pathButtonBorder)
                        //         textColor: isCurrent ? accentPrimaryText : text
                        //         textSize: baseFont
                        //         renaming: false
                        //         renameEnabled: false
                        //         onActivate: pathSegmentActivated(index)
                        //         DropArea {
                        //             anchors.fill: parent
                        //             enabled: allowDrops
                        //             onDropped: {
                        //                 if (!drop || !drop.text) return
                        //                 var targetPath = fullPathForDisplayIndex(index)
                        //                 if (!targetPath) return
                        //                 moveEntryRequested(drop.text, targetPath)
                        //                 drop.acceptProposedAction()
                        //             }
                        //         }
                        //     }
                        // }
                    }
                }
                Item {  // HORIZONTAL: folders row (top line); hidden if wrapped
                    id: topFlowHost
                    Layout.fillWidth: false
                    Layout.preferredWidth: flowOnSecondLine ? 0 : topFoldersRow.implicitWidth
                    Layout.minimumWidth: flowOnSecondLine ? 0 : topFoldersRow.implicitWidth
                    Layout.maximumWidth: flowOnSecondLine ? 0 : topFoldersRow.implicitWidth
                    Layout.preferredHeight: compactButtonHeight
                    Layout.alignment: Qt.AlignTop
                    visible: !flowOnSecondLine
                    onWidthChanged: scheduleLayoutUpdate()
                    Row {
                        id: topFoldersRow
                        spacing: 6
                        onImplicitWidthChanged: scheduleLayoutUpdate()
                        Repeater {
                            model: folders
                            delegate: FolderItem {
                                property string fullPath: itemName(modelData).indexOf("/") === 0
                                    ? itemName(modelData)
                                    : (path + "/" + itemName(modelData))
                                label: itemName(modelData)
                                style: effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                textYOffset: buttonTextYOffset
                                iconSource: iconFolder
                                fillColor: folderFillColor(modelData)
                                strokeColor: folderStrokeColor(modelData)
                                textColor: textSoft
                                textSize: baseFont
                                dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                dragPayload: fullPath
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                tabPinned: root.isPreviewPathActive(0, fullPath)
                                opacity: (root.previewPathForLevel(0).length > 0 && !root.isPreviewPathActive(0, fullPath))
                                    ? root.previewDimOpacity
                                    : 1.0
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                onHoverEntered: {
                                    var center = mapToItem(previewStack, width / 2, height / 2).x
                                    updatePreviewFromHover(0, fullPath, modelData, fillColor, center)
                                }
                                DropArea {
                                    anchors.fill: parent
                                    enabled: allowDrops && !itemIsEmbryo(modelData)
                                    onDropped: {
                                        if (!drop || !drop.text) return
                                        moveEntryRequested(drop.text, fullPath)
                                        drop.acceptProposedAction()
                                    }
                                }
                            }
                        }
                    }
                }
                Item {  // HORIZONTAL: spacer/feder between folders and right buttons
                    Layout.fillWidth: !flowOnSecondLine
                    Layout.preferredWidth: flowOnSecondLine ? 0 : -1
                    Layout.minimumWidth: flowOnSecondLine ? 0 : 0
                    Layout.maximumWidth: flowOnSecondLine ? 0 : -1
                }

                Item {  // HORIZONTAL: right button cluster (search + style + optional theme)
                    id: rightButtonsHost
                    Layout.preferredWidth: rightButtonsRow.implicitWidth
                    Layout.minimumWidth: rightButtonsRow.implicitWidth
                    Layout.maximumWidth: rightButtonsRow.implicitWidth
                    Layout.preferredHeight: compactButtonHeight
                    Layout.alignment: Qt.AlignTop | Qt.AlignRight
                    Row {
                        id: rightButtonsRow
                        anchors.fill: parent
                        spacing: 6
                        Component.onCompleted: scheduleLayoutUpdate()
                        onImplicitWidthChanged: scheduleLayoutUpdate()
                        Rectangle {
                            visible: showSearchToggle && searchActive && !verticalView
                            width: 200
                            height: compactButtonHeight
                            radius: TagChips.CHIP_RADIUS_COMPACT
                            color: card
                            border.color: pillBorder
                            TextField {
                                anchors.fill: parent
                                anchors.margins: 4
                                text: searchText
                                placeholderText: "Search      + deep    # all"
                                font.pixelSize: baseFont
                                selectByMouse: true
                                color: root.text
                                placeholderTextColor: root.textMuted
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 6
                                rightPadding: 6
                                topPadding: 1
                                bottomPadding: 0
                                background: Rectangle { color: "transparent" }
                                onTextChanged: {
                                    root.searchText = text
                                    root.searchTextEdited(text)
                                }
                                onVisibleChanged: {
                                    if (visible && searchActive) {
                                        forceActiveFocus()
                                        selectAll()
                                    }
                                }
                                Keys.onEscapePressed: {
                                    root.searchText = ""
                                    root.searchActive = false
                                }
                            }
                        }
                        Rectangle { // HORIZONTAL: search toggle button (Lupe)
                            visible: showSearchToggle
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: TagChips.CHIP_RADIUS_COMPACT
                            color: pill
                            border.color: pillBorder
                            Image {
                                anchors.centerIn: parent
                                source: iconSearch
                                width: baseFont
                                height: baseFont
                                fillMode: Image.PreserveAspectFit
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: toggleSearch()
                            }
                        }
                        Rectangle { // HORIZONTAL: display options menu (style + embryos)
                            visible: showStyleToggle || showEmbryoToggle
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: TagChips.CHIP_RADIUS_COMPACT
                            color: pill
                            border.color: pillBorder
                            Text {
                                anchors.centerIn: parent
                                text: "\u2630"
                                color: textSoft
                                font.pixelSize: baseFont
                                font.bold: true
                            }
                            Menu {
                                id: horizontalDisplayMenu
                                y: parent ? parent.height + 4 : 0
                                MenuItem {
                                    text: qsTr("t Text")
                                    visible: showStyleToggle
                                    checkable: true
                                    checked: buttonStyle === "text"
                                    onTriggered: styleChanged("text")
                                }
                                MenuItem {
                                    text: qsTr("G Gross")
                                    visible: showStyleToggle && allowLargeIcons
                                    checkable: true
                                    checked: buttonStyle === "largeIcon"
                                    onTriggered: styleChanged("largeIcon")
                                }
                                MenuItem {
                                    text: qsTr("k Klein")
                                    visible: showStyleToggle
                                    checkable: true
                                    checked: buttonStyle === "smallIcon"
                                    onTriggered: styleChanged("smallIcon")
                                }
                                MenuSeparator {
                                    visible: showStyleToggle && showEmbryoToggle
                                }
                                MenuItem {
                                    text: qsTr("E Embryos")
                                    visible: showEmbryoToggle
                                    checkable: true
                                    checked: showEmbryos
                                    onTriggered: toggleEmbryos()
                                }
                                MenuItem {
                                    text: qsTr("Vorschau")
                                    checkable: true
                                    checked: previewEnabled
                                    onTriggered: previewEnabled = !previewEnabled
                                }
                                MenuItem {
                                    text: qsTr("Vorschau Fokus-Hintergrund")
                                    checkable: true
                                    checked: previewFocusBackground
                                    onTriggered: previewFocusBackground = !previewFocusBackground
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: horizontalDisplayMenu.popup()
                            }
                        }
                    }
                }

            }

            RowLayout { // VERTICAL VIEW: main column + right column for buttons
                id: verticalContentRow
                visible: verticalView
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0
                Item {
                    id: verticalMainColumnHost
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    z: 2
                    ColumnLayout { // VERTICAL mainColumn
                        id: verticalMainColumn
                        anchors.fill: parent
                        spacing: 8
                    onImplicitHeightChanged: {
                        scheduleVerticalLayoutUpdate()
                        scheduleContentHeightUpdate()
                    }
                    onChildrenRectChanged: {
                        scheduleVerticalLayoutUpdate()
                        scheduleContentHeightUpdate()
                    }
                    RowLayout { // VERTICAL VIEW: top row (H/V toggle + inline buttons)
                        id: topRowVertical
                        Layout.fillWidth: true
                        Layout.preferredHeight: compactButtonHeight
                        spacing: 6
                        onWidthChanged: scheduleVerticalLayoutUpdate()
                        Rectangle {
                            id: modeToggleButtonVertical
                            visible: showModeToggle
                            width: compactButtonHeight
                            height: compactButtonHeight
                            radius: TagChips.CHIP_RADIUS_COMPACT
                            color: smallButtonBg
                            border.color: smallButtonBorder
                            Layout.alignment: Qt.AlignTop
                            Text {
                                anchors.centerIn: parent
                                text: verticalView ? "H" : "V"
                                color: smallButtonText
                                font.pixelSize: baseFont
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: toggleMode()
                            }
                        }
                        Item { Layout.fillWidth: true } // VERTICAL: spacer/feder between H/V toggle and right buttons
                        Item {
                            id: verticalButtonsSlotTop
                            visible: true
                            Layout.preferredWidth: verticalButtonsPanel.implicitWidth
                            Layout.minimumWidth: verticalButtonsPanel.implicitWidth
                            Layout.maximumWidth: verticalButtonsPanel.implicitWidth
                            Layout.preferredHeight: compactButtonHeight
                            Layout.alignment: Qt.AlignRight | Qt.AlignTop
                        }
                    }
                    Item { // SEARCH FIELD (vertical view)
                        visible: searchActive && verticalView
                        Layout.fillWidth: true
                        Layout.preferredHeight: compactButtonHeight
                        Rectangle {
                            anchors.fill: parent
                            radius: TagChips.CHIP_RADIUS_COMPACT
                            color: card
                            border.color: pillBorder
                            TextField {
                                anchors.fill: parent
                                anchors.margins: 4
                                text: searchText
                                placeholderText: "Search      + deep    # all"
                                font.pixelSize: baseFont
                                selectByMouse: true
                                color: root.text
                                placeholderTextColor: root.textMuted
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 6
                                rightPadding: 6
                                topPadding: 1
                                bottomPadding: 0
                                background: Rectangle { color: "transparent" }
                                onTextChanged: {
                                    root.searchText = text
                                    root.searchTextEdited(text)
                                }
                                onVisibleChanged: {
                                    if (visible && searchActive) {
                                        forceActiveFocus()
                                        selectAll()
                                    }
                                }
                                Keys.onEscapePressed: {
                                    root.searchText = ""
                                    root.searchActive = false
                                }
                            }
                        }
                    }
                    ColumnLayout { // VERTICAL VIEW: section 1 (parent paths)
                        id: verticalColumn
                        Layout.fillWidth: true
                        spacing: verticalParentSpacing

                        Repeater { // PathButtons
                            model: visibleParentPaths()
                            delegate: FolderItem {
                                width: parent.width
                                property string fullPathForSegment: modelData
                                // property var segmentColors: getPathSegmentColor(fullPathForSegment, false)
                                property var customColors: pathColorFunction ? pathColorFunction(fullPathForSegment, false) : null


                                fillColor: customColors ? customColors.fill : pathButtonFill
                                strokeColor: customColors ? customColors.stroke : pathButtonBorder
                                // fillColor: customColors ? customColors.fill : (tintPathAsProject
                                //     ? colorWithAlpha(projectTint, pathProjectOpacity, projectTint)
                                //     : pathButtonFill)

                                // strokeColor: customColors ? customColors.stroke : (tintPathAsProject
                                //     ? colorWithAlpha(projectTint, pathProjectOpacity, projectTintBorder)
                                //     : pathButtonBorder)                  

                                label: itemName(modelData).split("/").filter(function(p){ return p.length > 0 }).slice(-1)[0]
                                style: (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                textYOffset: buttonTextYOffset
                                iconSource: iconFolder
                                textLeftInset: effectiveStyle() === "text" ? 8 : 0
                                // fillColor: segmentColors.fill
                                // strokeColor: segmentColors.stroke
                                textColor: text
                                textSize: baseFont
                                renaming: false
                                renameEnabled: false
                                onActivate: pathSelected(modelData)
                            }
                        }

                        // Repeater { // PathButtons
                        //     model: visibleParentPaths()
                        //     delegate: FolderItem {
                        //         width: parent.width
                        //         label: itemName(modelData).split("/").filter(function(p){ return p.length > 0 }).slice(-1)[0]
                        //         style: (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
                        //         compactHeight: compactButtonHeight
                        //         largeHeight: largeButtonHeight
                        //         largePadding: largeButtonPadding
                        //         iconSmall: iconSizeSmall
                        //         iconLarge: iconSizeLarge
                        //         textYOffset: buttonTextYOffset
                        //         iconSource: iconFolder
                        //         fillColor: tintPathAsProject
                        //             ? colorWithAlpha(projectTint, pathProjectOpacity, projectTint)
                        //             : pathButtonFill
                        //         strokeColor: tintPathAsProject
                        //             ? colorWithAlpha(projectTint, pathProjectOpacity, projectTintBorder)
                        //             : pathButtonBorder
                        //         textColor: text
                        //         textSize: baseFont
                        //         renaming: false
                        //         renameEnabled: false
                        //         onActivate: pathSelected(modelData)
                        //     }
                        // }
                    }
            
                    FolderItem { // VERTICAL VIEW: section 2 (current path highlight)
                        id: cwpButton
                        width: (verticalContentRow ? verticalContentRow.width : parent.width) + root.cwdVerticalRightOverflow
                        z: 8
                        property string currentFullPath: path
                        property var currentPathColors: getPathSegmentColor(currentFullPath, true)
                        
                        label: pathPartsDisplay().length ? pathPartsDisplay()[pathPartsDisplay().length - 1] : "/"
                        style: (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
                        compactHeight: compactButtonHeight
                        largeHeight: largeButtonHeight
                        largePadding: largeButtonPadding
                        iconSmall: iconSizeSmall
                        iconLarge: iconSizeLarge
                        textYOffset: buttonTextYOffset
                        iconSource: iconFolder
                        textLeftInset: effectiveStyle() === "text" ? 8 : 0
                        // fillColor: currentPathColors.fill
                        // Eingesetzt
                        // property string currentFullPath: path
                        property var customColors: pathColorFunction ? pathColorFunction(currentFullPath, true) : null

                        fillColor: customColors ? customColors.fill : accentPrimary
                        strokeColor: customColors ? customColors.stroke : accentPrimary
                        // fillColor: customColors ? customColors.fill : (tintPathAsProject
                        //     ? colorWithAlpha(projectTint, cwdOpacity, projectTint)
                        //     : accentPrimary)

                        // strokeColor: customColors ? customColors.stroke : (tintPathAsProject
                        //     ? colorWithAlpha(projectTint, cwdOpacity, projectTintBorder)
                        //     : accentPrimary)
                        // bis hier
                        // strokeColor: currentPathColors.stroke
                        textColor: accentPrimaryText
                        textSize: baseFont + 1
                        textBold: true
                        flatBottomCorners: true
                        renaming: false
                        renameEnabled: false
                        onActivate: {}
                        DropArea {
                            anchors.fill: parent
                            enabled: allowDrops
                            onDropped: {
                                if (!drop || !drop.text) return
                                moveEntryRequested(drop.text, path)
                                drop.acceptProposedAction()
                            }
                        }
                    }            
                    // Edit
            
                    // FolderItem { // VERTICAL VIEW: section 2 (current path highlight)
                    //     id: cwpButton
                    //     width: parent.width
                    //     label: pathPartsDisplay().length ? pathPartsDisplay()[pathPartsDisplay().length - 1] : "/"
                    //     style: (effectiveStyle() === "largeIcon") ? "smallIcon" : effectiveStyle()
                    //     compactHeight: compactButtonHeight
                    //     largeHeight: largeButtonHeight
                    //     largePadding: largeButtonPadding
                    //     iconSmall: iconSizeSmall
                    //     iconLarge: iconSizeLarge
                    //     textYOffset: buttonTextYOffset
                    //     iconSource: iconFolder
                    //     fillColor: tintPathAsProject
                    //         ? colorWithAlpha(projectTint, cwdOpacity, projectTint)
                    //         : accentPrimary
                    //     strokeColor: tintPathAsProject
                    //         ? colorWithAlpha(projectTint, cwdOpacity, projectTintBorder)
                    //         : accentPrimary
                    //     textColor: accentPrimaryText
                    //     textSize: baseFont + 1
                    //     textBold: true
                    //     renaming: false
                    //     renameEnabled: false
                    //     onActivate: {}
                    //     DropArea {
                    //         anchors.fill: parent
                    //         enabled: allowDrops
                    //         onDropped: {
                    //             if (!drop || !drop.text) return
                    //             moveEntryRequested(drop.text, path)
                    //             drop.acceptProposedAction()
                    //         }
                    //     }
                    // }
                    Flickable { // VERTICAL VIEW: section 3 (folders list, scrollable)
                        id: foldersColumn
                        visible: !foldersInSecondColumn
                        Layout.fillWidth: true
                        Layout.fillHeight: false
                        Layout.preferredHeight: foldersContent.implicitHeight
                        contentWidth: width
                        contentHeight: foldersContent.implicitHeight
                        clip: true
                        Column {
                            id: foldersContent
                            width: parent.width
                            spacing: 6
                            Repeater {
                                model: folders
                                    delegate: FolderItem {
                                        property string fullPath: itemName(modelData).indexOf("/") === 0
                                            ? itemName(modelData)
                                            : (path + "/" + itemName(modelData))
                                    x: indent
                                    width: parent.width - indent
                                    label: itemName(modelData)
                                    style: effectiveStyle()
                                    largeIconAlignLeft: effectiveStyle() !== "largeIcon"
                                    compactHeight: compactButtonHeight
                                    largeHeight: largeButtonHeight
                                    largePadding: largeButtonPadding
                                    iconSmall: iconSizeSmall
                                    iconLarge: iconSizeLarge
                                    textYOffset: buttonTextYOffset
                                    iconSource: iconFolder
                                    fillColor: folderFillColor(modelData)
                                    strokeColor: folderStrokeColor(modelData)
                                    textColor: textSoft
                                    textSize: baseFont
                                        textLeftInset: effectiveStyle() === "text" ? 8 : 0
                                        dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                        dragPayload: fullPath
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                    renameEnabled: allowRename
                                    renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                    onRenameTextEdited: renameTextEdited(text)
                                    onRenameAccepted: renameAccepted()
                                    onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                        DropArea {
                                            anchors.fill: parent
                                            enabled: allowDrops && !itemIsEmbryo(modelData)
                                            onDropped: {
                                                if (!drop || !drop.text) return
                                                moveEntryRequested(drop.text, fullPath)
                                                drop.acceptProposedAction()
                                            }
                                        }
                                }
                            }
                        }
                    }
                    Item {
                        visible: foldersInSecondColumn
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Item { id: verticalSpacer; Layout.fillHeight: true; Layout.minimumHeight: 0 }
                }
                }
                Item {
                    id: verticalRightColumnHost
                    visible: foldersInSecondColumn
                    Layout.preferredWidth: Math.max(verticalButtonsPanel.implicitWidth, verticalRightColumnWidth)
                    Layout.minimumWidth: Math.max(verticalButtonsPanel.implicitWidth, verticalRightColumnWidth)
                    Layout.maximumWidth: Math.max(verticalButtonsPanel.implicitWidth, verticalRightColumnWidth)
                    Layout.fillHeight: true
                    z: 1
                    ColumnLayout { // VERTICAL: right column for folders
                        id: verticalRightColumn
                        anchors.fill: parent
                        spacing: 6
                        Rectangle { // Grey header 
                            Layout.fillWidth: true
                            Layout.preferredHeight: compactButtonHeight
                            border.width: 0
                            color: smallButtonBg
                            radius: 0
                            Rectangle {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                height: 1
                                color: smallButtonBorder
                                opacity: 0.45
                            }
                        }
                        Flickable { // VERTICAL: folders list (right column)
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            contentWidth: width
                            contentHeight: foldersContentRight.height
                            clip: true
                            Column {
                                id: foldersContentRight
                                width: parent.width
                                spacing: 6
                                Repeater {
                                    model: folders
                                    delegate: FolderItem {
                                        property string fullPath: itemName(modelData).indexOf("/") === 0
                                            ? itemName(modelData)
                                            : (path + "/" + itemName(modelData))
                                        x: 0
                                        width: parent.width
                                        label: itemName(modelData)
                                        style: effectiveStyle()
                                        largeIconAlignLeft: effectiveStyle() !== "largeIcon"
                                        compactHeight: compactButtonHeight
                                        largeHeight: largeButtonHeight
                                        largePadding: largeButtonPadding
                                        iconSmall: iconSizeSmall
                                        iconLarge: iconSizeLarge
                                    textYOffset: buttonTextYOffset
                                        iconSource: iconFolder
                                        fillColor: folderFillColor(modelData)
                                        strokeColor: folderStrokeColor(modelData)
                                        textColor: textSoft
                                        textSize: baseFont
                                        textLeftInset: effectiveStyle() === "text" ? 8 : 0
                                        dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                        dragPayload: fullPath
                                        renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                        renameEnabled: allowRename
                                        renameText: renameDraft
                                        onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                        onRenameTextEdited: renameTextEdited(text)
                                        onRenameAccepted: renameAccepted()
                                        onRenameCanceled: renameCanceled()
                                        onActivate: folderActivated(fullPath)
                                        DropArea {
                                            anchors.fill: parent
                                            enabled: allowDrops && !itemIsEmbryo(modelData)
                                            onDropped: {
                                                if (!drop || !drop.text) return
                                                moveEntryRequested(drop.text, fullPath)
                                                drop.acceptProposedAction()
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            RowLayout { // HORIZONTAL VIEW: row 2 (wrapped folders flow)
                id: bottomRow
                visible: !verticalView && flowOnSecondLine
                Layout.fillWidth: true
                spacing: 6
                implicitHeight: bottomFoldersFlow.implicitHeight
                Layout.preferredHeight: flowOnSecondLine ? bottomFoldersFlow.implicitHeight : 0
                Item {
                    id: bottomFlowHost
                    Layout.fillWidth: true
                    Layout.preferredHeight: flowOnSecondLine ? bottomFoldersFlow.implicitHeight : 0
                    Flow {
                        id: bottomFoldersFlow
                        width: bottomFlowHost.width
                        height: implicitHeight
                        spacing: 6
                        flow: Flow.LeftToRight
                        layoutDirection: Qt.LeftToRight
                        Repeater {
                            model: folders
                            delegate: FolderItem {
                                property string fullPath: itemName(modelData).indexOf("/") === 0
                                    ? itemName(modelData)
                                    : (path + "/" + itemName(modelData))
                                label: itemName(modelData)
                                style: effectiveStyle()
                                compactHeight: compactButtonHeight
                                largeHeight: largeButtonHeight
                                largePadding: largeButtonPadding
                                iconSmall: iconSizeSmall
                                iconLarge: iconSizeLarge
                                textYOffset: buttonTextYOffset
                                iconSource: iconFolder
                                fillColor: folderFillColor(modelData)
                                strokeColor: folderStrokeColor(modelData)
                                textColor: textSoft
                                textSize: baseFont
                                dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                dragPayload: fullPath
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                tabPinned: root.isPreviewPathActive(0, fullPath)
                                opacity: (root.previewPathForLevel(0).length > 0 && !root.isPreviewPathActive(0, fullPath))
                                    ? root.previewDimOpacity
                                    : 1.0
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                onHoverEntered: {
                                    var center = mapToItem(previewStack, width / 2, height / 2).x
                                    updatePreviewFromHover(0, fullPath, modelData, fillColor, center)
                                }
                                DropArea {
                                    anchors.fill: parent
                                    enabled: allowDrops && !itemIsEmbryo(modelData)
                                    onDropped: {
                                        if (!drop || !drop.text) return
                                        moveEntryRequested(drop.text, fullPath)
                                        drop.acceptProposedAction()
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Column {
                id: previewStack
                visible: previewEnabled && !verticalView && previewRows.length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: height
                spacing: root.previewRowSpacing
                clip: true
                height: visible ? implicitHeight : 0
                onImplicitHeightChanged: {
                    if (root.previewHeightSyncPending) return
                    root.previewHeightSyncPending = true
                    previewHeightSyncTimer.restart()
                }
                onHeightChanged: {
                    if (root.previewHeightSyncPending) return
                    root.previewHeightSyncPending = true
                    previewHeightSyncTimer.restart()
                }

                Behavior on height {
                    NumberAnimation {
                        duration: previewStack.height < (previewStack.visible ? previewStack.implicitHeight : 0)
                            ? root.previewExpandDurationMs
                            : root.previewCollapseDurationMs
                        easing.type: Easing.OutCubic
                    }
                }

                Repeater {
                    model: previewRows
                    delegate: Rectangle {
                        required property var modelData
                        property int rowIndex: Number(modelData && modelData.level !== undefined ? modelData.level : 0)
                        property string rowParentPath: String(modelData && modelData.parentPath ? modelData.parentPath : "")
                        readonly property bool ancestorRow: rowIndex < Math.max(0, root.previewActivePaths.length - 1)
                        readonly property real rowBgAlpha: (root.previewFocusBackground && ancestorRow) ? 0.0 : 1.0
                        width: parent.width
                        z: 1000 - rowIndex
                        radius: 0
                        readonly property color rowBaseColor: (modelData && modelData.color !== undefined) ? modelData.color : root.panelColor
                        gradient: Gradient {
                            orientation: Gradient.Vertical
                            GradientStop {
                                position: 0.0
                                color: Qt.rgba(rowBaseColor.r, rowBaseColor.g, rowBaseColor.b, rowBgAlpha)
                            }
                            GradientStop {
                                position: 1.0
                                property color mixedRowColor: root.blendColors(rowBaseColor, root.panelColor, root.previewRowShadeMix)
                                color: Qt.rgba(mixedRowColor.r, mixedRowColor.g, mixedRowColor.b, rowBgAlpha)
                            }
                        }
                        border.width: 0
                        implicitHeight: previewFlow.implicitHeight + 2

                        Flow {
                            id: previewFlow
                            property int previewLevel: rowIndex
                            property string basePath: rowParentPath
                            readonly property real anchorCenterX: root.previewAnchorCenterForLevel(previewLevel)
                            readonly property real firstButtonWidth: {
                                var first = previewFlowRepeater.itemAt(0)
                                return first ? first.width : 120
                            }
                            readonly property real desiredStartX: {
                                if (anchorCenterX < 0) return 1
                                var proposed = anchorCenterX - (firstButtonWidth / 2)
                                var maxStart = Math.max(1, parent.width * 0.45)
                                return Math.max(1, Math.min(maxStart, proposed))
                            }
                            x: desiredStartX
                            y: 1
                            width: Math.max(24, parent.width - desiredStartX - 1)
                            height: implicitHeight
                            spacing: 6
                            flow: Flow.LeftToRight
                            layoutDirection: Qt.LeftToRight

                            Repeater {
                                id: previewFlowRepeater
                                model: (modelData && modelData.entries) ? modelData.entries : []
                                delegate: FolderItem {
                                    property string fullPath: root._resolveFullPath(previewFlow.basePath, modelData)
                                    property int previewLevel: previewFlow.previewLevel
                                    label: itemName(modelData)
                                    style: effectiveStyle()
                                    compactHeight: compactButtonHeight
                                    largeHeight: largeButtonHeight
                                    largePadding: largeButtonPadding
                                    iconSmall: iconSizeSmall
                                    iconLarge: iconSizeLarge
                                    textYOffset: buttonTextYOffset
                                    iconSource: iconFolder
                                    fillColor: folderFillColor(modelData)
                                    strokeColor: folderStrokeColor(modelData)
                                    textColor: textSoft
                                    textSize: baseFont
                                    dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                    dragPayload: fullPath
                                    renaming: false
                                    renameEnabled: false
                                    tabHoverDropEnabled: true
                                    tabHoverDropPx: root.previewTabDropPx
                                    tabPinned: root.isPreviewPathActive(previewLevel + 1, fullPath)
                                    opacity: (root.previewPathForLevel(previewLevel + 1).length > 0
                                        && !root.isPreviewPathActive(previewLevel + 1, fullPath))
                                        ? root.previewDimOpacity
                                        : 1.0
                                    onActivate: folderActivated(fullPath)
                                    onHoverEntered: {
                                        var center = mapToItem(previewStack, width / 2, height / 2).x
                                        updatePreviewFromHover(previewLevel + 1, fullPath, modelData, fillColor, center)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
