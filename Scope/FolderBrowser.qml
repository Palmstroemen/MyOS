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
    property var debugLogger: null
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
    property bool isPerspective: false
    readonly property bool is_perspective: isPerspective
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
    // Primary click intent (single click)
    signal folderActivated(string name)
    // Secondary click intent (double click)
    signal folderDoubleActivated(string name)
    signal folderPreviewed(string path)
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
    property bool cwdHoverPanelOpen: false
    property bool cwdHoverOverButton: false
    property bool cwdHoverOverPanel: false
    property int cwdHoverPanelHoverCount: 0
    property bool cwdHoverMainPanelHovered: false
    property var cwdHoverCascadePanelHovered: []
    property real cwdHoverPanelX: 0
    property real cwdHoverPanelY: 0
    property real cwdHoverPanelWidth: 160
    property int cwdHoverOutzonePx: 50
    property var cwdHoverCascadePanels: []
    property bool cwdHoverChildPanelOpen: false
    property bool cwdHoverOverChildPanel: false
    property real cwdHoverChildPanelY: 0
    property string cwdHoverChildPanelPath: ""
    property var cwdHoverChildEntries: []
    property bool cwdHoverGrandchildPanelOpen: false
    property bool cwdHoverOverGrandchildPanel: false
    property real cwdHoverGrandchildPanelY: 0
    property string cwdHoverGrandchildPanelPath: ""
    property var cwdHoverGrandchildEntries: []
    property int cwdTabDrop: 4
    property int cwdVerticalRightOverflow: 10
    property bool previewEnabled: true
    property bool previewFocusBackground: true
    // anchor: current behavior, hybrid: keep anchor but shift left to reduce early wrapping
    property string previewLayoutMode: "hybrid"
    // normal: equal preview column widths, eng: tighter per-column widths
    property string verticalPreviewMode: "eng"
    property var previewRows: []
    property var previewActivePaths: []
    property var previewAnchorCenters: []
    property var previewAnchorCentersY: []
    property real previewDimOpacity: 0.5
    property real previewDimOpacityH1: 0.3
    property bool s2CollapseOnS4EnterEnabled: true
    property int s2CollapseDurationMs: 500
    property bool s2CollapseTransitionRunning: false
    property bool s2CollapsedInS4: false
    property string s2CollapseTransitionKey: ""
    property bool s2ReverseSequenceEnabled: true
    property bool s2ReverseSequenceRunning: false
    property int s2ReverseSequenceDelayMs: 36
    property real s2CollapseProgress: 0.0
    property bool s2PointerCarryEnabled: true
    property real s2PointerCarryFactor: 0.5
    property bool s2SystemPointerCarryEnabled: true
    property real s2SystemPointerCarryFactor: 0.82
    property real s2SystemPointerUserOffsetFactor: 0.35
    property real previewPointerX: -1
    property real s2PointerCarryStartX: -1
    property real s2PointerCarryUserOffsetX: 0
    property real s2SystemCarryAppliedX: 0
    property var s2CollapseSnapshotActivePaths: []
    property var s2CollapseSnapshotAnchorCenters: []
    property var s2CollapseSnapshotAnchorCentersY: []
    property var s2CollapseSnapshotRows: []
    property bool h2LiftEnabled: false
    property int h2LiftLeftPx: 30
    property int h2LiftDurationMs: 1500
    property bool previewDebugBg: false
    property bool previewHoverDebug: false
    property bool previewReopenDebug: false
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
    property bool previewAnchorDebug: false
    // Safety cap for anchor viewport calculations to avoid runaway host heights.
    property int previewAnchorViewportClampPx: 5000
    property string previewAnchorDebugLastLine: ""
    property int previewPendingLevel: 0
    property string previewPendingPath: ""
    property var previewPendingItem: null
    property var previewPendingFillColor: null
    property real previewPendingCenterX: -1
    property real previewPendingCenterY: -1
    property bool previewReopenAfterPathCommitPending: false
    property bool previewReopenSkipNextFoldersReset: false
    property int previewReopenSkipFoldersResetCount: 0
    property bool previewReopenStabilizing: false
    property int previewReopenStabilizeMs: 220
    property bool previewInstantReopenEnabled: true
    property string previewReopenCommitPath: ""
    property var previewReopenActivePaths: []
    property var previewReopenAnchorCenters: []
    property var previewReopenAnchorCentersY: []
    property var previewReopenRows: []
    property int previewReopenRetryCount: 0
    property int previewReopenMaxRetries: 16

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
                var rowWidth = (row && row.width !== undefined)
                    ? Math.max(verticalMinWidth, Number(row.width) || 0)
                    : calculateFoldersColumnWidthForEntries(rowEntries)
                perRow.push(Math.round(rowWidth))
                maxPreviewWidth = Math.max(maxPreviewWidth, rowWidth)
                sumPreviewWidths += rowWidth
            }
            var spacingPerGap = verticalPreviewMode === "eng" ? 3 : 6
            var spacing = previewCount > 1 ? ((previewCount - 1) * spacingPerGap) : 0
            var previewTotal = verticalPreviewMode === "eng"
                ? Math.max(verticalMinWidth, sumPreviewWidths + spacing)
                : Math.max(verticalMinWidth, (maxPreviewWidth * previewCount) + spacing)
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
        if (previewInstantReopenEnabled && previewReopenStabilizing) {
            verticalRightColumnWidthHoldTarget = target
            verticalRightColumnWidthHold = target
            if (verticalRightWidthSmoother.running) {
                verticalRightWidthSmoother.stop()
            }
            return
        }
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
            // Keep vertical implicit height stable to prevent feedback loops
            // between contentHeight-driven relayout and fill-height spacers.
            var preferred = Number(verticalPreferredHeight || 0)
            if (preferred > 0) {
                return Math.round(preferred)
            }
            return 360
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
        // Returning from S3 to S2: undim S2 immediately.
        // This acts as the first phase trigger for the reverse transition.
        if (pointerOverMainHoverColumn && !pointerOverPreviewColumns) {
            return false
        }
        // Start dimming only after user actually entered the preview side (S3/H1).
        // While still on S2/main column, keep entries fully visible.
        if (!pointerOverPreviewColumns && Number(previewLastApplyLevel || -1) < 1) {
            return false
        }
        var deepestActiveLevel = -1
        for (var i = 0; i < previewActivePaths.length; i++) {
            if (String(previewActivePaths[i] || "").length > 0) {
                deepestActiveLevel = i
            }
        }
        // Dim all columns left of the current hover column.
        // Keep only the selected path item clear in each of those columns.
        if (deepestActiveLevel <= 0 || level < 0 || level >= deepestActiveLevel) {
            return false
        }
        var activePath = previewPathForLevel(level)
        if (activePath.length === 0) {
            return false
        }
        // In each left column: keep selected path clear, dim all others.
        return !isPreviewPathActive(level, fullPath)
    }

    function previewOpacityForEntry(level, fullPath) {
        if (!isPreviewDimmed(level, fullPath)) {
            return 1.0
        }
        return level <= 1 ? previewDimOpacityH1 : previewDimOpacity
    }

    function previewDeepestActiveLevel() {
        if (!previewActivePaths || previewActivePaths.length === 0) {
            return -1
        }
        for (var i = previewActivePaths.length - 1; i >= 0; i--) {
            if (String(previewActivePaths[i] || "").length > 0) {
                return i
            }
        }
        return -1
    }

    function isS3ToS4TransitionActive() {
        if (!verticalView || !s2CollapseOnS4EnterEnabled) {
            return false
        }
        if (!pointerOverPreviewColumns) {
            return false
        }
        return previewDeepestActiveLevel() >= 2
    }

    function maybeStartS2CollapseTransition() {
        if (!isS3ToS4TransitionActive()) {
            return
        }
        var key = previewPathForLevel(0) + "|" + previewPathForLevel(1) + "|" + String(previewDeepestActiveLevel())
        if ((s2CollapseTransitionRunning || s2CollapsedInS4) && key === s2CollapseTransitionKey) {
            return
        }
        s2CollapseTransitionKey = key
        // Snapshot the current open chain at transition start.
        // Later (at commit time) hover state may already have shifted/collapsed.
        s2CollapseSnapshotActivePaths = previewActivePaths.slice()
        s2CollapseSnapshotAnchorCenters = previewAnchorCenters.slice()
        s2CollapseSnapshotAnchorCentersY = previewAnchorCentersY.slice()
        s2CollapseSnapshotRows = previewRows.slice()
        if (previewPointerX < 0) {
            previewPointerX = Math.round(width * 0.5)
        }
        s2PointerCarryStartX = previewPointerX
        s2PointerCarryUserOffsetX = 0
        s2SystemCarryAppliedX = 0
        if (previewReopenDebug) {
            console.log(
                "[preview-reopen:snapshot]",
                "key=", s2CollapseTransitionKey,
                "active=", JSON.stringify(s2CollapseSnapshotActivePaths || []),
                "rows=", s2CollapseSnapshotRows.length
            )
        }
        s2CollapsedInS4 = true
        s2CollapseTransitionRunning = true
        // Restart progress each time so the carry phase is always visible.
        s2CollapseProgress = 0.0
        Qt.callLater(function() {
            if (s2CollapseTransitionRunning) {
                s2CollapseProgress = 1.0
            }
        })
        s2CollapseTransitionTimer.interval = s2CollapseDurationMs
        s2CollapseTransitionTimer.restart()
    }

    function maybeResetS2CollapseTransition() {
        // Reset only on explicit return to S2/main column.
        if (pointerOverMainHoverColumn && !pointerOverPreviewColumns) {
            if (s2ReverseSequenceEnabled && s2CollapsedInS4) {
                startReverseS2Sequence()
                return
            }
            s2CollapseTransitionRunning = false
            s2CollapsedInS4 = false
            s2CollapseTransitionKey = ""
            s2CollapseSnapshotActivePaths = []
            s2CollapseSnapshotAnchorCenters = []
            s2CollapseSnapshotAnchorCentersY = []
            s2CollapseSnapshotRows = []
            s2PointerCarryStartX = -1
            s2PointerCarryUserOffsetX = 0
            s2SystemCarryAppliedX = 0
            s2CollapseProgress = 0.0
            s2CollapseTransitionTimer.stop()
        }
    }

    function restorePreviewFromCollapseSnapshotForReverse() {
        if (!s2CollapseSnapshotRows || s2CollapseSnapshotRows.length === 0) {
            return
        }
        var rows = []
        for (var i = 0; i < s2CollapseSnapshotRows.length; i++) {
            var rawRow = s2CollapseSnapshotRows[i]
            if (!rawRow || !rawRow.entries || rawRow.entries.length === 0) {
                continue
            }
            rows.push({
                level: rows.length,
                parentPath: String(rawRow.parentPath || ""),
                color: colorToHex(rawRow.color, panelColor),
                width: Number(rawRow.width) || calculateFoldersColumnWidthForEntries(rawRow.entries),
                entries: rawRow.entries
            })
        }
        if (rows.length === 0) {
            return
        }
        previewLastHoverKey = ""
        previewRows = rows
        previewActivePaths = (s2CollapseSnapshotActivePaths || []).slice(0, rows.length)
        previewAnchorCenters = (s2CollapseSnapshotAnchorCenters || []).slice(0, rows.length)
        previewAnchorCentersY = (s2CollapseSnapshotAnchorCentersY || []).slice(0, rows.length)
        previewLastApplyAtMs = Date.now()
        previewLastApplyLevel = Math.max(-1, rows.length - 1)
    }

    function startReverseS2Sequence() {
        if (s2ReverseSequenceRunning) {
            return
        }
        s2ReverseSequenceRunning = true
        // 1) Logical swap stage is already represented by pointer state entering S2.
        // 2) Rebuild lost right-side columns immediately from snapshots.
        restorePreviewFromCollapseSnapshotForReverse()
        // 3) Animate the return only after rebuild is visible.
        s2ReverseSequenceTimer.interval = s2ReverseSequenceDelayMs
        s2ReverseSequenceTimer.restart()
    }

    function s2CarryOffsetForShift(baseShiftX) {
        if (!s2PointerCarryEnabled || !s2CollapseTransitionRunning) {
            return 0
        }
        var shift = Number(baseShiftX || 0)
        if (shift >= 0) {
            return 0
        }
        return (-shift * Math.max(0, s2PointerCarryFactor)) + Number(s2PointerCarryUserOffsetX || 0)
    }

    function s2PanelCarryOffsetForShift(baseShiftX) {
        // When real system cursor carry is active, keep panel path stable and
        // apply carry only to the cursor. This avoids cursor overshoot.
        if (s2SystemPointerCarryEnabled) {
            return 0
        }
        return s2CarryOffsetForShift(baseShiftX)
    }

    function syncSystemPointerCarry() {
        if (!s2SystemPointerCarryEnabled || !s2CollapseTransitionRunning) {
            return
        }
        if (!backend || typeof backend.moveCursorByX !== "function") {
            return
        }
        var baseShift = 0
        if (verticalRightColumnHost && typeof verticalRightColumnHost.previewColumnTargetWidth === "function") {
            baseShift = -Number(verticalRightColumnHost.previewColumnTargetWidth(0) || 0) * Number(s2CollapseProgress || 0)
        }
        var desiredSystemX = (baseShift * Math.max(0, s2SystemPointerCarryFactor))
            + (Number(s2PointerCarryUserOffsetX || 0) * Math.max(0, s2SystemPointerUserOffsetFactor))
        var delta = desiredSystemX - Number(s2SystemCarryAppliedX || 0)
        if (Math.abs(delta) < 0.2) {
            return
        }
        if (backend.moveCursorByX(delta)) {
            s2SystemCarryAppliedX += delta
            previewPointerX = Number(previewPointerX || 0) + delta
        }
    }

    function commitS2ToS1ShiftIfNeeded() {
        if (!s2CollapsedInS4) {
            return
        }
        var nextPath = previewPathForLevel(0)
        if (!nextPath || String(nextPath).length === 0) {
            return
        }
        if (String(nextPath) === String(path || "")) {
            return
        }
        var sourcePaths = (s2CollapseSnapshotActivePaths && s2CollapseSnapshotActivePaths.length > 0)
            ? s2CollapseSnapshotActivePaths
            : previewActivePaths
        var sourceAnchorX = (s2CollapseSnapshotAnchorCenters && s2CollapseSnapshotAnchorCenters.length > 0)
            ? s2CollapseSnapshotAnchorCenters
            : previewAnchorCenters
        var sourceAnchorY = (s2CollapseSnapshotAnchorCentersY && s2CollapseSnapshotAnchorCentersY.length > 0)
            ? s2CollapseSnapshotAnchorCentersY
            : previewAnchorCentersY
        var sourceRows = (s2CollapseSnapshotRows && s2CollapseSnapshotRows.length > 0)
            ? s2CollapseSnapshotRows
            : previewRows
        if (previewReopenDebug) {
            console.log(
                "[preview-reopen:commit]",
                "nextPath=", String(nextPath),
                "sourceActive=", JSON.stringify(sourcePaths || []),
                "sourceRows=", sourceRows.length
            )
        }
        preparePreviewReopenAfterPathCommit(nextPath, sourcePaths, sourceAnchorX, sourceAnchorY, sourceRows)
        folderPreviewed(String(nextPath))
    }

    function _normalizePathForCompare(rawPath) {
        var value = String(rawPath || "")
        if (value.length > 1 && value.endsWith("/")) {
            value = value.slice(0, -1)
        }
        return value
    }

    function _pathIsEqualOrChildOf(basePath, candidatePath) {
        var base = _normalizePathForCompare(basePath)
        var candidate = _normalizePathForCompare(candidatePath)
        if (!base || !candidate) {
            return false
        }
        if (candidate === base) {
            return true
        }
        if (base === "/") {
            return candidate.indexOf("/") === 0
        }
        return candidate.indexOf(base + "/") === 0
    }

    function preparePreviewReopenAfterPathCommit(nextPath, sourcePaths, sourceAnchorX, sourceAnchorY, sourceRows) {
        var commitPath = String(nextPath || "")
        var activeSource = sourcePaths || previewActivePaths
        var anchorXSource = sourceAnchorX || previewAnchorCenters
        var anchorYSource = sourceAnchorY || previewAnchorCentersY
        var rowSource = sourceRows || previewRows
        var shiftedPaths = []
        for (var i = 1; i < activeSource.length; i++) {
            var activePath = String(activeSource[i] || "")
            if (activePath.length > 0) {
                shiftedPaths.push(activePath)
            }
        }
        var shiftedRows = []
        for (var r = 1; r < rowSource.length; r++) {
            var rawRow = rowSource[r]
            if (!rawRow || !rawRow.entries || rawRow.entries.length === 0) {
                break
            }
            shiftedRows.push({
                level: shiftedRows.length,
                parentPath: String(rawRow.parentPath || ""),
                color: colorToHex(rawRow.color, panelColor),
                width: Number(rawRow.width) || calculateFoldersColumnWidthForEntries(rawRow.entries),
                entries: rawRow.entries
            })
        }
        previewReopenCommitPath = commitPath
        previewReopenActivePaths = shiftedPaths
        previewReopenAnchorCenters = anchorXSource.slice(1, 1 + shiftedPaths.length)
        previewReopenAnchorCentersY = anchorYSource.slice(1, 1 + shiftedPaths.length)
        previewReopenRows = shiftedRows
        previewReopenAfterPathCommitPending = shiftedPaths.length > 0 || shiftedRows.length > 0
        previewReopenRetryCount = 0
        if (previewReopenDebug) {
            console.log(
                "[preview-reopen:prepared]",
                "commitPath=", previewReopenCommitPath,
                "shiftedActive=", JSON.stringify(previewReopenActivePaths || []),
                "shiftedRows=", previewReopenRows.length,
                "pending=", previewReopenAfterPathCommitPending
            )
        }
    }

    function clearPendingPreviewReopen() {
        previewReopenAfterPathCommitPending = false
        previewReopenCommitPath = ""
        previewReopenActivePaths = []
        previewReopenAnchorCenters = []
        previewReopenAnchorCentersY = []
        previewReopenRows = []
        previewReopenRetryCount = 0
        previewReopenStabilizing = false
        previewReopenRetryTimer.stop()
        previewReopenStabilizeTimer.stop()
    }

    function schedulePreviewReopenRetry() {
        if (!previewReopenAfterPathCommitPending) {
            return
        }
        if (previewReopenRetryCount >= previewReopenMaxRetries) {
            if (previewReopenDebug) {
                console.log("[preview-reopen:retry-stop]", "reason=max-retries", "count=", previewReopenRetryCount)
            }
            clearPendingPreviewReopen()
            return
        }
        previewReopenRetryCount += 1
        if (previewReopenDebug) {
            console.log("[preview-reopen:retry]", "count=", previewReopenRetryCount, "max=", previewReopenMaxRetries)
        }
        previewReopenRetryTimer.restart()
    }

    function tryRestorePreviewAfterPathCommit() {
        if (!previewReopenAfterPathCommitPending) {
            if (previewReopenDebug) {
                console.log("[preview-reopen:restore-skip]", "reason=not-pending")
            }
            return false
        }
        if (_normalizePathForCompare(path) !== _normalizePathForCompare(previewReopenCommitPath)) {
            if (previewReopenDebug) {
                console.log(
                    "[preview-reopen:restore-wait-path]",
                    "path=", String(path || ""),
                    "commitPath=", String(previewReopenCommitPath || "")
                )
            }
            return false
        }

        var restoredActive = []
        var restoredRows = []
        var restoredAnchorX = []
        var restoredAnchorY = []
        if (previewReopenRows && previewReopenRows.length > 0) {
            restoredRows = previewReopenRows.slice()
            for (var k = 0; k < restoredRows.length; k++) {
                if (k < previewReopenActivePaths.length) {
                    restoredActive.push(String(previewReopenActivePaths[k] || ""))
                }
                if (k < previewReopenAnchorCenters.length) {
                    restoredAnchorX.push(previewReopenAnchorCenters[k])
                }
                if (k < previewReopenAnchorCentersY.length) {
                    restoredAnchorY.push(previewReopenAnchorCentersY[k])
                }
            }
        }
        if (restoredRows.length === 0) {
        for (var i = 0; i < previewReopenActivePaths.length; i++) {
            var activePath = String(previewReopenActivePaths[i] || "")
            if (activePath.length === 0) {
                break
            }
            if (!_pathIsEqualOrChildOf(path, activePath)) {
                break
            }

            var children = listPreviewChildren(activePath)
            if (children.length <= 0) {
                break
            }

            restoredActive.push(activePath)
            if (i < previewReopenAnchorCenters.length) {
                restoredAnchorX.push(previewReopenAnchorCenters[i])
            }
            if (i < previewReopenAnchorCentersY.length) {
                restoredAnchorY.push(previewReopenAnchorCentersY[i])
            }
            var segmentColor = getPathSegmentColor(activePath, false)
            var rowColor = segmentColor && segmentColor.fill !== undefined
                ? segmentColor.fill
                : panelColor
            restoredRows.push({
                level: i,
                parentPath: activePath,
                color: colorToHex(rowColor, panelColor),
                width: calculateFoldersColumnWidthForEntries(children),
                entries: children
            })
        }
        }

        if (restoredRows.length === 0) {
            if (previewReopenDebug) {
                console.log(
                    "[preview-reopen:restore-empty]",
                    "active=", JSON.stringify(previewReopenActivePaths || []),
                    "rowsFromSnapshot=", (previewReopenRows ? previewReopenRows.length : 0)
                )
            }
            return false
        }

        if (previewInstantReopenEnabled) {
            // Enter stabilization before applying restored rows, so width/hold
            // calculations in this frame are applied instantly (no wipe).
            previewReopenStabilizing = true
        }
        previewLastHoverKey = ""
        previewRows = restoredRows
        previewActivePaths = restoredActive
        previewAnchorCenters = restoredAnchorX
        previewAnchorCentersY = restoredAnchorY
        previewLastApplyAtMs = Date.now()
        previewLastApplyLevel = restoredActive.length - 1
        previewColumnsHoldActive = false
        previewColumnsHoldTimer.stop()

        previewReopenAfterPathCommitPending = false
        previewReopenSkipNextFoldersReset = true
        // Folder models can emit multiple change events right after path commit.
        // Keep restored preview chain alive across that short burst.
        previewReopenSkipFoldersResetCount = 4
        previewReopenStabilizing = true
        previewReopenStabilizeTimer.interval = previewReopenStabilizeMs
        previewReopenStabilizeTimer.restart()
        previewReopenCommitPath = ""
        previewReopenActivePaths = []
        previewReopenAnchorCenters = []
        previewReopenAnchorCentersY = []
        previewReopenRows = []
        previewReopenRetryCount = 0
        previewReopenRetryTimer.stop()
        if (previewReopenDebug) {
            console.log(
                "[preview-reopen:restore-ok]",
                "restoredActive=", JSON.stringify(restoredActive || []),
                "restoredRows=", restoredRows.length
            )
        }
        return true
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
        if (!tryRestorePreviewAfterPathCommit()) {
            schedulePreviewReopenRetry()
        }
        scheduleVerticalWidthUpdate()
    }
    onFoldersChanged: {
        if (previewReopenAfterPathCommitPending && tryRestorePreviewAfterPathCommit()) {
            scheduleVerticalWidthUpdate()
            return
        }
        if (previewReopenAfterPathCommitPending) {
            schedulePreviewReopenRetry()
            scheduleVerticalWidthUpdate()
            return
        }
        if (previewReopenSkipNextFoldersReset) {
            previewReopenSkipNextFoldersReset = false
            scheduleVerticalWidthUpdate()
            return
        }
        if (previewReopenSkipFoldersResetCount > 0) {
            previewReopenSkipFoldersResetCount -= 1
            if (previewReopenDebug) {
                console.log(
                    "[preview-reopen:folders-guard]",
                    "remaining=", previewReopenSkipFoldersResetCount,
                    "rows=", previewRows.length
                )
            }
            scheduleVerticalWidthUpdate()
            return
        }
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
    onPreviewActivePathsChanged: {
        maybeStartS2CollapseTransition()
    }
    onPointerOverPreviewColumnsChanged: {
        maybeStartS2CollapseTransition()
        maybeResetS2CollapseTransition()
    }
    onPointerOverMainHoverColumnChanged: {
        maybeResetS2CollapseTransition()
    }
    onS2CollapseProgressChanged: {
        syncSystemPointerCarry()
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
        id: cwdHoverCloseTimer
        interval: 60
        repeat: false
        onTriggered: {
            if (!root.cwdHoverOverButton && !root.anyCwdPanelHovered()) {
                root.closeCwdHoverPanels()
            }
        }
    }
    Timer {
        id: cwdHoverChildCloseTimer
        interval: 220
        repeat: false
        onTriggered: {
            if (!root.cwdHoverOverChildPanel && !root.cwdHoverOverPanel && !root.cwdHoverOverGrandchildPanel) {
                root.cwdHoverChildPanelOpen = false
                root.cwdHoverGrandchildPanelOpen = false
            }
        }
    }
    Timer {
        id: cwdHoverGrandchildCloseTimer
        interval: 220
        repeat: false
        onTriggered: {
            if (!root.cwdHoverOverGrandchildPanel && !root.cwdHoverOverChildPanel) {
                root.cwdHoverGrandchildPanelOpen = false
            }
        }
    }
    Timer {
        id: previewReopenRetryTimer
        interval: 34
        repeat: false
        onTriggered: {
            if (!root.previewReopenAfterPathCommitPending) {
                return
            }
            if (root.tryRestorePreviewAfterPathCommit()) {
                root.scheduleVerticalWidthUpdate()
                return
            }
            root.schedulePreviewReopenRetry()
        }
    }
    Timer {
        id: previewReopenStabilizeTimer
        interval: root.previewReopenStabilizeMs
        repeat: false
        onTriggered: {
            root.previewReopenStabilizing = false
            if (root.previewReopenDebug) {
                console.log("[preview-reopen:stabilize-end]")
            }
        }
    }
    Timer {
        id: s2CollapseTransitionTimer
        interval: root.s2CollapseDurationMs
        repeat: false
        onTriggered: {
            root.s2CollapseTransitionRunning = false
            root.s2PointerCarryStartX = -1
            root.s2PointerCarryUserOffsetX = 0
            root.s2SystemCarryAppliedX = 0
            root.commitS2ToS1ShiftIfNeeded()
        }
    }
    Timer {
        id: s2ReverseSequenceTimer
        interval: root.s2ReverseSequenceDelayMs
        repeat: false
        onTriggered: {
            root.s2CollapseTransitionRunning = false
            root.s2CollapsedInS4 = false
            root.s2CollapseTransitionKey = ""
            root.s2PointerCarryStartX = -1
            root.s2PointerCarryUserOffsetX = 0
            root.s2SystemCarryAppliedX = 0
            root.s2CollapseProgress = 0.0
            root.s2CollapseSnapshotActivePaths = []
            root.s2CollapseSnapshotAnchorCenters = []
            root.s2CollapseSnapshotAnchorCentersY = []
            root.s2CollapseSnapshotRows = []
            root.s2ReverseSequenceRunning = false
        }
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

    Behavior on s2CollapseProgress {
        NumberAnimation {
            duration: root.s2CollapseDurationMs
            easing.type: Easing.InOutCubic
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
        s2CollapseTransitionRunning = false
        s2CollapsedInS4 = false
        s2CollapseTransitionKey = ""
        s2CollapseSnapshotActivePaths = []
        s2CollapseSnapshotAnchorCenters = []
        s2CollapseSnapshotAnchorCentersY = []
        s2CollapseSnapshotRows = []
        s2PointerCarryStartX = -1
        s2PointerCarryUserOffsetX = 0
        s2SystemCarryAppliedX = 0
        s2CollapseProgress = 0.0
        s2ReverseSequenceRunning = false
        s2ReverseSequenceTimer.stop()
        s2CollapseTransitionTimer.stop()
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
        if (previewAnchorDebug) {
            var yLog = (hasY ? Math.round(y) : -1)
            console.log("[v-anchor:set]", "level=", level, "x=", Math.round(x), "y=", yLog, "path=", String(previewPendingPath || ""))
        }
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
            // Leaf hover should collapse immediately without hold artifacts.
            previewColumnsHoldActive = false
            previewColumnsHoldTimer.stop()
            if (_samePreviewRows(previewRows, nextRows)) {
                return
            }
            previewRows = nextRows
            return
        }

        if (children.length > 0) {
            var rowColor = colorToHex(_previewColorForItem(sourceItem, basePath, sourceFillColor), panelColor)
            var rowWidth = calculateFoldersColumnWidthForEntries(children)
            nextRows.push({
                level: level,
                parentPath: basePath,
                color: rowColor,
                width: rowWidth,
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
        var hasChildrenNow = listPreviewChildren(basePath).length > 0
        if (verticalView && !hasChildrenNow) {
            // Cancel any pending delayed/deeper preview apply and collapse now.
            previewHoverGen += 1
            previewHoverApplyScheduled = false
            previewHoverPendingGeneration = 0
            previewHoverDelayTimer.stop()
            previewPendingLevel = level
            previewPendingPath = basePath
            previewPendingItem = sourceItem
            previewPendingFillColor = sourceFillColor
            previewPendingCenterX = sourceCenterX
            previewPendingCenterY = sourceCenterY
            previewHoverApplyScheduled = true
            var immediateGeneration = previewHoverGen
            Qt.callLater(function() { _applyQueuedPreviewHover(immediateGeneration) })
            return
        }
        if (previewHoverApplyScheduled) {
            var pendingLevel = Math.max(0, Number(previewPendingLevel) || 0)
            // When overlapping hover events happen in the same frame,
            // keep the deeper level event to avoid collapse flicker.
            // Exception: when hovered target has no children, prefer immediate collapse.
            if (level < pendingLevel && hasChildrenNow) {
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
        var needsDelay = verticalView && hasChildrenNow && level >= previewHoverDelayMinLevel && previewHoverDelayMs > 0
        if (needsDelay) {
            previewHoverPendingGeneration = generation
            previewHoverDelayTimer.interval = previewHoverDelayMs
            previewHoverDelayTimer.restart()
            return
        }
        previewHoverDelayTimer.stop()
        Qt.callLater(function() { _applyQueuedPreviewHover(generation) })
    }

    function updatePreviewFromHover(sourceLevel, sourcePath, sourceItem, sourceFillColor, sourceCenterX, sourceCenterY) {
        if (!previewEnabled) {
            return
        }
        if (previewReopenStabilizing && verticalView) {
            if (previewReopenDebug) {
                console.log("[preview-reopen:hover-blocked]", "level=", sourceLevel, "path=", String(sourcePath || ""))
            }
            return
        }
        var level = Math.max(0, Number(sourceLevel) || 0)
        var basePath = String(sourcePath || "").trim()
        if (!basePath) {
            return
        }
        folderPreviewed(basePath)
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

    function parentPathsFullChain() {
        var parts = pathPartsFull()
        var paths = []
        for (var i = 0; i < parts.length - 1; i++) {
            paths.push("/" + parts.slice(0, i + 1).join("/"))
        }
        return paths
    }

    function visibleParentPaths() {
        var parents = parentPaths()
        if (parents.length <= maxParents) return parents
        return parents.slice(Math.max(0, parents.length - maxParents))
    }

    function cwdHoverOverlayHost() {
        return (root.Window && root.Window.window && root.Window.window.contentItem)
            ? root.Window.window.contentItem
            : (root.parent ? root.parent : root)
    }

    function cascadePanelY(anchorY, panelHeight) {
        var host = cwdHoverOverlayHost()
        var hostHeight = Math.max(0, Number(host && host.height !== undefined ? host.height : root.height) || 0)
        var h = Math.max(compactButtonHeight + 8, Number(panelHeight || 0))
        var y = Number(anchorY || 0)
        if (hostHeight > 0 && y > (hostHeight * 0.5)) {
            y = y - h + compactButtonHeight
        }
        if (hostHeight <= 0) {
            return Math.max(0, Math.round(y))
        }
        var maxY = Math.max(0, hostHeight - h)
        return Math.max(0, Math.min(maxY, Math.round(y)))
    }

    function openCwdCascadePanel(depth, fullPath, sourceItem) {
        var host = cwdHoverOverlayHost()
        var p = sourceItem.mapToItem(host, sourceItem.width, 0)
        var entries = listPreviewChildren(fullPath)
        var next = cwdHoverCascadePanels.slice(0, Math.max(0, depth))
        var nextHover = cwdHoverCascadePanelHovered.slice(0, Math.max(0, depth))
        if (!entries || entries.length === 0) {
            // No children => no panel on the right; also trim deeper panels.
            cwdHoverCascadePanels = next
            cwdHoverCascadePanelHovered = nextHover
            return
        }
        next.push({
            path: fullPath,
            y: p.y,
            entries: entries
        })
        nextHover.push(false)
        cwdHoverCascadePanels = next
        cwdHoverCascadePanelHovered = nextHover
    }

    function cwdPanelHoverEnter() {
        cwdHoverPanelHoverCount += 1
        cwdHoverOverPanel = true
        cwdHoverCloseTimer.stop()
    }

    function cwdPanelHoverLeave() {
        cwdHoverPanelHoverCount = Math.max(0, cwdHoverPanelHoverCount - 1)
        cwdHoverOverPanel = anyCwdPanelHovered()
        if (!cwdHoverOverPanel && !cwdHoverOverButton) {
            cwdHoverCloseTimer.restart()
        }
    }

    function anyCwdPanelHovered() {
        if (cwdHoverMainPanelHovered) return true
        for (var i = 0; i < cwdHoverCascadePanelHovered.length; i++) {
            if (cwdHoverCascadePanelHovered[i]) return true
        }
        return false
    }

    function closeCwdHoverPanels() {
        cwdHoverOverButton = false
        cwdHoverOverPanel = false
        cwdHoverOverChildPanel = false
        cwdHoverOverGrandchildPanel = false
        cwdHoverPanelHoverCount = 0
        cwdHoverMainPanelHovered = false
        cwdHoverCascadePanelHovered = []
        cwdHoverPanelOpen = false
        cwdHoverChildPanelOpen = false
        cwdHoverGrandchildPanelOpen = false
        cwdHoverCascadePanels = []
        cwdHoverCloseTimer.stop()
        cwdHoverChildCloseTimer.stop()
        cwdHoverGrandchildCloseTimer.stop()
    }

    function setCwdCascadePanelHovered(panelIndex, hovered) {
        var idx = Number(panelIndex)
        if (idx < 0) return
        var next = cwdHoverCascadePanelHovered.slice()
        while (next.length <= idx) {
            next.push(false)
        }
        next[idx] = !!hovered
        cwdHoverCascadePanelHovered = next
    }

    function isCwdCascadePanelHovered(panelIndex) {
        var idx = Number(panelIndex)
        if (idx < 0 || idx >= cwdHoverCascadePanelHovered.length) return false
        return !!cwdHoverCascadePanelHovered[idx]
    }

    function cwdCascadeSelectedPathForPanel(panelIndex) {
        var idx = Number(panelIndex)
        if (idx < 0) {
            return cwdHoverCascadePanels.length > 0 ? String(cwdHoverCascadePanels[0].path || "") : ""
        }
        return cwdHoverCascadePanels.length > (idx + 1) ? String(cwdHoverCascadePanels[idx + 1].path || "") : ""
    }

    function cwdPanelOpacityMultiplier(panelIndex, fullPath) {
        var selectedPath = cwdCascadeSelectedPathForPanel(panelIndex)
        if (selectedPath.length === 0) return 1.0
        var hovered = Number(panelIndex) < 0 ? cwdHoverMainPanelHovered : isCwdCascadePanelHovered(panelIndex)
        if (hovered) return 1.0
        return String(fullPath || "") === selectedPath ? 1.0 : 0.2
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
        if (previewInstantReopenEnabled && previewReopenStabilizing && verticalView) {
            verticalWidthAnim.stop()
            verticalPreferredWidth = target
            return
        }
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
        if (verticalView) return
        if (!topFoldersRow || !topRow || !rightButtonsRow || !pathRow) return
        if (topRow.width <= 0) return
        var toggleWidth = (showModeToggle && modeToggleButton) ? modeToggleButton.width : 0
        var gapCount = showModeToggle ? 4 : 3
        var rightWidth = rightButtonsRow.implicitWidth
        var visibleFoldersWidth = (!flowOnSecondLine && topFlowHost && topFlowHost.visible) ? topFoldersRow.implicitWidth : 0
        var usedVisible = pathRow.implicitWidth + visibleFoldersWidth + rightWidth + toggleWidth + (topRow.spacing * gapCount)
        var slackVisible = topRow.width - usedVisible
        var used = pathRow.implicitWidth + topFoldersRow.implicitWidth + rightWidth + toggleWidth + (topRow.spacing * gapCount)
        var slack = topRow.width - used
        // Decide wrapping using the hypothetical single-row layout (full used width)
        // to avoid wrap/unwap oscillation caused by state-dependent width metrics.
        var shouldWrap = flowOnSecondLine ? (slack < wrapSlackOff) : (slack < wrapSlackOn)
        if (flowOnSecondLine !== shouldWrap) {
            flowOnSecondLine = shouldWrap
            if (debugLayout) {
                console.log("[folderbrowser] wrap", path, "->", shouldWrap, "row", topRow.width, "used", used, "slack", slack)
            }
        }
    }

    function horizontalPathHostMaxWidth() {
        if (!topRow || !rightButtonsRow) return 0
        var toggleWidth = (showModeToggle && modeToggleButton) ? modeToggleButton.width : 0
        var gapCount = showModeToggle ? 4 : 3
        var foldersWidth = (!flowOnSecondLine && topFlowHost && topFlowHost.visible && topFoldersRow)
            ? topFoldersRow.implicitWidth
            : 0
        var maxWidth = topRow.width - rightButtonsRow.implicitWidth - toggleWidth - (topRow.spacing * gapCount) - foldersWidth
        return Math.max(0, maxWidth)
    }

    function updateVerticalButtonsPlacement() {
        if (!verticalView) return
        if (!verticalMainColumn || !verticalContentRow) return
        if (verticalContentRow.height <= 0) return
        var showRightColumn = shouldShowVerticalRightColumn()
        var freeHeight          = verticalSpacer ? verticalSpacer.height : 0
        var uListHeight         = verticalRightPreviewColumns ? verticalRightPreviewColumns.implicitHeight : 0
        var hasRightContent = (previewRows && previewRows.length > 0)
                              || previewColumnsHoldActive
                              || (uListHeight > 0.5)
        var shouldWrap          = false
        if (hasRightContent && !showRightColumn) {
            shouldWrap = foldersInSecondColumn
                ? (freeHeight * 2 <= uListHeight + 10)
                : (freeHeight < 1)
        }
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
                            checked: verticalPreviewMode === "normal"
                            onTriggered: verticalPreviewMode = "normal"
                        }
                        MenuItem {
                            text: qsTr("V-Vorschau: Eng")
                            checkable: true
                            checked: verticalPreviewMode === "eng"
                            onTriggered: verticalPreviewMode = "eng"
                        }
                        MenuSeparator {}
                        MenuItem {
                            text: qsTr("Instant Reopen")
                            checkable: true
                            checked: previewInstantReopenEnabled
                            onTriggered: previewInstantReopenEnabled = !previewInstantReopenEnabled
                        }
                        MenuItem {
                            text: qsTr("Tuning: Soft")
                            onTriggered: {
                                s2PointerCarryFactor = 0.35
                                s2CollapseDurationMs = 700
                                previewReopenStabilizeMs = 280
                                previewHoverDelayMs = 110
                            }
                        }
                        MenuItem {
                            text: qsTr("Tuning: Balanced")
                            onTriggered: {
                                s2PointerCarryFactor = 0.5
                                s2CollapseDurationMs = 500
                                previewReopenStabilizeMs = 220
                                previewHoverDelayMs = 90
                            }
                        }
                        MenuItem {
                            text: qsTr("Tuning: Aggressive")
                            onTriggered: {
                                s2PointerCarryFactor = 0.7
                                s2CollapseDurationMs = 380
                                previewReopenStabilizeMs = 160
                                previewHoverDelayMs = 60
                            }
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
                    Layout.preferredWidth: flowOnSecondLine ? 0 : Math.min(pathRow.implicitWidth, horizontalPathHostMaxWidth())
                    Layout.maximumWidth: flowOnSecondLine ? -1 : horizontalPathHostMaxWidth()
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
                                MouseArea {
                                    visible: isCurrent && !root.verticalView
                                    anchors.fill: parent
                                    acceptedButtons: Qt.NoButton
                                    hoverEnabled: true
                                    onEntered: {
                                        var host = root.cwdHoverOverlayHost()
                                        var p = parent.mapToItem(host, 0, parent.height)
                                        root.cwdHoverPanelX = p.x
                                        root.cwdHoverPanelY = p.y
                                        root.cwdHoverPanelWidth = Math.max(120, parent.width)
                                        root.cwdHoverOverButton = true
                                        root.cwdHoverPanelOpen = true
                                        root.cwdHoverChildPanelOpen = false
                                        root.cwdHoverGrandchildPanelOpen = false
                                        root.cwdHoverPanelHoverCount = 0
                                        root.cwdHoverMainPanelHovered = false
                                        root.cwdHoverOverPanel = false
                                        root.cwdHoverCascadePanels = []
                                        root.cwdHoverCascadePanelHovered = []
                                        root.cwdHoverChildPanelPath = ""
                                        root.cwdHoverGrandchildPanelPath = ""
                                        cwdHoverCloseTimer.stop()
                                    }
                                    onExited: {
                                        root.cwdHoverOverButton = false
                                        cwdHoverCloseTimer.restart()
                                    }
                                }
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
                                opacity: root.previewOpacityForEntry(0, fullPath)
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                onDoubleActivate: folderDoubleActivated(fullPath)
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
                                MenuSeparator {}
                                MenuItem {
                                    text: qsTr("Instant Reopen")
                                    checkable: true
                                    checked: previewInstantReopenEnabled
                                    onTriggered: previewInstantReopenEnabled = !previewInstantReopenEnabled
                                }
                                MenuItem {
                                    text: qsTr("Tuning: Soft")
                                    onTriggered: {
                                        s2PointerCarryFactor = 0.35
                                        s2SystemPointerCarryFactor = 0.72
                                        s2CollapseDurationMs = 700
                                        previewReopenStabilizeMs = 280
                                        previewHoverDelayMs = 110
                                    }
                                }
                                MenuItem {
                                    text: qsTr("Tuning: Balanced")
                                    onTriggered: {
                                        s2PointerCarryFactor = 0.5
                                        s2SystemPointerCarryFactor = 0.82
                                        s2CollapseDurationMs = 500
                                        previewReopenStabilizeMs = 220
                                        previewHoverDelayMs = 90
                                    }
                                }
                                MenuItem {
                                    text: qsTr("Tuning: Aggressive")
                                    onTriggered: {
                                        s2PointerCarryFactor = 0.7
                                        s2SystemPointerCarryFactor = 0.92
                                        s2CollapseDurationMs = 380
                                        previewReopenStabilizeMs = 160
                                        previewHoverDelayMs = 60
                                    }
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
                            onPositionChanged: function(mouse) {
                                var mapped = mapToItem(root, Number(mouse.x || 0), Number(mouse.y || 0))
                                root.previewPointerX = Number(mapped.x || 0)
                                if (root.s2CollapseTransitionRunning && root.s2PointerCarryStartX >= 0) {
                                    var rawDelta = root.previewPointerX - root.s2PointerCarryStartX
                                    root.s2PointerCarryUserOffsetX = rawDelta - Number(root.s2SystemCarryAppliedX || 0)
                                }
                            }
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
                                        property bool s2SelectedPath: root.isPreviewPathActive(0, fullPath)
                                        property bool s2CollapseActive: root.s2CollapseTransitionRunning || root.s2CollapsedInS4
                                        property real s2CollapseTargetY: cwpButton.mapToItem(
                                            foldersContent,
                                            0,
                                            cwpButton.height + 6
                                        ).y
                                        property real s2ShiftX: (s2CollapseActive && s2SelectedPath) ? (-indent) : 0
                                        property real s2ShiftY: (s2CollapseActive && s2SelectedPath)
                                            ? (s2CollapseTargetY - y)
                                            : 0
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
                                    tabPinned: root.isPreviewPathActive(0, fullPath)
                                    textBold: root.isPreviewPathActive(0, fullPath)
                                    dimmedStyle: root.isPreviewDimmed(0, fullPath)
                                    opacity: s2CollapseActive
                                        ? (s2SelectedPath ? 1.0 : 0.0)
                                        : root.previewOpacityForEntry(0, fullPath)
                                    transform: Translate {
                                        x: s2ShiftX
                                        y: s2ShiftY
                                    }
                                    Behavior on opacity {
                                        NumberAnimation {
                                            duration: root.s2CollapseDurationMs
                                            easing.type: Easing.OutCubic
                                        }
                                    }
                                    Behavior on s2ShiftY {
                                        NumberAnimation {
                                            duration: root.s2CollapseDurationMs
                                            easing.type: Easing.OutCubic
                                        }
                                    }
                                    Behavior on s2ShiftX {
                                        NumberAnimation {
                                            duration: root.s2CollapseDurationMs
                                            easing.type: Easing.OutCubic
                                        }
                                    }
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
                                onDoubleActivate: folderDoubleActivated(fullPath)
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
                    readonly property real previewColumnsSpacing: root.verticalPreviewMode === "eng" ? 3 : 6
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
                    function previewAnchorYForColumn(columnIndex) {
                        var sourceLevel = Math.max(0, previewLevelAt(columnIndex) - 1)
                        return root.previewAnchorCenterYForLevel(sourceLevel)
                    }
                    function previewColumnStartY(columnIndex, contentHeight, hostHeight) {
                        if (root.verticalPreviewMode !== "eng") {
                            return 0
                        }
                        var anchorY = previewAnchorYForColumn(columnIndex)
                        if (anchorY < 0) {
                            if (root.previewAnchorDebug) {
                                var miss = "[v-anchor:calc] col=" + columnIndex + " anchorY=-1 contentH=" + Math.round(Number(contentHeight) || 0) + " hostH=" + Math.round(Number(hostHeight) || 0)
                                if (miss !== root.previewAnchorDebugLastLine) {
                                    root.previewAnchorDebugLastLine = miss
                                    console.log(miss)
                                }
                            }
                            return 0
                        }
                        var localAnchor = root.mapToItem(verticalRightPreviewColumns, 0, anchorY).y
                        var itemHeight = Math.max(compactButtonHeight, 20)
                        var ch = Math.max(0, Number(contentHeight || 0))
                        var hh = Math.max(0, Number(hostHeight || 0))
                        var stackHalf = ch / 2
                        var shiftedAnchor = localAnchor - stackHalf
                        // Use a stable viewport height to avoid runaway hostHeight loops.
                        var stableHost = Math.max(0, Number(root.height) || 0)
                        var vh = stableHost > 0 ? Math.min(hh, stableHost) : hh
                        var clampPx = Math.max(200, Number(root.previewAnchorViewportClampPx) || 0)
                        if (vh > clampPx) {
                            vh = clampPx
                        }
                        var targetY = 0
                        var proposedTop = shiftedAnchor - (itemHeight / 2)
                        var maxTop = 0
                        var clampedTop = 0
                        if (ch <= vh) {
                            // Short content: shift content down inside viewport.
                            var proposedY = proposedTop
                            var maxY = Math.max(0, vh - ch)
                            targetY = Math.max(0, Math.min(maxY, proposedY))
                        } else {
                            // Tall content: scroll by moving content up.
                            maxTop = Math.max(0, ch - vh)
                            clampedTop = Math.max(0, Math.min(maxTop, proposedTop))
                            targetY = -Math.round(clampedTop)
                        }
                        var clampedY = Math.round(targetY)
                        if (root.previewAnchorDebug) {
                            var line = "[v-anchor:calc] col=" + columnIndex
                                + " anchorY=" + Math.round(anchorY)
                                + " localY=" + Math.round(localAnchor)
                                + " stackHalf=" + Math.round(stackHalf)
                                + " shiftedAnchor=" + Math.round(shiftedAnchor)
                                + " itemH=" + Math.round(itemHeight)
                                + " proposedTop=" + Math.round(proposedTop)
                                + " vh=" + Math.round(vh)
                                + " maxTop=" + Math.round(maxTop)
                                + " clampedTop=" + Math.round(clampedTop)
                                + " clampedY=" + Math.round(clampedY)
                                + " contentH=" + Math.round(ch)
                                + " hostH=" + Math.round(hh)
                            if (line !== root.previewAnchorDebugLastLine) {
                                root.previewAnchorDebugLastLine = line
                                console.log(line)
                            }
                        }
                        return clampedY
                    }
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
                            for (var i = 0; i < previewColumnCount; i++) {
                                var w = Math.round(previewColumnTargetWidth(i))
                                var px = Math.round(previewColumnX(i))
                                parts.push("c" + i + "=[" + px + ".." + Math.round(px + w) + "]")
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
                    function deepestPreviewActiveLevel() {
                        if (!root.previewActivePaths || root.previewActivePaths.length === 0) {
                            return -1
                        }
                        for (var i = root.previewActivePaths.length - 1; i >= 0; i--) {
                            if (String(root.previewActivePaths[i] || "").length > 0) {
                                return i
                            }
                        }
                        return -1
                    }
                    function shouldLiftH2() {
                        if (!root.h2LiftEnabled) {
                            return false
                        }
                        // Lift H2 while user is in H2 or deeper.
                        var deepest = deepestPreviewActiveLevel()
                        return deepest >= 2
                    }
                    function previewColumnNormalX(columnIndex) {
                        var cursor = previewColumnsStartX()
                        for (var i = 0; i < columnIndex; i++) {
                            cursor += previewColumnTargetWidth(i) + previewColumnsSpacing
                        }
                        return cursor
                    }
                    function previewColumnX(columnIndex) {
                        var collapseShift0 = -previewColumnTargetWidth(0) * root.s2CollapseProgress
                        var collapseShiftFollowing = -(previewColumnTargetWidth(0) + previewColumnsSpacing) * root.s2CollapseProgress
                        if (columnIndex === 0 && (root.s2CollapseTransitionRunning || root.s2CollapsedInS4)) {
                            // Move current S3 (H1) left into S2 slot during S3->S4 transition.
                            return previewColumnNormalX(0) + collapseShift0 + root.s2PanelCarryOffsetForShift(collapseShift0)
                        }
                        if (columnIndex > 0 && (root.s2CollapseTransitionRunning || root.s2CollapsedInS4)) {
                            // Pull following columns (S4/S5/...) left in X only by closing
                            // the horizontal gap left by S3.
                            return previewColumnNormalX(columnIndex) + collapseShiftFollowing + root.s2PanelCarryOffsetForShift(collapseShiftFollowing)
                        }
                        if (columnIndex === 1 && shouldLiftH2()) {
                            return previewColumnsStartX() + root.h2LiftLeftPx
                        }
                        return previewColumnNormalX(columnIndex)
                    }
                    function previewColumnZ(columnIndex) {
                        if (columnIndex === 0 && (root.s2CollapseTransitionRunning || root.s2CollapsedInS4)) {
                            return 20
                        }
                        return (columnIndex === 1 && shouldLiftH2()) ? 3 : 1
                    }
                    function previewColumnTargetWidth(columnIndex) {
                        if (!hasPreviewColumns || root.verticalPreviewMode !== "eng") {
                            return previewColumnWidth
                        }
                        var row = previewRowAt(columnIndex)
                        if (row && row.width !== undefined) {
                            return Math.max(verticalMinWidth, Number(row.width) || 0)
                        }
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
                        onPositionChanged: function(mouse) {
                            var mapped = mapToItem(root, Number(mouse.x || 0), Number(mouse.y || 0))
                            root.previewPointerX = Number(mapped.x || 0)
                            if (root.s2CollapseTransitionRunning && root.s2PointerCarryStartX >= 0) {
                                var rawDelta = root.previewPointerX - root.s2PointerCarryStartX
                                root.s2PointerCarryUserOffsetX = rawDelta - Number(root.s2SystemCarryAppliedX || 0)
                            }
                        }
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
                            clip: !(root.s2CollapseTransitionRunning || root.s2CollapsedInS4)
                            Item {
                                id: verticalRightPreviewColumns
                                anchors.fill: parent
                                height: parent.height
                                Repeater {
                                    model: verticalRightColumnHost.previewColumnCount
                                    delegate: Flickable {
                                        id: rightColumnFlick
                                        property int columnIndex: index
                                        function requestRefreshAnchorY() {
                                            Qt.callLater(function() {
                                                try {
                                                    if (rightColumnFlick && typeof rightColumnFlick.refreshAnchorY === "function") {
                                                        rightColumnFlick.refreshAnchorY()
                                                    }
                                                } catch (e) {
                                                    // Delegate may be destroyed while delayed callback is pending.
                                                }
                                            })
                                        }
                                        function refreshAnchorY() {
                                            var nextY = verticalRightColumnHost.previewColumnStartY(
                                                rightColumnFlick.columnIndex,
                                                rightColumnContent.implicitHeight,
                                                rightColumnFlick.height
                                            )
                                            if (Math.abs(rightColumnContent.y - nextY) > 0.5) {
                                                rightColumnContent.y = nextY
                                            }
                                        }
                                        x: verticalRightColumnHost.previewColumnX(rightColumnFlick.columnIndex)
                                        z: verticalRightColumnHost.previewColumnZ(rightColumnFlick.columnIndex)
                                        width: verticalRightColumnHost.previewColumnTargetWidth(rightColumnFlick.columnIndex)
                                        height: parent.height
                                        flickableDirection: Flickable.VerticalFlick
                                        contentHeight: rightColumnContent.implicitHeight
                                        boundsBehavior: Flickable.StopAtBounds
                                        clip: true
                                        Behavior on x {
                                            enabled: !(root.s2CollapseTransitionRunning || root.s2CollapsedInS4)
                                                     && !(root.previewInstantReopenEnabled && root.previewReopenStabilizing)
                                            NumberAnimation {
                                                duration: root.h2LiftDurationMs
                                                easing.type: Easing.InOutCubic
                                            }
                                        }
                                        onHeightChanged: requestRefreshAnchorY()
                                        onContentHeightChanged: requestRefreshAnchorY()
                                        Component.onCompleted: requestRefreshAnchorY()
                                        Connections {
                                            target: root
                                            function onPreviewAnchorCentersYChanged() { rightColumnFlick.requestRefreshAnchorY() }
                                            function onPreviewRowsChanged() { rightColumnFlick.requestRefreshAnchorY() }
                                            function onPreviewActivePathsChanged() { rightColumnFlick.requestRefreshAnchorY() }
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            z: 0
                                            hoverEnabled: true
                                            acceptedButtons: Qt.AllButtons
                                            preventStealing: true
                                            onPressed: function(mouse) { mouse.accepted = true }
                                            onReleased: function(mouse) { mouse.accepted = true }
                                        }
                                        Column {
                                            id: rightColumnContent
                                            y: 0
                                            z: 1
                                            width: parent.width
                                            spacing: 6
                                            Behavior on y {
                                                enabled: !(root.previewInstantReopenEnabled && root.previewReopenStabilizing)
                                                NumberAnimation {
                                                    duration: 120
                                                    easing.type: Easing.OutCubic
                                                }
                                            }
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
                                                    opacity: root.previewOpacityForEntry(previewLevel, fullPath)
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
                                                    onDoubleActivate: folderDoubleActivated(fullPath)
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
                                opacity: root.previewOpacityForEntry(0, fullPath)
                                renaming: allowRename && renameTargetPath === (itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                renameEnabled: allowRename
                                renameText: renameDraft
                                onRenameRequested: renameRequested(itemName(modelData).indexOf("/") === 0 ? itemName(modelData) : (path + "/" + itemName(modelData)))
                                onRenameTextEdited: renameTextEdited(text)
                                onRenameAccepted: renameAccepted()
                                onRenameCanceled: renameCanceled()
                                onActivate: folderActivated(fullPath)
                                onDoubleActivate: folderDoubleActivated(fullPath)
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
                                    opacity: root.previewOpacityForEntry(previewLevel + 1, fullPath)
                                    onActivate: folderActivated(fullPath)
                                    onDoubleActivate: folderDoubleActivated(fullPath)
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
            Item {
                id: cwdHoverPanel
                parent: root.cwdHoverOverlayHost()
                visible: root.cwdHoverPanelOpen && !root.verticalView
                x: root.cwdHoverPanelX
                y: root.cwdHoverPanelY
                z: 9999
                width: root.cwdHoverPanelWidth
                height: Math.max(root.compactButtonHeight + 8, cwdHoverPanelColumn.implicitHeight + 8)
                Rectangle {
                    anchors.fill: parent
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: root.panelColor
                    border.color: root.panelBorderColor
                }
                Flickable {
                    id: cwdHoverPanelFlick
                    z: 1
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 4
                    anchors.bottomMargin: 4
                    anchors.topMargin: 0
                    clip: true
                    contentWidth: width
                    contentHeight: cwdHoverPanelColumn.implicitHeight
                    interactive: false
                    boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: cwdHoverPanelColumn
                        width: cwdHoverPanelFlick.width
                        spacing: 4
                        Repeater {
                            model: root.parentPathsFullChain().slice().reverse()
                            delegate: FolderItem {
                                property var browserRoot: root
                                property string fullPath: String(modelData || "")
                                property var customColors: root.pathColorFunction ? root.pathColorFunction(fullPath, false) : null
                                width: parent.width
                                label: fullPath === "/" ? "/" : fullPath.split("/").filter(function(p){ return p.length > 0 }).slice(-1)[0]
                                style: (root.effectiveStyle() === "largeIcon") ? "smallIcon" : root.effectiveStyle()
                                compactHeight: root.compactButtonHeight
                                largeHeight: root.largeButtonHeight
                                largePadding: root.largeButtonPadding
                                iconSmall: root.iconSizeSmall
                                iconLarge: root.iconSizeLarge
                                textYOffset: root.buttonTextYOffset
                                iconSource: root.iconFolder
                                textLeftInset: root.effectiveStyle() === "text" ? 8 : 0
                                fillColor: customColors ? customColors.fill : root.pathButtonFill
                                strokeColor: customColors ? customColors.stroke : root.pathButtonBorder
                                textColor: root.text
                                textSize: root.baseFont
                                dimmedStyle: false
                                flatBottomCorners: false
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                opacity: root.cwdPanelOpacityMultiplier(-1, fullPath)
                                renaming: false
                                renameEnabled: false
                                onActivate: {
                                    browserRoot.closeCwdHoverPanels()
                                    browserRoot.folderActivated(fullPath)
                                }
                                HoverHandler {
                                    acceptedDevices: PointerDevice.Mouse
                                    onPointChanged: {
                                        if (!hovered) return
                                        var xPos = Number(point.position.x || 0)
                                        var inOutzone = xPos >= (width - Math.max(1, root.cwdHoverOutzonePx))
                                        if (inOutzone) {
                                            root.openCwdCascadePanel(0, fullPath, parent)
                                            root.cwdHoverChildPanelPath = fullPath
                                            root.cwdHoverChildEntries = root.listPreviewChildren(fullPath)
                                            root.cwdHoverChildPanelOpen = true
                                            root.cwdHoverGrandchildPanelOpen = false
                                            root.cwdHoverGrandchildPanelPath = ""
                                            cwdHoverChildCloseTimer.stop()
                                        } else if (root.cwdHoverChildPanelPath === fullPath && !root.cwdHoverOverChildPanel) {
                                            cwdHoverChildCloseTimer.restart()
                                        }
                                    }
                                    onHoveredChanged: {
                                        if (!hovered && root.cwdHoverChildPanelPath === fullPath && !root.cwdHoverOverChildPanel) {
                                            cwdHoverChildCloseTimer.restart()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                HoverHandler {
                    acceptedDevices: PointerDevice.Mouse
                    onHoveredChanged: {
                        if (hovered) {
                            root.cwdHoverMainPanelHovered = true
                            root.cwdPanelHoverEnter()
                        } else {
                            root.cwdHoverMainPanelHovered = false
                            root.cwdPanelHoverLeave()
                        }
                    }
                }
            }
            Repeater {
                model: root.cwdHoverCascadePanels
                delegate: Item {
                    required property int index
                    required property var modelData
                    property int cascadeIndex: index
                    property string cascadeBasePath: String(modelData && modelData.path ? modelData.path : "")
                    parent: root.cwdHoverOverlayHost()
                    visible: root.cwdHoverPanelOpen && !root.verticalView
                    x: root.cwdHoverPanelX + ((cascadeIndex + 1) * root.cwdHoverPanelWidth)
                    y: root.cascadePanelY(Number(modelData && modelData.y !== undefined ? modelData.y : 0), height)
                    z: 9999
                    width: Math.max(140, root.cwdHoverPanelWidth)
                    height: Math.max(root.compactButtonHeight + 8, cascadeColumn.implicitHeight + 8)
                    Rectangle {
                        anchors.fill: parent
                        radius: TagChips.CHIP_RADIUS_COMPACT
                        color: root.panelColor
                        border.color: root.panelBorderColor
                    }
                    Flickable {
                        id: cascadeFlick
                        z: 1
                        anchors.fill: parent
                        anchors.margins: 4
                        clip: true
                        contentWidth: width
                        contentHeight: cascadeColumn.implicitHeight
                        interactive: false
                        boundsBehavior: Flickable.StopAtBounds
                        Column {
                            id: cascadeColumn
                            width: cascadeFlick.width
                            spacing: 4
                            Repeater {
                                model: (modelData && modelData.entries) ? modelData.entries : []
                                delegate: FolderItem {
                                    property var browserRoot: root
                                    property string parentPath: cascadeBasePath
                                    property string fullPath: itemName(modelData).indexOf("/") === 0
                                        ? itemName(modelData)
                                        : root._resolveFullPath(parentPath, modelData)
                                    width: parent.width
                                    label: itemName(modelData)
                                    style: root.effectiveStyle()
                                    compactHeight: root.compactButtonHeight
                                    largeHeight: root.largeButtonHeight
                                    largePadding: root.largeButtonPadding
                                    iconSmall: root.iconSizeSmall
                                    iconLarge: root.iconSizeLarge
                                    textYOffset: root.buttonTextYOffset
                                    iconSource: root.iconFolder
                                    fillColor: root.folderFillColorForPath(modelData, 0, fullPath)
                                    strokeColor: root.folderStrokeColorForPath(modelData, 0, fullPath)
                                    textColor: root.textSoft
                                    textSize: root.baseFont
                                    dragEnabled: root.allowDrags && !root.itemIsEmbryo(modelData)
                                    dragPayload: fullPath
                                    tabHoverDropEnabled: true
                                    tabHoverDropPx: root.previewTabDropPx
                                    tabPinned: root.isPreviewPathActive(0, fullPath)
                                    textBold: root.isPreviewPathActive(0, fullPath)
                                    dimmedStyle: root.isPreviewDimmed(0, fullPath)
                                    opacity: root.previewOpacityForEntry(0, fullPath) * root.cwdPanelOpacityMultiplier(cascadeIndex, fullPath)
                                    renaming: false
                                    renameEnabled: false
                                    onActivate: {
                                        browserRoot.closeCwdHoverPanels()
                                        browserRoot.folderActivated(fullPath)
                                    }
                                    onHoverEntered: {
                                        var centerPoint = mapToItem(root, width / 2, height / 2)
                                        root.updatePreviewFromHover(0, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
                                    }
                                    HoverHandler {
                                        acceptedDevices: PointerDevice.Mouse
                                        onPointChanged: {
                                            if (!hovered) return
                                            var xPos = Number(point.position.x || 0)
                                            var inOutzone = xPos >= (width - Math.max(1, root.cwdHoverOutzonePx))
                                            if (inOutzone) {
                                                root.openCwdCascadePanel(cascadeIndex + 1, fullPath, parent)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    HoverHandler {
                        acceptedDevices: PointerDevice.Mouse
                        onHoveredChanged: {
                            if (hovered) {
                                root.setCwdCascadePanelHovered(cascadeIndex, true)
                                root.cwdPanelHoverEnter()
                            } else {
                                root.setCwdCascadePanelHovered(cascadeIndex, false)
                                root.cwdPanelHoverLeave()
                            }
                        }
                    }
                }
            }
            Item {
                id: cwdHoverChildPanel
                parent: root.cwdHoverOverlayHost()
                visible: root.cwdHoverPanelOpen && root.cwdHoverChildPanelOpen && !root.verticalView && false
                x: root.cwdHoverPanelX + root.cwdHoverPanelWidth
                y: root.cascadePanelY(root.cwdHoverChildPanelY, height)
                z: 9999
                width: Math.max(140, root.cwdHoverPanelWidth)
                height: Math.max(root.compactButtonHeight + 8, cwdHoverChildPanelColumn.implicitHeight + 8)
                Rectangle {
                    anchors.fill: parent
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: root.panelColor
                    border.color: root.panelBorderColor
                }
                Flickable {
                    id: cwdHoverChildPanelFlick
                    z: 1
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    contentWidth: width
                    contentHeight: cwdHoverChildPanelColumn.implicitHeight
                    interactive: false
                    boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: cwdHoverChildPanelColumn
                        width: cwdHoverChildPanelFlick.width
                        spacing: 4
                        Repeater {
                            model: root.cwdHoverChildEntries
                            delegate: FolderItem {
                                property var browserRoot: root
                                property string fullPath: itemName(modelData).indexOf("/") === 0
                                    ? itemName(modelData)
                                    : root._resolveFullPath(root.cwdHoverChildPanelPath, modelData)
                                width: parent.width
                                label: itemName(modelData)
                                style: root.effectiveStyle()
                                compactHeight: root.compactButtonHeight
                                largeHeight: root.largeButtonHeight
                                largePadding: root.largeButtonPadding
                                iconSmall: root.iconSizeSmall
                                iconLarge: root.iconSizeLarge
                                textYOffset: root.buttonTextYOffset
                                iconSource: root.iconFolder
                                fillColor: root.folderFillColorForPath(modelData, 0, fullPath)
                                strokeColor: root.folderStrokeColorForPath(modelData, 0, fullPath)
                                textColor: root.textSoft
                                textSize: root.baseFont
                                dragEnabled: root.allowDrags && !root.itemIsEmbryo(modelData)
                                dragPayload: fullPath
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                tabPinned: root.isPreviewPathActive(0, fullPath)
                                textBold: root.isPreviewPathActive(0, fullPath)
                                dimmedStyle: root.isPreviewDimmed(0, fullPath)
                                opacity: root.previewOpacityForEntry(0, fullPath)
                                renaming: false
                                renameEnabled: false
                                onActivate: {
                                    browserRoot.closeCwdHoverPanels()
                                    browserRoot.folderActivated(fullPath)
                                }
                                onHoverEntered: {
                                    var centerPoint = mapToItem(root, width / 2, height / 2)
                                    root.updatePreviewFromHover(0, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    acceptedButtons: Qt.NoButton
                                    hoverEnabled: true
                                    onPositionChanged: function(mouse) {
                                        if (!containsMouse) return
                                        var inOutzone = Number(mouse.x || 0) >= (width - Math.max(1, root.cwdHoverOutzonePx))
                                        if (inOutzone) {
                                            var host = root.cwdHoverOverlayHost()
                                            var p = parent.mapToItem(host, parent.width, 0)
                                            root.cwdHoverGrandchildPanelY = p.y
                                            root.cwdHoverGrandchildPanelPath = fullPath
                                            root.cwdHoverGrandchildEntries = root.listPreviewChildren(fullPath)
                                            root.cwdHoverGrandchildPanelOpen = true
                                            cwdHoverGrandchildCloseTimer.stop()
                                        } else if (root.cwdHoverGrandchildPanelPath === fullPath && !root.cwdHoverOverGrandchildPanel) {
                                            cwdHoverGrandchildCloseTimer.restart()
                                        }
                                    }
                                    onExited: {
                                        if (root.cwdHoverGrandchildPanelPath === fullPath && !root.cwdHoverOverGrandchildPanel) {
                                            cwdHoverGrandchildCloseTimer.restart()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                HoverHandler {
                    acceptedDevices: PointerDevice.Mouse
                    onHoveredChanged: {
                        root.cwdHoverOverChildPanel = hovered
                        if (hovered) {
                            cwdHoverCloseTimer.stop()
                            cwdHoverChildCloseTimer.stop()
                        } else {
                            cwdHoverCloseTimer.restart()
                            cwdHoverChildCloseTimer.restart()
                        }
                    }
                }
            }
            Item {
                id: cwdHoverGrandchildPanel
                parent: root.cwdHoverOverlayHost()
                visible: root.cwdHoverPanelOpen && root.cwdHoverChildPanelOpen && root.cwdHoverGrandchildPanelOpen && !root.verticalView && false
                x: root.cwdHoverPanelX + (2 * root.cwdHoverPanelWidth)
                y: root.cascadePanelY(root.cwdHoverGrandchildPanelY, height)
                z: 9999
                width: Math.max(140, root.cwdHoverPanelWidth)
                height: Math.max(root.compactButtonHeight + 8, cwdHoverGrandchildPanelColumn.implicitHeight + 8)
                Rectangle {
                    anchors.fill: parent
                    radius: TagChips.CHIP_RADIUS_COMPACT
                    color: root.panelColor
                    border.color: root.panelBorderColor
                }
                Flickable {
                    id: cwdHoverGrandchildPanelFlick
                    z: 1
                    anchors.fill: parent
                    anchors.margins: 4
                    clip: true
                    contentWidth: width
                    contentHeight: cwdHoverGrandchildPanelColumn.implicitHeight
                    interactive: false
                    boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: cwdHoverGrandchildPanelColumn
                        width: cwdHoverGrandchildPanelFlick.width
                        spacing: 4
                        Repeater {
                            model: root.cwdHoverGrandchildEntries
                            delegate: FolderItem {
                                property var browserRoot: root
                                property string fullPath: itemName(modelData).indexOf("/") === 0
                                    ? itemName(modelData)
                                    : root._resolveFullPath(root.cwdHoverGrandchildPanelPath, modelData)
                                width: parent.width
                                label: itemName(modelData)
                                style: root.effectiveStyle()
                                compactHeight: root.compactButtonHeight
                                largeHeight: root.largeButtonHeight
                                largePadding: root.largeButtonPadding
                                iconSmall: root.iconSizeSmall
                                iconLarge: root.iconSizeLarge
                                textYOffset: root.buttonTextYOffset
                                iconSource: root.iconFolder
                                fillColor: root.folderFillColorForPath(modelData, 0, fullPath)
                                strokeColor: root.folderStrokeColorForPath(modelData, 0, fullPath)
                                textColor: root.textSoft
                                textSize: root.baseFont
                                dragEnabled: root.allowDrags && !root.itemIsEmbryo(modelData)
                                dragPayload: fullPath
                                tabHoverDropEnabled: true
                                tabHoverDropPx: root.previewTabDropPx
                                tabPinned: root.isPreviewPathActive(0, fullPath)
                                textBold: root.isPreviewPathActive(0, fullPath)
                                dimmedStyle: root.isPreviewDimmed(0, fullPath)
                                opacity: root.previewOpacityForEntry(0, fullPath)
                                renaming: false
                                renameEnabled: false
                                onActivate: {
                                    browserRoot.closeCwdHoverPanels()
                                    browserRoot.folderActivated(fullPath)
                                }
                                onHoverEntered: {
                                    var centerPoint = mapToItem(root, width / 2, height / 2)
                                    root.updatePreviewFromHover(0, fullPath, modelData, fillColor, centerPoint.x, centerPoint.y)
                                }
                            }
                        }
                    }
                }
                HoverHandler {
                    acceptedDevices: PointerDevice.Mouse
                    onHoveredChanged: {
                        root.cwdHoverOverGrandchildPanel = hovered
                        if (hovered) {
                            cwdHoverCloseTimer.stop()
                            cwdHoverGrandchildCloseTimer.stop()
                        } else {
                            cwdHoverCloseTimer.restart()
                            cwdHoverGrandchildCloseTimer.restart()
                        }
                    }
                }
            }
        }
    }
}
