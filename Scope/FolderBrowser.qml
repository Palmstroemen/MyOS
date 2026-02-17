import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "Theme/tag_chips.js" as TagChips

Item { // ROOT
    id: root
    property string debugName: "FolderBrowser"
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
    property bool debugVerticalWrap: false
    property bool foldersInSecondColumn: false
    property int verticalAutoWidth: 0
    property int verticalColumnWidth: 0
    property int verticalRightColumnWidth: 0
    property int verticalRightColumnWidthHold: 0
    property int verticalRightColumnWidthHoldTarget: 0
    property bool verticalRightFixedWidthEnabled: false
    property int verticalRightFixedWidthPx: 120
    property int verticalRightExpandPxPerSec: 400
    property int verticalRightCollapsePxPerSec: 40
    property int verticalRightWidthTickMs: 16
    property int verticalWidthApplyThresholdPx: 0
    property int verticalGlitchLogThresholdPx: 90
    property bool verticalWidthAnimationEnabled: true
    property bool verticalWidthSpeedBased: true
    property int verticalWidthExpandPxPerSec: 400
    property int verticalWidthCollapsePxPerSec: 40
    property int verticalWidthExpandDurationMs: 150
    property int verticalWidthCollapseDurationMs: 420
    property bool verticalWidthUpdatePending: false
    property int contentHeight: 0
    property bool contentHeightUpdatePending: false
    property bool contentHeightSettlePending: false
    property int cwdTabDrop: 4
    property int cwdVerticalRightOverflow: 10
    property bool previewEnabled: true
    property bool previewFocusBackground: true
    // anchor: current behavior, hybrid: keep anchor but shift left to reduce early wrapping
    property string previewLayoutMode: "hybrid"
    // normal: equal preview column widths, eng: tighter per-column widths
    property string verticalPreviewMode: "normal"
    property var previewRows: []
    property var previewActivePaths: []
    property var previewAnchorCenters: []
    property var previewAnchorCentersY: []
    property real previewDimOpacity: 0.5
    property bool previewDebugBg: false
    property bool previewHoverDebug: false
    property int previewRowSpacing: 1
    property real previewShadeSliderMix: 0.65
    readonly property real previewRowShadeMix: Math.max(0, Math.min(1, 1 - previewShadeSliderMix))
    property int previewExpandDurationMs: 300
    property int previewCollapseDurationMs: 700
    property int contentHeightAnimDurationMs: 110
    property int previewTabDropPx: 4
    property bool previewHeightSyncPending: false
    property string previewLastHoverKey: ""
    property bool previewColumnsHoldActive: false
    property int previewColumnsHoldMs: 160
    property bool previewHoverApplyScheduled: false
    property int previewHoverDelayMs: 90
    property int previewHoverDelayMinLevel: 1
    property int previewHoverPendingGeneration: 0
    property bool previewCloseOnHoverExitEnabled: false
    property int previewCloseDelayMs: 120
    property bool pointerOverMainHoverColumn: false
    property bool pointerOverPreviewColumns: false
    property int previewHoverGen: 0
    property int previewCascadeGuardMs: 140
    property real previewLastApplyAtMs: 0
    property int previewLastApplyLevel: -1
    property int previewPendingLevel: 0
    property string previewPendingPath: ""
    property var previewPendingItem: null
    property var previewPendingFillColor: null
    property real previewPendingCenterX: -1
    property real previewPendingCenterY: -1

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

    function embryoAlphaForPath(level, fullPath) {
        var base = embryoOpacity
        if (isPreviewPathActive(level, fullPath)) {
            return 1.0
        }
        if (isPreviewDimmed(level, fullPath)) {
            return Math.min(base, previewDimOpacity)
        }
        return base
    }

    function folderFillColorForPath(item, level, fullPath) {
        if (itemIsEmbryo(item)) {
            return colorWithAlpha(item.color, embryoAlphaForPath(level, fullPath), projectTint)
        }
        return folderFillColor(item)
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

    function folderStrokeColorForPath(item, level, fullPath) {
        if (itemIsEmbryo(item)) {
            return colorWithAlpha(item.color, embryoAlphaForPath(level, fullPath), projectTintBorder)
        }
        return folderStrokeColor(item)
    }

    function currentRowHeight() {
        return effectiveStyle() === "largeIcon" ? largeButtonHeight : compactButtonHeight
    }

    function shouldShowVerticalRightColumn() {
        return foldersInSecondColumn || (previewEnabled && verticalView && (previewRows.length > 0 || previewColumnsHoldActive))
    }

    function calculateFoldersColumnWidthForEntries(entries) {
        if (!entries || entries.length === 0) {
            return verticalMinWidth
        }
        var maxWidth = 0
        var folderStyle = effectiveStyle()
        for (var f = 0; f < entries.length; f++) {
            maxWidth = Math.max(maxWidth, estimateButtonWidth(itemName(entries[f]), folderStyle))
        }
        var padded = maxWidth + 32
        return Math.max(verticalMinWidth, padded)
    }

    function calculateVerticalAutoWidth() {
        if (!verticalView) return verticalPreferredWidth > 0 ? verticalPreferredWidth : verticalMinWidth
        var showRightColumn = shouldShowVerticalRightColumn()
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
        for (var f = 0; f < folders.length; f++) {
            maxWidth = Math.max(maxWidth, estimateButtonWidth(itemName(folders[f]), folderStyle))
        }
        var buttonsWidth = (showModeToggle ? compactButtonHeight + 6 : 0) + verticalButtonsPanel.implicitWidth
        maxWidth = Math.max(maxWidth, buttonsWidth + 12)
        var padded = maxWidth + 32
        var columnWidth = Math.min(verticalMaxWidth, Math.max(verticalMinWidth, padded))
        var rightWidth = calculateFoldersColumnWidth()
        verticalColumnWidth = columnWidth
        verticalRightColumnWidth = rightWidth
        var gap = showRightColumn ? (verticalContentRow ? verticalContentRow.spacing : 12) : 0
        // A (test toggle): hard width reduction disabled.
        var total = columnWidth + (showRightColumn ? rightWidth : 0) + gap
        if (debugVerticalWrap) {
            console.log(
                "[vwidth:auto]",
                "name=", debugName,
                "path=", path,
                "previewRows=", previewRows.length,
                "showRight=", showRightColumn,
                "foldersInSecondColumn=", foldersInSecondColumn,
                "maxWidth=", Math.round(maxWidth),
                "column=", Math.round(columnWidth),
                "right=", Math.round(rightWidth),
                "gap=", Math.round(gap),
                "total=", Math.round(total)
            )
        }
        return total
    }

    function calculateFoldersColumnWidth() {
        if (verticalView && verticalRightFixedWidthEnabled) {
            var fixed = Math.max(verticalMinWidth, Math.round(Number(verticalRightFixedWidthPx) || verticalMinWidth))
            _setVerticalRightHoldTarget(fixed)
            return fixed
        }
        if (previewEnabled && verticalView && previewRows.length > 0) {
            var previewCount = previewRows.length
            var maxPreviewWidth = verticalMinWidth
            var perRow = []
            var sumPreviewWidths = 0
            for (var i = 0; i < previewCount; i++) {
                var row = previewRows[i]
                var rowEntries = (row && row.entries) ? row.entries : []
                var rowWidth = calculateFoldersColumnWidthForEntries(rowEntries)
                perRow.push(Math.round(rowWidth))
                maxPreviewWidth = Math.max(maxPreviewWidth, rowWidth)
                sumPreviewWidths += rowWidth
            }
            var spacingPerGap = 6
            var spacing = previewCount > 1 ? ((previewCount - 1) * spacingPerGap) : 0
            var previewTotal = Math.max(verticalMinWidth, (maxPreviewWidth * previewCount) + spacing)
            if (debugVerticalWrap) {
                console.log(
                    "[vwidth:right-preview]",
                    "name=", debugName,
                    "mode=", verticalPreviewMode,
                    "rows=", previewCount,
                    "perRow=", "[" + perRow.join(",") + "]",
                    "maxRow=", Math.round(maxPreviewWidth),
                    "spacing=", Math.round(spacing),
                    "total=", Math.round(previewTotal)
                )
            }
            if (verticalView && previewEnabled) {
                _setVerticalRightHoldTarget(previewTotal)
                var hold = Math.max(verticalMinWidth, Number(verticalRightColumnWidthHold) || 0)
                return hold > 0 ? hold : previewTotal
            }
            return previewTotal
        }
        var fallback = calculateFoldersColumnWidthForEntries(folders || [])
        if (debugVerticalWrap) {
            console.log(
                "[vwidth:right-fallback]",
                "name=", debugName,
                "folders=", (folders ? folders.length : 0),
                "total=", Math.round(fallback)
            )
        }
        if (verticalView && previewEnabled) {
            _setVerticalRightHoldTarget(fallback)
            var fallbackHold = Math.max(verticalMinWidth, Number(verticalRightColumnWidthHold) || 0)
            return fallbackHold > 0 ? fallbackHold : fallback
        }
        return fallback
    }

    function _setVerticalRightHoldTarget(nextWidth) {
        var target = Math.max(verticalMinWidth, Math.round(Number(nextWidth) || 0))
        verticalRightColumnWidthHoldTarget = target
        if (!verticalRightWidthSmoother.running) {
            verticalRightWidthSmoother.start()
        }
    }

    function _tickVerticalRightHoldWidth() {
        var current = Math.max(0, Number(verticalRightColumnWidthHold) || 0)
        var target = Math.max(0, Number(verticalRightColumnWidthHoldTarget) || 0)
        var dt = Math.max(0.001, Number(verticalRightWidthTickMs) / 1000.0)
        var speed = target >= current ? Math.max(1, verticalRightExpandPxPerSec) : Math.max(1, verticalRightCollapsePxPerSec)
        var step = speed * dt
        var next = current
        if (target > current) {
            next = Math.min(target, current + step)
        } else if (target < current) {
            next = Math.max(target, current - step)
        }
        if (Math.abs(next - current) >= 0.5) {
            verticalRightColumnWidthHold = Math.round(next)
            scheduleVerticalWidthUpdate()
            return
        }
        if (Math.abs(target - current) >= 0.5) {
            verticalRightColumnWidthHold = Math.round(target)
            scheduleVerticalWidthUpdate()
        }
        verticalRightWidthSmoother.stop()
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

    function isPreviewDimmed(level, fullPath) {
        if (!previewActivePaths || previewActivePaths.length === 0) {
            return false
        }
        var deepestActiveLevel = -1
        for (var i = 0; i < previewActivePaths.length; i++) {
            if (String(previewActivePaths[i] || "").length > 0) {
                deepestActiveLevel = i
            }
        }
        // Only dim in the row directly above the currently active row.
        var dimLevel = deepestActiveLevel - 1
        if (dimLevel < 0 || level !== dimLevel) {
            return false
        }
        var activePath = previewPathForLevel(level)
        if (activePath.length === 0) {
            return false
        }
        // In that previous row: keep selected path clear, dim all others.
        return !isPreviewPathActive(level, fullPath)
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
    onVerticalPreviewModeChanged: {
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
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
    }
    onPreviewRowsChanged: {
        if (previewEnabled && verticalView) {
            if (previewRows.length > 0) {
                previewColumnsHoldActive = false
                previewColumnsHoldTimer.stop()
            } else {
                previewColumnsHoldActive = true
                previewColumnsHoldTimer.restart()
            }
        } else {
            previewColumnsHoldActive = false
            previewColumnsHoldTimer.stop()
        }
        scheduleVerticalWidthUpdate()
        scheduleContentHeightUpdate()
        if (verticalRightColumnHost && verticalRightColumnHost.schedulePreviewLayoutLog) {
            verticalRightColumnHost.schedulePreviewLayoutLog("preview-rows")
        }
        _debugPreviewBgState("rowsChanged")
    }
    onPreviewAnchorCentersChanged: {
        if (verticalRightColumnHost && verticalRightColumnHost.schedulePreviewLayoutLog) {
            verticalRightColumnHost.schedulePreviewLayoutLog("anchor-x")
        }
    }
    onPreviewAnchorCentersYChanged: {
        if (verticalRightColumnHost && verticalRightColumnHost.schedulePreviewLayoutLog) {
            verticalRightColumnHost.schedulePreviewLayoutLog("anchor-y")
        }
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

    Timer {
        id: previewColumnsHoldTimer
        interval: root.previewColumnsHoldMs
        repeat: false
        onTriggered: {
            root.previewColumnsHoldActive = false
            root.scheduleVerticalWidthUpdate()
            root.scheduleContentHeightUpdate()
        }
    }

    Timer {
        id: previewHoverDelayTimer
        interval: root.previewHoverDelayMs
        repeat: false
        onTriggered: root._applyQueuedPreviewHover(root.previewHoverPendingGeneration)
    }

    Timer {
        id: previewCloseTimer
        interval: root.previewCloseDelayMs
        repeat: false
        onTriggered: {
            if (!root.previewCloseOnHoverExitEnabled) return
            if (!root.verticalView || !root.previewEnabled) return
            if (root._keepPreviewAlive()) return
            root.resetPreview()
            root.scheduleVerticalWidthUpdate()
            root.scheduleContentHeightUpdate()
        }
    }

    Timer {
        id: verticalRightWidthSmoother
        interval: Math.max(8, root.verticalRightWidthTickMs)
        repeat: true
        onTriggered: root._tickVerticalRightHoldWidth()
    }

    NumberAnimation {
        id: verticalWidthAnim
        target: root
        property: "verticalPreferredWidth"
        easing.type: Easing.OutCubic
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
        previewAnchorCentersY = []
        previewLastHoverKey = ""
        previewColumnsHoldActive = false
        previewColumnsHoldTimer.stop()
        verticalRightColumnWidthHold = 0
        verticalRightColumnWidthHoldTarget = 0
        verticalRightWidthSmoother.stop()
        previewHoverGen += 1
        previewHoverApplyScheduled = false
        previewHoverPendingGeneration = 0
        previewHoverDelayTimer.stop()
        previewPendingLevel = 0
        previewPendingPath = ""
        previewPendingItem = null
        previewPendingFillColor = null
        previewPendingCenterX = -1
        previewPendingCenterY = -1
    }

    function _keepPreviewAlive() {
        return pointerOverMainHoverColumn || pointerOverPreviewColumns
    }

    function _schedulePreviewCloseIfIdle() {
        if (!previewCloseOnHoverExitEnabled) return
        if (!verticalView || !previewEnabled) return
        if (_keepPreviewAlive()) {
            previewCloseTimer.stop()
            return
        }
        previewCloseTimer.restart()
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

    function _setPreviewAnchorCenter(level, centerX, centerY) {
        var x = Number(centerX)
        if (!isFinite(x)) {
            return
        }
        var nextCenters = previewAnchorCenters.slice(0, level)
        nextCenters.push(x)
        var y = Number(centerY)
        var hasY = isFinite(y)
        var nextCentersY = previewAnchorCentersY.slice(0, level)
        if (hasY) {
            nextCentersY.push(y)
        } else if (previewAnchorCentersY && level < previewAnchorCentersY.length) {
            nextCentersY.push(previewAnchorCentersY[level])
        }
        var changedX = !_samePathArray(previewAnchorCenters, nextCenters)
        var changedY = !_samePathArray(previewAnchorCentersY, nextCentersY)
        if (!changedX && !changedY) {
            return
        }
        previewAnchorCenters = nextCenters
        previewAnchorCentersY = nextCentersY
    }

    function previewAnchorCenterForLevel(level) {
        if (!previewAnchorCenters || level < 0 || level >= previewAnchorCenters.length) {
            return -1
        }
        var x = Number(previewAnchorCenters[level])
        return isFinite(x) ? x : -1
    }

    function previewAnchorCenterYForLevel(level) {
        if (!previewAnchorCentersY || level < 0 || level >= previewAnchorCentersY.length) {
            return -1
        }
        var y = Number(previewAnchorCentersY[level])
        return isFinite(y) ? y : -1
    }

    function _applyPreviewHover(level, basePath, sourceItem, sourceFillColor) {
        var hoverKey = String(level) + "|" + basePath + "|" + String(sourceFillColor)
        if (hoverKey === previewLastHoverKey) {
            if (previewHoverDebug) {
                console.log("[preview-hover] skip-same", "level=", level, "path=", basePath)
            }
            return
        }
        previewLastHoverKey = hoverKey
        var children = listPreviewChildren(basePath)
        if (previewHoverDebug) {
            console.log("[preview-hover] apply", "level=", level, "path=", basePath, "children=", children.length)
        }
        var nextRows = previewRows.slice(0, level)
        // Collapse deeper rows when the currently hovered item has no children.
        // Vertical rule: do not keep/open an empty next column.
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

    function _applyQueuedPreviewHover(generation) {
        previewHoverApplyScheduled = false
        if (generation !== previewHoverGen) {
            return
        }
        if (!previewEnabled) {
            return
        }
        var queuedLevel = Math.max(0, Number(previewPendingLevel) || 0)
        var queuedPath = String(previewPendingPath || "").trim()
        if (!queuedPath) {
            return
        }
        if (previewHoverDebug) {
            console.log("[preview-hover] queued-apply", "level=", queuedLevel, "path=", queuedPath)
        }
        _setPreviewActivePath(queuedLevel, queuedPath)
        _setPreviewAnchorCenter(queuedLevel, previewPendingCenterX, previewPendingCenterY)
        _debugPreviewBgState("hoverBeforeApply")
        _applyPreviewHover(queuedLevel, queuedPath, previewPendingItem, previewPendingFillColor)
        _debugPreviewBgState("hoverAfterApply")
        previewLastApplyAtMs = Date.now()
        previewLastApplyLevel = queuedLevel
    }

    function _queuePreviewHover(level, basePath, sourceItem, sourceFillColor, sourceCenterX, sourceCenterY) {
        if (previewHoverApplyScheduled) {
            var pendingLevel = Math.max(0, Number(previewPendingLevel) || 0)
            // When overlapping hover events happen in the same frame,
            // keep the deeper level event to avoid collapse flicker.
            if (level < pendingLevel) {
                if (previewHoverDebug) {
                    console.log("[preview-hover] queue-skip-shallower", "level=", level, "pending=", pendingLevel, "path=", basePath)
                }
                return
            }
        }
        previewPendingLevel = level
        previewPendingPath = basePath
        previewPendingItem = sourceItem
        previewPendingFillColor = sourceFillColor
        previewPendingCenterX = sourceCenterX
        previewPendingCenterY = sourceCenterY
        if (previewHoverDebug) {
            console.log("[preview-hover] queue", "level=", level, "path=", basePath, "centerX=", sourceCenterX)
        }
        if (previewHoverApplyScheduled) {
            return
        }
        previewHoverApplyScheduled = true
        var generation = previewHoverGen
        var needsDelay = verticalView && level >= previewHoverDelayMinLevel && previewHoverDelayMs > 0
        if (needsDelay) {
            previewHoverPendingGeneration = generation
            previewHoverDelayTimer.interval = previewHoverDelayMs
            previewHoverDelayTimer.restart()
            return
        }
        Qt.callLater(function() { _applyQueuedPreviewHover(generation) })
    }

    function updatePreviewFromHover(sourceLevel, sourcePath, sourceItem, sourceFillColor, sourceCenterX, sourceCenterY) {
        if (!previewEnabled) {
            return
        }
        var level = Math.max(0, Number(sourceLevel) || 0)
        var basePath = String(sourcePath || "").trim()
        if (!basePath) {
            return
        }
        if (verticalView && level < Math.max(0, previewActivePaths.length - 1)) {
            // Ignore stale re-hover on already-selected higher level.
            // This avoids collapsing deeper columns when pointer overlaps.
            if (basePath === previewPathForLevel(level)) {
                if (previewHoverDebug) {
                    console.log("[preview-hover] skip-stale-upper", "level=", level, "path=", basePath)
                }
                return
            }
        }
        if (previewHoverDebug) {
            console.log("[preview-hover] enter", "vertical=", verticalView, "level=", level, "path=", basePath)
        }
        if (verticalView) {
            var nowMs = Date.now()
            var elapsed = nowMs - Number(previewLastApplyAtMs || 0)
            if (level >= 2 && level > previewLastApplyLevel && elapsed >= 0 && elapsed < previewCascadeGuardMs) {
                if (previewHoverDebug) {
                    console.log("[preview-hover] skip-cascade", "level=", level, "lastLevel=", previewLastApplyLevel, "elapsed=", Math.round(elapsed))
                }
                return
            }
            _queuePreviewHover(level, basePath, sourceItem, sourceFillColor, sourceCenterX, sourceCenterY)
            return
        }
        // Keep tab feedback immediate even while row animations run.
        _setPreviewActivePath(level, basePath)
        _setPreviewAnchorCenter(level, sourceCenterX, sourceCenterY)
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
            var previous = verticalAutoWidth
            var nextWidth = calculateVerticalAutoWidth()
            var delta = Math.abs(nextWidth - previous)
            if (delta >= verticalWidthApplyThresholdPx) {
                verticalAutoWidth = nextWidth
                _applyVerticalPreferredWidth(nextWidth)
            } else if (debugVerticalWrap) {
                console.log(
                    "[vwidth:skip-small]",
                    "name=", debugName,
                    "prev=", Math.round(previous),
                    "next=", Math.round(nextWidth),
                    "delta=", Math.round(delta),
                    "threshold=", verticalWidthApplyThresholdPx
                )
            }
            if (delta >= verticalGlitchLogThresholdPx) {
                console.log(
                    "[vwidth:glitch-candidate]",
                    "name=", debugName,
                    "prev=", Math.round(previous),
                    "next=", Math.round(nextWidth),
                    "delta=", Math.round(delta),
                    "rows=", previewRows.length,
                    "mode=", verticalPreviewMode,
                    "showRight=", shouldShowVerticalRightColumn()
                )
            }
            if (debugVerticalWrap) {
                console.log("[vwidth:apply]", "name=", debugName, "prev=", Math.round(previous), "next=", Math.round(verticalAutoWidth))
            }
            verticalWidthUpdatePending = false
        })
    }

    function _applyVerticalPreferredWidth(nextWidth) {
        var target = Math.max(0, Math.round(Number(nextWidth) || 0))
        if (!verticalWidthAnimationEnabled || !verticalView) {
            verticalPreferredWidth = target
            return
        }
        var current = Math.max(0, Math.round(Number(verticalPreferredWidth) || 0))
        if (current <= 0 || Math.abs(target - current) < 1) {
            verticalPreferredWidth = target
            return
        }
        verticalWidthAnim.stop()
        if (verticalWidthSpeedBased) {
            var delta = Math.abs(target - current)
            if (target > current) {
                var expandSpeed = Math.max(1, Number(verticalWidthExpandPxPerSec) || 1)
                verticalWidthAnim.duration = Math.max(80, Math.round((delta / expandSpeed) * 1000))
            } else {
                var collapseSpeed = Math.max(1, Number(verticalWidthCollapsePxPerSec) || 1)
                verticalWidthAnim.duration = Math.max(120, Math.round((delta / collapseSpeed) * 1000))
            }
        } else {
            verticalWidthAnim.duration = target > current
                ? verticalWidthExpandDurationMs
                : verticalWidthCollapseDurationMs
        }
        verticalWidthAnim.from = current
        verticalWidthAnim.to = target
        verticalWidthAnim.start()
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
        var showRightColumn = shouldShowVerticalRightColumn()
        var freeHeight          = verticalSpacer ? verticalSpacer.height : 0
        var uListHeight         = verticalRightPreviewColumns ? verticalRightPreviewColumns.implicitHeight : 0
        var shouldWrap          = showRightColumn
            ? false
            : (foldersInSecondColumn
                ? (freeHeight*2 <= uListHeight + 10)
                : (freeHeight < 1))
        if (debugVerticalWrap) {
            console.log(
                "[vwidth:wrap-check]",
                "name=", debugName,
                "path=", path,
                "showRight=", showRightColumn,
                "freeHeight=", Math.round(freeHeight),
                "uListHeight=", Math.round(uListHeight),
                "currentWrap=", foldersInSecondColumn,
                "nextWrap=", shouldWrap
            )
        }
        if (verticalButtonsOnSecondLine !== shouldWrap) {
            verticalButtonsOnSecondLine = shouldWrap
            foldersInSecondColumn = shouldWrap
            if (debugVerticalWrap) {
                console.log("[vwidth:wrap-apply]", "set=", shouldWrap)
            }
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
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Vorschau Layout: Anchor")
                            checkable: true
                            checked: previewLayoutMode === "anchor"
                            onTriggered: previewLayoutMode = "anchor"
                        }
                        MenuItem {
                            text: qsTr("Vorschau Layout: Hybrid")
                            checkable: true
                            checked: previewLayoutMode === "hybrid"
                            onTriggered: previewLayoutMode = "hybrid"
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("V-Vorschau: Normal")
                            checkable: true
                            checked: true
                            enabled: false
                            onTriggered: {}
                        }
                        MenuItem {
                            text: qsTr("V-Vorschau: Eng")
                            checkable: true
                            checked: false
                            enabled: false
                            onTriggered: {}
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
                                dimmedStyle: isCurrent
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
                                fillColor: folderFillColorForPath(modelData, 0, fullPath)
                                strokeColor: folderStrokeColorForPath(modelData, 0, fullPath)
                                textColor: textSoft
                                textSize: baseFont
                                dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                dragPayload: fullPath
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                tabPinned: root.isPreviewPathActive(0, fullPath)
                                textBold: root.isPreviewPathActive(0, fullPath)
                                dimmedStyle: root.isPreviewDimmed(0, fullPath)
                                opacity: root.isPreviewDimmed(0, fullPath) ? root.previewDimOpacity : 1.0
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                onHoverEntered: {
                                    var centerPoint = mapToItem(root, width / 2, height / 2)
                                    updatePreviewFromHover(0, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
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
                                MenuSeparator {}
                                MenuItem {
                                    text: qsTr("Vorschau Layout: Anchor")
                                    checkable: true
                                    checked: previewLayoutMode === "anchor"
                                    onTriggered: previewLayoutMode = "anchor"
                                }
                                MenuItem {
                                    text: qsTr("Vorschau Layout: Hybrid")
                                    checkable: true
                                    checked: previewLayoutMode === "hybrid"
                                    onTriggered: previewLayoutMode = "hybrid"
                                }
                                MenuSeparator {}
                                MenuItem {
                                    text: qsTr("V-Vorschau: Normal")
                                    checkable: true
                                    checked: verticalPreviewMode === "normal"
                                    onTriggered: verticalPreviewMode = "normal"
                                }
                                MenuItem {
                                    text: qsTr("V-Vorschau: Eng")
                                    checkable: true
                                    checked: verticalPreviewMode === "eng"
                                    onTriggered: verticalPreviewMode = "eng"
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
                    Layout.fillWidth: false
                    Layout.preferredWidth: Math.max(verticalMinWidth, verticalColumnWidth)
                    Layout.minimumWidth: Math.max(verticalMinWidth, verticalColumnWidth)
                    Layout.maximumWidth: Math.max(verticalMinWidth, verticalColumnWidth)
                    Layout.fillHeight: true
                    clip: true
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
                        width: parent.width + root.cwdVerticalRightOverflow
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
                        dimmedStyle: true
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
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.NoButton
                            hoverEnabled: true
                            onEntered: {
                                root.pointerOverMainHoverColumn = true
                                previewCloseTimer.stop()
                            }
                            onExited: {
                                root.pointerOverMainHoverColumn = false
                                root._schedulePreviewCloseIfIdle()
                            }
                        }
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
                                    fillColor: folderFillColorForPath(modelData, 0, fullPath)
                                    strokeColor: folderStrokeColorForPath(modelData, 0, fullPath)
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
                                onHoverEntered: {
                                    if (!verticalView) {
                                        return
                                    }
                                    var centerPoint = mapToItem(root, width / 2, height / 2)
                                    updatePreviewFromHover(0, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
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
                    Item {
                        visible: shouldShowVerticalRightColumn()
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Item { id: verticalSpacer; Layout.fillHeight: true; Layout.minimumHeight: 0 }
                }
                }
                Item {
                    id: verticalRightColumnHost
                    visible: shouldShowVerticalRightColumn()
                    property bool debugColumnLayout: (debugVerticalWrap || debugLayout)
                    property bool previewLayoutLogPending: false
                    readonly property bool hasPreviewColumns: previewEnabled && verticalView && previewRows.length > 0
                    readonly property int previewColumnCount: hasPreviewColumns ? previewRows.length : 1
                    readonly property real previewColumnsSpacing: 6
                    readonly property real previewHostTargetWidth: Math.max(verticalMinWidth, verticalRightColumnWidth)
                    readonly property real previewColumnsContentWidth: 0
                    readonly property real previewColumnWidth: Math.max(
                        verticalMinWidth,
                        (previewHostTargetWidth - ((previewColumnCount - 1) * previewColumnsSpacing)) / Math.max(1, previewColumnCount)
                    )
                    function previewColumnsStartX() {
                        // Stabilized for now: keep preview block pinned directly
                        // to the right of the main column.
                        return 0
                    }
                    function previewAnchorYForColumn(columnIndex) { return -1 }
                    function previewColumnStartY(columnIndex, contentHeight, hostHeight) { return 0 }
                    function schedulePreviewLayoutLog(reason) {
                        if (!debugColumnLayout || previewLayoutLogPending) {
                            return
                        }
                        previewLayoutLogPending = true
                        Qt.callLater(function() {
                            previewLayoutLogPending = false
                            if (!debugColumnLayout || !visible) {
                                return
                            }
                            var startX = previewColumnsStartX()
                            var hostRight = width
                            var parts = []
                            var cursor = startX
                            for (var i = 0; i < previewColumnCount; i++) {
                                var w = Math.round(previewColumnTargetWidth(i))
                                parts.push("c" + i + "=[" + Math.round(cursor) + ".." + Math.round(cursor + w) + "]")
                                cursor += w + (i < previewColumnCount - 1 ? previewColumnsSpacing : 0)
                            }
                            console.log(
                                "[vcols:layout]",
                                "reason=", String(reason || ""),
                                "hostX=", Math.round(x),
                                "hostW=", Math.round(width),
                                "startX=", Math.round(startX),
                                "contentW=", Math.round(previewColumnsContentWidth),
                                "right=", Math.round(hostRight),
                                "anchorX0=", Math.round(root.previewAnchorCenterForLevel(0)),
                                "anchorY0=", Math.round(root.previewAnchorCenterYForLevel(0)),
                                "rows=", previewRows.length,
                                "cols=", previewColumnCount,
                                parts.join(" ")
                            )
                        })
                    }
                    onXChanged: schedulePreviewLayoutLog("host-x")
                    onWidthChanged: schedulePreviewLayoutLog("host-width")
                    onVisibleChanged: {
                        schedulePreviewLayoutLog("host-visible")
                        if (!visible) {
                            root.pointerOverPreviewColumns = false
                            root._schedulePreviewCloseIfIdle()
                        }
                    }
                    onPreviewColumnsContentWidthChanged: {}
                    onPreviewColumnCountChanged: schedulePreviewLayoutLog("column-count")
                    function previewColumnTargetWidth(columnIndex) {
                        return previewColumnWidth
                    }
                    function previewRowAt(columnIndex) {
                        if (!hasPreviewColumns) {
                            return null
                        }
                        if (columnIndex < 0 || columnIndex >= previewRows.length) {
                            return null
                        }
                        return previewRows[columnIndex]
                    }
                    function previewEntriesAt(columnIndex) {
                        var row = previewRowAt(columnIndex)
                        if (row && row.entries) {
                            return row.entries
                        }
                        return columnIndex === 0 ? folders : []
                    }
                    function previewLevelAt(columnIndex) {
                        var row = previewRowAt(columnIndex)
                        if (row && row.level !== undefined) {
                            return Number(row.level) + 1
                        }
                        return 0
                    }
                    function previewBasePathAt(columnIndex) {
                        var row = previewRowAt(columnIndex)
                        if (row && row.parentPath !== undefined) {
                            return String(row.parentPath || "")
                        }
                        return String(path || "")
                    }
                    Layout.preferredWidth: Math.max(
                        verticalButtonsPanel.implicitWidth,
                        root.verticalRightFixedWidthEnabled ? root.verticalRightFixedWidthPx : verticalRightColumnWidth
                    )
                    Layout.minimumWidth: Math.max(
                        verticalButtonsPanel.implicitWidth,
                        root.verticalRightFixedWidthEnabled ? root.verticalRightFixedWidthPx : verticalRightColumnWidth
                    )
                    Layout.maximumWidth: Math.max(
                        verticalButtonsPanel.implicitWidth,
                        root.verticalRightFixedWidthEnabled ? root.verticalRightFixedWidthPx : verticalRightColumnWidth
                    )
                    Layout.fillHeight: true
                    z: 1
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        onEntered: {
                            root.pointerOverPreviewColumns = true
                            previewCloseTimer.stop()
                        }
                        onExited: {
                            root.pointerOverPreviewColumns = false
                            root._schedulePreviewCloseIfIdle()
                        }
                    }
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
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            Row {
                                id: verticalRightPreviewColumns
                                x: verticalRightColumnHost.previewColumnsStartX()
                                onXChanged: verticalRightColumnHost.schedulePreviewLayoutLog("row-x")
                                width: implicitWidth
                                height: parent.height
                                spacing: verticalRightColumnHost.previewColumnsSpacing
                                Repeater {
                                    model: verticalRightColumnHost.previewColumnCount
                                    delegate: Flickable {
                                        id: rightColumnFlick
                                        property int columnIndex: index
                                        width: verticalRightColumnHost.previewColumnTargetWidth(rightColumnFlick.columnIndex)
                                        height: parent.height
                                        contentWidth: width
                                        contentHeight: rightColumnContent.implicitHeight
                                        clip: true
                                        Column {
                                            id: rightColumnContent
                                            y: 0
                                            width: parent.width
                                            spacing: 6
                                            Repeater {
                                                model: verticalRightColumnHost.previewEntriesAt(rightColumnFlick.columnIndex)
                                                delegate: FolderItem {
                                                    property int previewLevel: verticalRightColumnHost.previewLevelAt(rightColumnFlick.columnIndex)
                                                    property string previewBasePath: verticalRightColumnHost.previewBasePathAt(rightColumnFlick.columnIndex)
                                                    property string fullPath: itemName(modelData).indexOf("/") === 0
                                                        ? itemName(modelData)
                                                        : root._resolveFullPath(previewBasePath, modelData)
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
                                                    fillColor: folderFillColorForPath(modelData, previewLevel, fullPath)
                                                    strokeColor: folderStrokeColorForPath(modelData, previewLevel, fullPath)
                                                    textColor: textSoft
                                                    textSize: baseFont
                                                    textLeftInset: effectiveStyle() === "text" ? 8 : 0
                                                    tabHoverDropEnabled: true
                                                    tabHoverDropPx: root.previewTabDropPx
                                                    tabPinned: root.isPreviewPathActive(previewLevel, fullPath)
                                                    textBold: root.isPreviewPathActive(previewLevel, fullPath)
                                                    dimmedStyle: root.isPreviewDimmed(previewLevel, fullPath)
                                                    opacity: root.isPreviewDimmed(previewLevel, fullPath) ? root.previewDimOpacity : 1.0
                                                    dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                                    dragPayload: fullPath
                                                    renaming: allowRename && renameTargetPath === fullPath
                                                    renameEnabled: allowRename
                                                    renameText: renameDraft
                                                    onRenameRequested: renameRequested(fullPath)
                                                    onRenameTextEdited: renameTextEdited(text)
                                                    onRenameAccepted: renameAccepted()
                                                    onRenameCanceled: renameCanceled()
                                                    onActivate: folderActivated(fullPath)
                                                    onHoverEntered: {
                                                        if (!verticalView) {
                                                            return
                                                        }
                                                        var centerPoint = mapToItem(root, width / 2, height / 2)
                                                        updatePreviewFromHover(previewLevel, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
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
                                fillColor: folderFillColorForPath(modelData, 0, fullPath)
                                strokeColor: folderStrokeColorForPath(modelData, 0, fullPath)
                                textColor: textSoft
                                textSize: baseFont
                                dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                dragPayload: fullPath
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                tabPinned: root.isPreviewPathActive(0, fullPath)
                                textBold: root.isPreviewPathActive(0, fullPath)
                                dimmedStyle: root.isPreviewDimmed(0, fullPath)
                                opacity: root.isPreviewDimmed(0, fullPath) ? root.previewDimOpacity : 1.0
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                onHoverEntered: {
                                    var centerPoint = mapToItem(root, width / 2, height / 2)
                                    updatePreviewFromHover(0, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
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
                            readonly property real contentWidthEstimate: {
                                var count = previewFlowRepeater.count
                                if (count <= 0) {
                                    return 0
                                }
                                var total = 0
                                for (var i = 0; i < count; i++) {
                                    var button = previewFlowRepeater.itemAt(i)
                                    total += button ? button.width : 120
                                    if (i > 0) {
                                        total += previewFlow.spacing
                                    }
                                }
                                return total
                            }
                            readonly property real anchorStartX: {
                                if (anchorCenterX < 0) return 1
                                var proposed = anchorCenterX - (firstButtonWidth / 2)
                                var maxStart = Math.max(1, parent.width * 0.45)
                                return Math.max(1, Math.min(maxStart, proposed))
                            }
                            readonly property real maxStartForSingleRow: {
                                // Left-shift just enough to keep as many items as possible in the current row.
                                return Math.max(1, parent.width - contentWidthEstimate - 1)
                            }
                            readonly property real desiredStartX: {
                                if (root.previewLayoutMode === "anchor") {
                                    return anchorStartX
                                }
                                // hybrid (default): keep anchor feel, but shift left to avoid premature wrapping.
                                return Math.max(1, Math.min(anchorStartX, maxStartForSingleRow))
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
                                    fillColor: folderFillColorForPath(modelData, previewLevel + 1, fullPath)
                                    strokeColor: folderStrokeColorForPath(modelData, previewLevel + 1, fullPath)
                                    textColor: textSoft
                                    textSize: baseFont
                                    dragEnabled: allowDrags && !itemIsEmbryo(modelData)
                                    dragPayload: fullPath
                                    renaming: false
                                    renameEnabled: false
                                    tabHoverDropEnabled: true
                                    tabHoverDropPx: root.previewTabDropPx
                                    tabPinned: root.isPreviewPathActive(previewLevel + 1, fullPath)
                                    textBold: root.isPreviewPathActive(previewLevel + 1, fullPath)
                                    dimmedStyle: root.isPreviewDimmed(previewLevel + 1, fullPath)
                                    opacity: root.isPreviewDimmed(previewLevel + 1, fullPath) ? root.previewDimOpacity : 1.0
                                    onActivate: folderActivated(fullPath)
                                    onHoverEntered: {
                                        var centerPoint = mapToItem(root, width / 2, height / 2)
                                        updatePreviewFromHover(previewLevel + 1, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
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
