import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    id: root
    width: 1180
    height: 780
    visible: !sunTreeStartHidden
    title: "SunTree"
    color: "#0f1117"
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property var foldersModel: []
    property var embryosModel: []
    property var clipboardModel: []
    property var filtersModel: []
    property var parentModel: []
    property string selectedFilterName: ""
    property int hoveredLeftIndex: -1
    property int hoveredRightIndex: -1
    property int hoveredCenterIndex: -1
    property int hoveredFrameIndex: -1
    property int hoveredTopIndex: -1
    property int pendingLeftClickIndex: -1
    property string cwdPath: ""
    property string currentProjectColor: ""

    // --- The lens (Designdocument Perspective Resolver MVP.md, Part A) -------------------
    // The lens lives in one session (the perspective daemon), shared with Scope; SunTree
    // only asks it and shows what it answers - it builds no lens paths. The gestures are
    // Scope's. With a lens on, the left half shows the lens' folder in its project and a
    // frame (✕ and the lens' levels) stands above the CWD.
    property var lensState: ({ active: false })
    readonly property bool lensOn: !!(lensState && lensState.active)
    readonly property bool lensInProject: lensOn && !!lensState.project

    function refreshModels() {
        cwdPath = String(sunTreeBackend.cwd() || "")
        foldersModel = sunTreeBackend.listFolders()
        currentProjectColor = String(sunTreeBackend.effectiveProjectColor(cwdPath) || "")
        var reply = sunTreeBackend.lens("state", {})
        lensState = (reply && reply.ok) ? reply.result : ({ active: false })
        embryosModel = sunTreeBackend.listEmbryosAt(leftListingPath())
        clipboardModel = sunTreeBackend.listClipboardEntries()
        filtersModel = sunTreeBackend.listFilters()
        parentModel = sunTreeBackend.listParents()
    }

    /// The left half: the MyOS folders of the CWD; with a lens on, the lens' folder.
    function leftListingPath() {
        return lensInProject ? String(lensState.target || "") : cwdPath
    }

    /// Ask the session (look_at, move_to, take_off, ...) and show the lens afterwards.
    function lensRequest(method, params) {
        var reply = sunTreeBackend.lens(method, params || ({}))
        if (!reply || !reply.ok) {
            console.log("lens", method, "failed:", reply ? reply.error : "no reply")
            return false
        }
        refreshModels()
        leftSectorCanvas.requestPaint()
        return true
    }

    /// A MyOS folder (born or embryo): a double click on it puts on its lens.
    function isMyosFolder(entry) {
        if (entry && entry.folderType !== undefined && !isNaN(Number(entry.folderType))) {
            return Number(entry.folderType) > 0
        }
        return !!(entry && entry.isEmbryo === true)
    }

    /// Go to path: with a lens on, a project moves the lens there, keeping its depth; any
    /// other folder takes it off (Scope's projects row).
    function navigateTo(path) {
        var target = String(path || "")
        if (target.length === 0) return
        if (lensOn) {
            if (sunTreeBackend.lens("move_to", { "path": target }).ok) {
                sunTreeBackend.setCwd(target)
                return
            }
            sunTreeBackend.lens("take_off", {})
        }
        sunTreeBackend.setCwd(target)
    }

    /// ✕ on the frame: only the lens goes, one stays where it looked - its folder in its
    /// project becomes the CWD (an embryo stays one: then the project).
    function takeOffLens() {
        if (!lensOn) return
        var projectDir = String(lensState.project_dir || "")
        var target = String(lensState.target || "")
        if (!lensRequest("take_off")) return
        if (!sunTreeBackend.setCwd(target) && projectDir.length > 0) {
            sunTreeBackend.setCwd(projectDir)
        }
    }

    /// The frame: the levels of the lens below its project (04_Finanz, Ausgaben, ...).
    function frameEntries() {
        if (!lensInProject) return []
        var projectDir = String(lensState.project_dir || "").replace(/\/+$/, "")
        var target = String(lensState.target || "").replace(/\/+$/, "")
        if (target.indexOf(projectDir + "/") !== 0) return []
        var parts = target.slice(projectDir.length + 1).split("/").filter(function(p) { return p.length > 0 })
        var out = []
        var path = projectDir
        for (var i = 0; i < parts.length; i++) {
            path += "/" + parts[i]
            out.push({ label: parts[i], path: path })
        }
        return out
    }

    function toggleFromHotkey() {
        visible = !visible
        if (visible) {
            raise()
            requestActivate()
            refreshModels()
        }
    }

    function fullPathFromEntry(entry) {
        if (!entry) {
            return ""
        }
        var explicitPath = String(entry.path || "")
        if (explicitPath.length > 0) {
            if (explicitPath.charAt(0) === "/") {
                return explicitPath
            }
        }
        var raw = String(entry.name || "")
        if (raw.length === 0) {
            return ""
        }
        if (raw.charAt(0) === "/") {
            return raw
        }
        var base = String(sunTreeBackend.cwd() || "")
        if (base.endsWith("/")) {
            return base + raw
        }
        return base + "/" + raw
    }

    function leftEntries() {
        var rows = []
        var base = leftListingPath().replace(/\/+$/, "")
        for (var i = 0; i < embryosModel.length; i++) {
            var item = embryosModel[i]
            var name = String((item && item.name) ? item.name : "")
            rows.push({
                kind: "template",
                label: name.indexOf("/") >= 0 ? name.split("/").filter(function(p) { return p.length > 0 }).slice(-1)[0] : name,
                path: String((item && item.path) ? item.path : "") || (name.charAt(0) === "/" ? name : base + "/" + name),
                color: String((item && item.color) ? item.color : ""),
                entry: item
            })
        }
        return rows
    }

    function rightEntries() {
        var rows = []
        for (var i = 0; i < foldersModel.length; i++) {
            rows.push({
                kind: "project",
                label: String((foldersModel[i] && foldersModel[i].name) ? foldersModel[i].name : ""),
                color: String((foldersModel[i] && foldersModel[i].color) ? foldersModel[i].color : ""),
                entry: foldersModel[i]
            })
        }
        return rows
    }

    function cwdLeafName() {
        var cwd = String(cwdPath || "")
        var parts = cwd.split("/").filter(function(p) { return p.length > 0 })
        if (parts.length === 0) {
            return "/"
        }
        return String(parts[parts.length - 1] || "/")
    }

    function projectNameFromCwd() {
        var parsed = parseApdFromPath(String(cwdPath || ""))
        return parsed.valid ? String(parsed.projectName || "") : ""
    }

    function _adjustColor(hex, factor) {
        var text = String(hex || "").trim()
        var m = text.match(/^#([0-9a-fA-F]{6})$/)
        if (!m) {
            return text
        }
        var value = m[1]
        var r = parseInt(value.slice(0, 2), 16)
        var g = parseInt(value.slice(2, 4), 16)
        var b = parseInt(value.slice(4, 6), 16)
        var clamp = function(v) { return Math.max(0, Math.min(255, Math.round(v))) }
        var toHex = function(v) {
            var s = clamp(v).toString(16)
            return s.length < 2 ? ("0" + s) : s
        }
        return "#" + toHex(r * factor) + toHex(g * factor) + toHex(b * factor)
    }

    function _sectorColor(base, hovered, selected, fallback) {
        var source = String(base || "")
        if (source.length === 0) {
            source = fallback
        }
        if (selected) {
            return _adjustColor(source, 1.12)
        }
        if (hovered) {
            return _adjustColor(source, 0.92)
        }
        return _adjustColor(source, 0.82)
    }

    function topBandEntries() {
        var rows = []
        for (var i = 0; i < filtersModel.length; i++) {
            var p = filtersModel[i]
            rows.push({
                kind: "filter",
                label: String((p && p.name) ? p.name : "Filter")
            })
        }
        rows.push({
            kind: "clipboardPath",
            label: "Clipboard (" + clipboardModel.length + ")"
        })
        rows.push({
            kind: "clipboardCreate",
            label: "Dummy Ablage"
        })
        return rows
    }

    function centerStackEntries() {
        var rows = parentModel || []
        var out = []
        if (rows.length <= 1) {
            return out
        }
        for (var i = rows.length - 2; i >= 0; i--) {
            var row = rows[i]
            var path = String((row && row.path) ? row.path : "")
            var label = String((row && row.label) ? row.label : "")
            if (path === "/") {
                continue
            }
            if (path === "/home" || label.toLowerCase() === "home") {
                label = "Home"
            }
            out.push({
                label: label.length > 0 ? label : path,
                path: path,
                color: String((row && row.color) ? row.color : "")
            })
        }
        return out
    }

    function parseApdFromPath(path) {
        var raw = String(path || "").trim()
        var parts = raw.split("/").filter(function(p) { return p.length > 0 })
        var idx = -1
        for (var i = parts.length - 1; i >= 0; i--) {
            if (parts[i] === "Projekte" && i + 1 < parts.length) {
                idx = i
                break
            }
        }
        if (idx < 0) {
            return { valid: false, apdPath: "", apdParts: [], projectName: "", tailParts: [] }
        }
        var apdParts = parts.slice(0, idx + 2)
        return {
            valid: true,
            apdPath: "/" + apdParts.join("/"),
            apdParts: apdParts,
            projectName: String(parts[idx + 1] || ""),
            tailParts: parts.slice(idx + 2)
        }
    }

    /// A click on the left half: with a lens on, a flatter or sharper lens; without one,
    /// SunTree goes into the folder (it has no file list to browse in).
    function applyLeftClick(index) {
        var rows = leftEntries()
        if (!(index >= 0 && index < rows.length)) return
        if (lensOn) {
            lensRequest("look_at", { "path": rows[index].path })
        } else {
            sunTreeBackend.enterFolder(rows[index].path)
        }
    }

    /// A double click: on a MyOS folder it puts on its lens and the CWD stays; with a lens
    /// on it gets sharper, or another department's lens is put on (A3).
    function applyLeftDoubleClick(index) {
        var rows = leftEntries()
        if (!(index >= 0 && index < rows.length)) return
        if (lensOn || isMyosFolder(rows[index].entry)) {
            lensRequest("look_at", { "path": rows[index].path })
        } else {
            sunTreeBackend.enterFolder(rows[index].path)
        }
    }

    function leftSectorIndex(localX, localY, areaWidth, areaHeight, count, innerR, outerR) {
        if (count <= 0) {
            return -1
        }
        var cx = areaWidth
        var cy = areaHeight * 0.5
        var dx = localX - cx
        var dy = localY - cy
        var radius = Math.sqrt(dx * dx + dy * dy)
        if (radius < innerR || radius > outerR) {
            return -1
        }
        var deg = Math.atan2(dy, dx) * 180 / Math.PI
        if (deg < 0) {
            deg += 360
        }
        if (deg < 90 || deg > 270) {
            return -1
        }
        var rel = deg - 90
        var idx = Math.floor(rel / (180 / count))
        if (idx < 0 || idx >= count) {
            return -1
        }
        // Left half should start at top; geometric slices start at bottom.
        return count - 1 - idx
    }

    function rightSectorIndex(localX, localY, areaWidth, areaHeight, count, innerR, outerR) {
        if (count <= 0) {
            return -1
        }
        var cx = 0
        var cy = areaHeight * 0.5
        var dx = localX - cx
        var dy = localY - cy
        var radius = Math.sqrt(dx * dx + dy * dy)
        if (radius < innerR || radius > outerR) {
            return -1
        }
        var deg = Math.atan2(dy, dx) * 180 / Math.PI
        if (deg < 0) {
            deg += 360
        }
        if (deg > 90 && deg < 270) {
            return -1
        }
        var rel = deg <= 90 ? (deg + 90) : (deg - 270)
        var idx = Math.floor(rel / (180 / count))
        return (idx >= 0 && idx < count) ? idx : -1
    }

    Shortcut {
        sequence: "Ctrl+Alt+Space"
        onActivated: root.toggleFromHotkey()
    }

    Connections {
        target: sunTreeHotkey
        function onActivated() { root.toggleFromHotkey() }
    }

    Connections {
        target: sunTreeBackend
        function onDataChanged() {
            root.refreshModels()
            leftSectorCanvas.requestPaint()
            rightSectorCanvas.requestPaint()
        }
        function onCwdChanged() {
            root.refreshModels()
            leftSectorCanvas.requestPaint()
            rightSectorCanvas.requestPaint()
        }
    }

    Component.onCompleted: refreshModels()
    // The lens is shared with Scope: coming back, show what it is now.
    onActiveChanged: if (active) refreshModels()

    Timer {
        id: leftClickDelayTimer
        interval: 170
        repeat: false
        onTriggered: {
            var idx = pendingLeftClickIndex
            pendingLeftClickIndex = -1
            applyLeftClick(idx)
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#0f1117"

        Item {
            id: layoutRoot
            anchors.fill: parent
            anchors.margins: 20
            property real topBandHeight: 42
            property real stackWidth: 170
            property real stackGap: 14
            property real shellDiameter: Math.min(mainArea.height * 0.86, mainArea.width * 0.54)
            property real shellHalfWidth: shellDiameter * 0.5
            property real shellTop: (mainArea.height - shellDiameter) * 0.5
            property real shellBottom: shellTop + shellDiameter
            property real centerX: width * 0.5
            property real stackX: centerX - stackWidth * 0.5
            property real leftX: stackX - stackGap - shellHalfWidth
            property real rightX: stackX + stackWidth + stackGap
            property real cwdHeight: 72
            property real cwdWidth: stackWidth + 56
            property real cwdY: shellTop + shellDiameter * 0.5 - cwdHeight * 0.5
            property real halfOuterRadius: Math.min(shellHalfWidth - 8, shellDiameter * 0.5 - 8)
            property real halfInnerRadius: Math.max(38, halfOuterRadius * 0.43)

            Rectangle {
                id: topBand
                x: 0
                y: 0
                width: parent.width
                height: layoutRoot.topBandHeight
                radius: 10
                color: "#1a2230"
                border.width: 1
                border.color: "#324667"

                Flickable {
                    anchors.left: parent.left
                    anchors.right: closeButton.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 5
                    anchors.rightMargin: 8
                    anchors.topMargin: 5
                    anchors.bottomMargin: 5
                    contentWidth: topRow.implicitWidth
                    contentHeight: topRow.height
                    clip: true
                    interactive: contentWidth > width

                    Row {
                        id: topRow
                        spacing: 6
                        height: parent.height

                        Repeater {
                            model: topBandEntries()
                            delegate: Rectangle {
                                property var rowData: modelData
                                width: Math.max(100, labelItem.implicitWidth + 18)
                                height: 30
                                radius: 8
                                color: hoveredTopIndex === index ? "#496a97" : "#2c3f5d"
                                border.width: 1
                                border.color: hoveredTopIndex === index ? "#9ec2ff" : "#5f7297"

                                Text {
                                    id: labelItem
                                    anchors.centerIn: parent
                                    text: String((rowData && rowData.label) ? rowData.label : "")
                                    color: "#e8efff"
                                    font.pixelSize: 12
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onEntered: hoveredTopIndex = index
                                    onExited: if (hoveredTopIndex === index) hoveredTopIndex = -1
                                    onClicked: {
                                        var kind = String((rowData && rowData.kind) ? rowData.kind : "")
                                        if (kind === "filter") {
                                            selectedFilterName = String(rowData.label || "")
                                        } else if (kind === "clipboardPath") {
                                            sunTreeBackend.setCwd(sunTreeBackend.clipboardPath())
                                        } else if (kind === "clipboardCreate") {
                                            sunTreeBackend.createClipboardNote("capture-" + Date.now() + ".md")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: closeButton
                    width: 30
                    height: 30
                    anchors.right: parent.right
                    anchors.rightMargin: 6
                    anchors.verticalCenter: parent.verticalCenter
                    radius: 8
                    color: closeMouse.pressed ? "#d40000" : (closeMouse.containsMouse ? "#ff1e1e" : "#ea0000")
                    border.width: 1
                    border.color: "#ffd2d2"

                    Text {
                        anchors.centerIn: parent
                        text: "X"
                        color: "#ffffff"
                        font.bold: true
                        font.pixelSize: 13
                    }

                    MouseArea {
                        id: closeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: Qt.quit()
                    }
                }
            }

            Item {
                id: mainArea
                x: 0
                y: topBand.y + topBand.height + 14
                width: parent.width
                height: parent.height - y

                Item {
                    id: leftHalf
                    x: layoutRoot.leftX
                    y: layoutRoot.shellTop
                    width: layoutRoot.shellHalfWidth
                    height: layoutRoot.shellDiameter
                    clip: true

                    Rectangle {
                        x: 0
                        y: 0
                        width: layoutRoot.shellDiameter
                        height: layoutRoot.shellDiameter
                        radius: width * 0.5
                        color: "#273847"
                        border.width: 0
                    }

                    Canvas {
                        id: leftSectorCanvas
                        anchors.fill: parent
                        antialiasing: true
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.reset()
                            var rows = leftEntries()
                            if (!rows || rows.length === 0) {
                                return
                            }
                            var cx = width
                            var cy = height * 0.5
                            var startDeg = 90
                            var slice = 180 / rows.length
                            for (var i = 0; i < rows.length; i++) {
                                var segPos = rows.length - 1 - i
                                var a0 = (startDeg + segPos * slice) * Math.PI / 180
                                var a1 = (startDeg + (segPos + 1) * slice) * Math.PI / 180
                                var selected = false
                                var hovered = (hoveredLeftIndex === i)
                                var baseColor = String((rows[i] && rows[i].color) ? rows[i].color : "")
                                ctx.beginPath()
                                ctx.arc(cx, cy, layoutRoot.halfOuterRadius, a0, a1, false)
                                ctx.arc(cx, cy, layoutRoot.halfInnerRadius, a1, a0, true)
                                ctx.closePath()
                                ctx.fillStyle = _sectorColor(baseColor, hovered, selected, "#3b6b7d")
                                ctx.fill()
                                var mid = (a0 + a1) * 0.5
                                var r = layoutRoot.halfInnerRadius + 16
                                var tx = cx + Math.cos(mid) * r
                                var ty = cy + Math.sin(mid) * r
                                var label = String((rows[i] && rows[i].label) ? rows[i].label : "")
                                if (label.length > 12) {
                                    label = label.slice(0, 11) + "…"
                                }
                                ctx.save()
                                ctx.translate(tx, ty)
                                // Flip left labels to avoid upside-down text.
                                ctx.rotate(mid + Math.PI)
                                ctx.font = "12px sans-serif"
                                ctx.fillStyle = "#eff8ff"
                                // Left half: right-aligned and center-near anchor.
                                ctx.textAlign = "right"
                                ctx.textBaseline = "middle"
                                ctx.fillText(label, 0, 0)
                                ctx.restore()
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onPositionChanged: function(mouse) {
                            hoveredLeftIndex = leftSectorIndex(
                                mouse.x, mouse.y,
                                leftHalf.width, leftHalf.height,
                                leftEntries().length,
                                layoutRoot.halfInnerRadius,
                                layoutRoot.halfOuterRadius
                            )
                            leftSectorCanvas.requestPaint()
                        }
                        onExited: {
                            hoveredLeftIndex = -1
                            leftSectorCanvas.requestPaint()
                        }
                        onClicked: {
                            pendingLeftClickIndex = hoveredLeftIndex
                            leftClickDelayTimer.restart()
                        }
                        onDoubleClicked: {
                            leftClickDelayTimer.stop()
                            pendingLeftClickIndex = -1
                            applyLeftDoubleClick(hoveredLeftIndex)
                        }
                    }
                }

                Item {
                    id: rightHalf
                    x: layoutRoot.rightX
                    y: layoutRoot.shellTop
                    width: layoutRoot.shellHalfWidth
                    height: layoutRoot.shellDiameter
                    clip: true

                    Rectangle {
                        x: -layoutRoot.shellHalfWidth
                        y: 0
                        width: layoutRoot.shellDiameter
                        height: layoutRoot.shellDiameter
                        radius: width * 0.5
                        color: "#2d3750"
                        border.width: 0
                    }

                    Canvas {
                        id: rightSectorCanvas
                        anchors.fill: parent
                        antialiasing: true
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.reset()
                            var rows = rightEntries()
                            if (!rows || rows.length === 0) {
                                return
                            }
                            var cx = 0
                            var cy = height * 0.5
                            var startDeg = -90
                            var slice = 180 / rows.length
                            for (var i = 0; i < rows.length; i++) {
                                var a0 = (startDeg + i * slice) * Math.PI / 180
                                var a1 = (startDeg + (i + 1) * slice) * Math.PI / 180
                                var hovered = (hoveredRightIndex === i)
                                var baseColor = String((rows[i] && rows[i].color) ? rows[i].color : "")
                                ctx.beginPath()
                                ctx.arc(cx, cy, layoutRoot.halfOuterRadius, a0, a1, false)
                                ctx.arc(cx, cy, layoutRoot.halfInnerRadius, a1, a0, true)
                                ctx.closePath()
                                ctx.fillStyle = _sectorColor(baseColor, hovered, false, "#4e668f")
                                ctx.fill()
                                var mid = (a0 + a1) * 0.5
                                var r = layoutRoot.halfInnerRadius + 10
                                var tx = cx + Math.cos(mid) * r
                                var ty = cy + Math.sin(mid) * r
                                var label = String((rows[i] && rows[i].label) ? rows[i].label : "")
                                if (label.length > 12) {
                                    label = label.slice(0, 11) + "…"
                                }
                                ctx.save()
                                ctx.translate(tx, ty)
                                ctx.rotate(mid)
                                ctx.font = "12px sans-serif"
                                ctx.fillStyle = "#ecf2ff"
                                // Right half: left-aligned so text grows away from center.
                                ctx.textAlign = "left"
                                ctx.textBaseline = "middle"
                                ctx.fillText(label, 0, 0)
                                ctx.restore()
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onPositionChanged: function(mouse) {
                            hoveredRightIndex = rightSectorIndex(
                                mouse.x, mouse.y,
                                rightHalf.width, rightHalf.height,
                                rightEntries().length,
                                layoutRoot.halfInnerRadius,
                                layoutRoot.halfOuterRadius
                            )
                            rightSectorCanvas.requestPaint()
                        }
                        onExited: {
                            hoveredRightIndex = -1
                            rightSectorCanvas.requestPaint()
                        }
                        onClicked: {
                            var rows = rightEntries()
                            if (hoveredRightIndex >= 0 && hoveredRightIndex < rows.length) {
                                var full = fullPathFromEntry(rows[hoveredRightIndex].entry)
                                navigateTo(full)
                            }
                        }
                    }
                }

                Rectangle {
                    // The lens' frame (A3): ✕ takes it off (one stays where it looked); a
                    // level makes the lens flatter. Nearest to the CWD stands the deepest.
                    id: lensFrame
                    x: layoutRoot.stackX
                    y: layoutRoot.shellTop + 10
                    width: layoutRoot.stackWidth
                    height: Math.max(80, layoutRoot.cwdY - y - 10)
                    radius: 10
                    color: "transparent"
                    border.width: 2
                    border.color: "#e08a1e"
                    visible: lensInProject

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        onExited: hoveredFrameIndex = -1
                    }

                    Flickable {
                        anchors.fill: parent
                        anchors.margins: 8
                        contentHeight: Math.max(frameColumn.implicitHeight, height)
                        clip: true

                        Column {
                            id: frameColumn
                            y: Math.max(0, parent.height - implicitHeight)
                            width: parent.width
                            spacing: 6

                            Rectangle {
                                width: 30
                                height: 30
                                radius: 7
                                color: takeOffMouse.containsMouse ? "#5a4a33" : "#3a3328"
                                border.width: 1
                                border.color: "#e08a1e"

                                Text {
                                    anchors.centerIn: parent
                                    text: "\u2715"
                                    color: "#f4e6d2"
                                    font.pixelSize: 13
                                }

                                MouseArea {
                                    id: takeOffMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: takeOffLens()
                                }
                            }

                            Repeater {
                                model: frameEntries()
                                delegate: Rectangle {
                                    property var rowData: modelData
                                    width: parent.width
                                    height: 30
                                    radius: 7
                                    color: hoveredFrameIndex === index ? "#4a6f7f" : "#355767"
                                    border.width: index === frameEntries().length - 1 ? 1 : 0
                                    border.color: "#8cb8c4"

                                    Text {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        verticalAlignment: Text.AlignVCenter
                                        text: String((rowData && rowData.label) ? rowData.label : "")
                                        color: "#e4f6fb"
                                        font.pixelSize: 12
                                        font.bold: index === frameEntries().length - 1
                                        elide: Text.ElideRight
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onEntered: hoveredFrameIndex = index
                                        onExited: if (hoveredFrameIndex === index) hoveredFrameIndex = -1
                                        onClicked: lensRequest("look_at", { "path": String(rowData.path || "") })
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: centerStack
                    x: layoutRoot.stackX
                    y: layoutRoot.cwdY + layoutRoot.cwdHeight + 12
                    width: layoutRoot.stackWidth
                    height: Math.max(120, layoutRoot.shellBottom - y - 10)
                    radius: 10
                    color: "#1f2a3d"
                    border.width: 0

                    Flickable {
                        anchors.fill: parent
                        anchors.margins: 8
                        contentHeight: centerColumn.implicitHeight
                        clip: true

                        Column {
                            id: centerColumn
                            width: parent.width
                            spacing: 6

                            Repeater {
                                model: centerStackEntries()
                                delegate: Rectangle {
                                    property var rowData: modelData
                                    width: parent.width
                                    height: 32
                                    radius: 7
                                    color: hoveredCenterIndex === index
                                           ? (_adjustColor(String((rowData && rowData.color) ? rowData.color : ""), 0.96) || "#546c97")
                                           : (_adjustColor(String((rowData && rowData.color) ? rowData.color : ""), 0.78) || "#324663")
                                    border.width: 1
                                    border.color: hoveredCenterIndex === index
                                                  ? (_adjustColor(String((rowData && rowData.color) ? rowData.color : ""), 1.16) || "#c0d6ff")
                                                  : (_adjustColor(String((rowData && rowData.color) ? rowData.color : ""), 0.98) || "#6d82a8")

                                    Text {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        verticalAlignment: Text.AlignVCenter
                                        text: String((rowData && rowData.label) ? rowData.label : "")
                                        color: "#dbe6ff"
                                        font.pixelSize: 12
                                        elide: Text.ElideRight
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onEntered: hoveredCenterIndex = index
                                        onExited: if (hoveredCenterIndex === index) hoveredCenterIndex = -1
                                        onClicked: {
                                            navigateTo(String((rowData && rowData.path) ? rowData.path : ""))
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: cwdOval
                    width: layoutRoot.cwdWidth
                    height: layoutRoot.cwdHeight
                    radius: height * 0.5
                    x: layoutRoot.centerX - width * 0.5
                    y: layoutRoot.cwdY
                    z: 20
                    color: _adjustColor(currentProjectColor, 0.72) || "#2f3d60"
                    border.width: 2
                    border.color: _adjustColor(currentProjectColor, 1.1) || "#9cb7f0"

                    Column {
                        anchors.centerIn: parent
                        spacing: 2
                        width: parent.width - 24

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: cwdLeafName()
                            color: "#dbe5ff"
                            font.bold: true
                            font.pixelSize: 13
                            elide: Text.ElideRight
                            width: parent.width
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: projectNameFromCwd()
                            color: "#b7c8ef"
                            font.pixelSize: 11
                            visible: text.length > 0
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: sunTreeBackend.refreshAll()
                    }
                }

                Canvas {
                    id: rightArrowBottomToRight
                    width: 30
                    height: 30
                    x: cwdOval.x + cwdOval.width - width - 8
                    y: cwdOval.y + cwdOval.height * 0.5 - height * 0.5
                    z: 22
                    visible: hoveredCenterIndex >= 0
                    antialiasing: true
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = "#ffdd74"
                        ctx.lineWidth = 2
                        ctx.lineCap = "round"
                        // Right icon: arc 9h -> 12h, arrow at 12h.
                        ctx.beginPath()
                        ctx.moveTo(5, 15)
                        ctx.quadraticCurveTo(5, 5, 15, 5)
                        ctx.stroke()
                        ctx.beginPath()
                        ctx.moveTo(15, 5)
                        ctx.lineTo(11, 8)
                        ctx.moveTo(15, 5)
                        ctx.lineTo(19, 8)
                        ctx.stroke()
                    }
                }

                Canvas {
                    id: rightArrowRightToDown
                    width: 30
                    height: 30
                    x: cwdOval.x + cwdOval.width - width - 8
                    y: cwdOval.y + cwdOval.height * 0.5 - height * 0.5
                    z: 22
                    visible: hoveredRightIndex >= 0
                    antialiasing: true
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = "#ffdd74"
                        ctx.lineWidth = 2
                        ctx.lineCap = "round"
                        // Right icon: arc 9h -> 12h, arrow at 9h (reverse).
                        ctx.beginPath()
                        ctx.moveTo(5, 15)
                        ctx.quadraticCurveTo(5, 5, 15, 5)
                        ctx.stroke()
                        ctx.beginPath()
                        ctx.moveTo(5, 15)
                        ctx.lineTo(9, 12)
                        ctx.moveTo(5, 15)
                        ctx.lineTo(9, 18)
                        ctx.stroke()
                    }
                }

                Canvas {
                    id: leftArrowTopToLeft
                    width: 30
                    height: 30
                    x: cwdOval.x + 8
                    y: cwdOval.y + cwdOval.height * 0.5 - height * 0.5
                    z: 22
                    visible: hoveredFrameIndex >= 0
                    antialiasing: true
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = "#ffdd74"
                        ctx.lineWidth = 2
                        ctx.lineCap = "round"
                        // Left icon: arc 3h -> 6h, arrow at 3h.
                        ctx.beginPath()
                        ctx.moveTo(25, 15)
                        ctx.quadraticCurveTo(25, 25, 15, 25)
                        ctx.stroke()
                        ctx.beginPath()
                        ctx.moveTo(25, 15)
                        ctx.lineTo(21, 12)
                        ctx.moveTo(25, 15)
                        ctx.lineTo(21, 18)
                        ctx.stroke()
                    }
                }

                Canvas {
                    id: leftArrowLeftToUp
                    width: 30
                    height: 30
                    x: cwdOval.x + 8
                    y: cwdOval.y + cwdOval.height * 0.5 - height * 0.5
                    z: 22
                    visible: hoveredLeftIndex >= 0
                    antialiasing: true
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = "#ffdd74"
                        ctx.lineWidth = 2
                        ctx.lineCap = "round"
                        // Left icon: arc 3h -> 6h, arrow at 6h (reverse).
                        ctx.beginPath()
                        ctx.moveTo(25, 15)
                        ctx.quadraticCurveTo(25, 25, 15, 25)
                        ctx.stroke()
                        ctx.beginPath()
                        ctx.moveTo(15, 25)
                        ctx.lineTo(12, 21)
                        ctx.moveTo(15, 25)
                        ctx.lineTo(18, 21)
                        ctx.stroke()
                    }
                }
            }
        }
    }
}
