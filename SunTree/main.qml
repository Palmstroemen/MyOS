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
    property string cpdPath: ""
    property string cpdLabel: ""
    property var perspectiveState: ({ active: false, cpd: "", projectRoot: "", cwdReal: "" })
    property string lastSyncedPerspectiveCpd: ""
    property bool lastSyncedPerspectiveActive: false
    property int hoveredLeftIndex: -1
    property int hoveredRightIndex: -1
    property int hoveredCenterIndex: -1
    property int hoveredCpdIndex: -1
    property int hoveredTopIndex: -1
    property int selectedLeftIndex: -1
    property int pendingLeftClickIndex: -1
    property int leftEventSeq: 0
    property string cwdPath: ""
    property string currentProjectColor: ""

    function refreshModels() {
        cwdPath = String(sunTreeBackend.cwd() || "")
        foldersModel = sunTreeBackend.listFolders()
        currentProjectColor = String(sunTreeBackend.effectiveProjectColor(cwdPath) || "")
        syncPerspectiveState()
        if (perspectiveState.active) {
            embryosModel = sunTreeBackend.listPerspectiveTemplates(String(perspectiveState.cpd || ""))
        } else {
            embryosModel = sunTreeBackend.listEmbryos()
        }
        clipboardModel = sunTreeBackend.listClipboardEntries()
        filtersModel = sunTreeBackend.listFilters()
        parentModel = sunTreeBackend.listParents()
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
        for (var i = 0; i < embryosModel.length; i++) {
            var item = embryosModel[i]
            if (perspectiveState.active) {
                if (String((item && item.nodeType) ? item.nodeType : "") !== "dir") {
                    continue
                }
                rows.push({
                    kind: "template",
                    label: String((item && item.name) ? item.name : ""),
                    cpd: String((item && item.cpd) ? item.cpd : ""),
                    color: String((item && item.color) ? item.color : ""),
                    entry: item
                })
                continue
            }
            rows.push({
                kind: "template",
                label: String((item && item.name) ? item.name : ""),
                cpd: "",
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

    function currentTemplateRootName() {
        var fromState = String((perspectiveState && perspectiveState.templateRoot) ? perspectiveState.templateRoot : "").trim()
        if (fromState.length > 0) {
            return fromState
        }
        return "Standard"
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

    function parsePerspectiveCpd(cpd) {
        var raw = String(cpd || "").trim()
        var parts = raw.split("/").filter(function(p) { return p.length > 0 })
        var idx = -1
        for (var i = 0; i < parts.length; i++) {
            if (parts[i] === "Projekte") {
                idx = i
                break
            }
        }
        if (idx < 0 || idx + 1 >= parts.length) {
            return { valid: false, templateParts: [], projectName: "", tailParts: [] }
        }
        return {
            valid: true,
            templateParts: parts.slice(0, idx),
            projectName: String(parts[idx + 1] || ""),
            tailParts: parts.slice(idx + 2)
        }
    }

    function buildPerspectiveCpd(templateParts, projectName, tailParts) {
        var out = []
        for (var i = 0; i < templateParts.length; i++) out.push(String(templateParts[i]))
        out.push("Projekte")
        out.push(String(projectName || ""))
        for (var j = 0; j < tailParts.length; j++) out.push(String(tailParts[j]))
        return "/" + out.filter(function(p) { return p.length > 0 }).join("/")
    }

    function displayPathFromPerspectiveCpd(cpd) {
        var parsed = parsePerspectiveCpd(cpd)
        if (!parsed.valid) {
            return ""
        }
        var displayParts = ["Templates"].concat(parsed.templateParts).concat(parsed.tailParts)
        return "/" + displayParts.join("/") + "/"
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

    function sanitizeTailParts(parts) {
        var out = []
        for (var i = 0; i < (parts || []).length; i++) {
            var part = String(parts[i] || "").replace(/\//g, "").trim()
            if (part.length > 0) {
                out.push(part)
            }
        }
        return out
    }

    function tailPartsFromLeftRow(row) {
        if (row && String(row.cpd || "").length > 0) {
            var parsedCpd = parsePerspectiveCpd(String(row.cpd || ""))
            if (parsedCpd.valid) {
                return sanitizeTailParts(parsedCpd.templateParts.concat(parsedCpd.tailParts))
            }
        }
        var entryPath = String((row && row.entry && row.entry.path) ? row.entry.path : "")
        if (entryPath.length > 0) {
            var parsedPath = parseApdFromPath(entryPath)
            if (parsedPath.valid) {
                return sanitizeTailParts(parsedPath.tailParts)
            }
        }
        var label = String((row && row.label) ? row.label : "").replace(/\//g, "").trim()
        if (label.length > 0) {
            return [label]
        }
        return []
    }

    function _isPrefixParts(prefix, full) {
        if ((prefix || []).length > (full || []).length) {
            return false
        }
        for (var i = 0; i < prefix.length; i++) {
            if (String(prefix[i] || "") !== String(full[i] || "")) {
                return false
            }
        }
        return true
    }

    function derivePerspectiveTailForLeftDoubleClick(row) {
        var parsedState = parsePerspectiveCpd(String((perspectiveState && perspectiveState.cpd) ? perspectiveState.cpd : ""))
        var baseTail = parsedState.valid ? sanitizeTailParts(parsedState.templateParts.concat(parsedState.tailParts)) : []
        var parsedRow = parsePerspectiveCpd(String((row && row.cpd) ? row.cpd : ""))
        if (parsedRow.valid) {
            var rowTail = sanitizeTailParts(parsedRow.templateParts.concat(parsedRow.tailParts))
            // Accept resolver-provided CPD only when it extends current CPD tail.
            if (_isPrefixParts(baseTail, rowTail) && rowTail.length >= baseTail.length) {
                return rowTail
            }
        }
        var label = String((row && row.label) ? row.label : "").replace(/\//g, "").trim()
        if (label.length === 0) {
            return baseTail
        }
        return baseTail.concat([label])
    }

    function buildRealPathFromApdAndTail(apd, tailParts) {
        if (!apd || !apd.valid) {
            return ""
        }
        var cleanTail = sanitizeTailParts(tailParts)
        var allParts = []
        for (var i = 0; i < apd.apdParts.length; i++) {
            allParts.push(String(apd.apdParts[i] || ""))
        }
        for (var j = 0; j < cleanTail.length; j++) {
            allParts.push(cleanTail[j])
        }
        return "/" + allParts.filter(function(p) { return p.length > 0 }).join("/")
    }

    function buildCpdFromApdAndTail(apd, tailParts) {
        if (!apd || !apd.valid) {
            return ""
        }
        return buildPerspectiveCpd(sanitizeTailParts(tailParts), String(apd.projectName || ""), [])
    }

    function ensurePerspectiveOpenFromCwd() {
        if (perspectiveState.active) {
            return true
        }
        var opened = sunTreeBackend.openPerspective(String(sunTreeBackend.cwd() || ""))
        console.log("[SunTree] openPerspective from left dblclick", JSON.stringify(opened))
        syncPerspectiveState()
        if (!perspectiveState.active) {
            console.warn("[SunTree] perspective open failed from current CWD", String(sunTreeBackend.cwd() || ""))
            return false
        }
        return true
    }

    function applyLeftClick(index) {
        var rows = leftEntries()
        if (!(index >= 0 && index < rows.length)) {
            return
        }
        var row = rows[index]
        var apd = parseApdFromPath(String(sunTreeBackend.cwd() || ""))
        if (!apd.valid) {
            console.warn("[SunTree] left click missing APD in CWD", String(sunTreeBackend.cwd() || ""))
            return
        }
        var tail = tailPartsFromLeftRow(row)
        var targetReal = buildRealPathFromApdAndTail(apd, tail)
        console.log("[SunTree] left click -> CWD", JSON.stringify({ apdPath: apd.apdPath, tail: tail, targetReal: targetReal }))
        if (targetReal.length > 0) {
            sunTreeBackend.enterFolder(targetReal)
        }
    }

    function applyLeftDoubleClick(index) {
        var rows = leftEntries()
        if (!(index >= 0 && index < rows.length)) {
            return
        }
        if (!ensurePerspectiveOpenFromCwd()) {
            return
        }
        var row = rows[index]
        var apd = parseApdFromPath(String(sunTreeBackend.cwd() || ""))
        if (!apd.valid) {
            console.warn("[SunTree] left dblclick missing APD in CWD", String(sunTreeBackend.cwd() || ""))
            return
        }
        var tail = perspectiveState.active
                   ? derivePerspectiveTailForLeftDoubleClick(row)
                   : tailPartsFromLeftRow(row)
        var targetCpd = buildCpdFromApdAndTail(apd, tail)
        console.log("[SunTree] left dblclick -> CPD", JSON.stringify({ projectName: apd.projectName, tail: tail, targetCpd: targetCpd }))
        if (targetCpd.length === 0) {
            console.warn("[SunTree] left dblclick no target CPD", index, JSON.stringify(row))
            return
        }
        var setRes = sunTreeBackend.setPerspectiveCpd(targetCpd)
        console.log("[SunTree] setPerspectiveCpd result", JSON.stringify(setRes))
        if (!setRes || !setRes.ok) {
            console.warn("[SunTree] setPerspectiveCpd failed", targetCpd, JSON.stringify(setRes || {}))
            return
        }
        syncPerspectiveState()
        cpdLabel = String((row && row.label) ? row.label : "")
        selectedLeftIndex = index
        refreshModels()
        leftSectorCanvas.requestPaint()
    }

    function syncPerspectiveState() {
        var next = sunTreeBackend.getPerspectiveState() || ({ active: false, cpd: "" })
        var nextActive = !!next.active
        var nextCpd = String(next.cpd || "")
        var changed = (nextActive !== lastSyncedPerspectiveActive) || (nextCpd !== lastSyncedPerspectiveCpd)
        perspectiveState = next
        var rendered = next.active ? displayPathFromPerspectiveCpd(next.cpd) : ""
        cpdPath = rendered.length > 0 ? rendered : String(next.active ? (next.cpd || "") : "")
        if (changed) {
            lastSyncedPerspectiveActive = nextActive
            lastSyncedPerspectiveCpd = nextCpd
            embryosModel = nextActive
                          ? sunTreeBackend.listPerspectiveTemplates(nextCpd)
                          : sunTreeBackend.listEmbryos()
            leftSectorCanvas.requestPaint()
        }
    }

    function cpdStackEntries() {
        var parsed = parsePerspectiveCpd(String((perspectiveState && perspectiveState.cpd) ? perspectiveState.cpd : ""))
        if (!parsed.valid) {
            return []
        }
        var templateRootName = currentTemplateRootName()
        var normalizedTemplateParts = parsed.templateParts.slice(0)
        var cpdTemplatePrefix = []
        if (normalizedTemplateParts.length > 0 && String(normalizedTemplateParts[0] || "") === templateRootName) {
            cpdTemplatePrefix = [templateRootName]
            normalizedTemplateParts = normalizedTemplateParts.slice(1)
        }
        var displayParts = ["Templates", templateRootName].concat(normalizedTemplateParts).concat(parsed.tailParts)
        var out = []
        var templateLen = normalizedTemplateParts.length
        for (var i = 0; i < displayParts.length; i++) {
            var nextTemplate = []
            var nextTail = []
            if (i === 0) {
                nextTemplate = []
                nextTail = []
            } else if (i === 1) {
                nextTemplate = cpdTemplatePrefix.slice(0)
                nextTail = []
            } else if (i <= (templateLen + 1)) {
                nextTemplate = cpdTemplatePrefix.concat(normalizedTemplateParts.slice(0, i - 1))
                nextTail = []
            } else {
                nextTemplate = cpdTemplatePrefix.concat(normalizedTemplateParts.slice(0))
                var tailCount = i - (templateLen + 1)
                nextTail = parsed.tailParts.slice(0, tailCount)
            }
            out.push({
                label: i === 0 ? "Perspective OFF" : ("/" + displayParts[i] + "/"),
                cpd: buildPerspectiveCpd(nextTemplate, parsed.projectName, nextTail)
            })
        }
        return out
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

    Timer {
        id: leftClickDelayTimer
        interval: 170
        repeat: false
        onTriggered: {
            var idx = pendingLeftClickIndex
            leftEventSeq += 1
            console.log("[SunTree][L-Event#" + leftEventSeq + "] timer triggered", JSON.stringify({
                hoveredLeftIndex: hoveredLeftIndex,
                pendingLeftClickIndex: pendingLeftClickIndex,
                resolvedIndex: idx,
                rowsLen: leftEntries().length,
                ts: Date.now()
            }))
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
                                var selected = (selectedLeftIndex === i)
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
                        onPressed: function(mouse) {
                            leftEventSeq += 1
                            console.log("[SunTree][L-Event#" + leftEventSeq + "] pressed", JSON.stringify({
                                x: mouse.x,
                                y: mouse.y,
                                hoveredLeftIndex: hoveredLeftIndex,
                                pendingLeftClickIndex: pendingLeftClickIndex,
                                rowsLen: leftEntries().length,
                                ts: Date.now()
                            }))
                        }
                        onReleased: function(mouse) {
                            leftEventSeq += 1
                            console.log("[SunTree][L-Event#" + leftEventSeq + "] released", JSON.stringify({
                                x: mouse.x,
                                y: mouse.y,
                                hoveredLeftIndex: hoveredLeftIndex,
                                pendingLeftClickIndex: pendingLeftClickIndex,
                                rowsLen: leftEntries().length,
                                ts: Date.now()
                            }))
                        }
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
                            leftEventSeq += 1
                            console.log("[SunTree][L-Event#" + leftEventSeq + "] clicked", JSON.stringify({
                                hoveredLeftIndex: hoveredLeftIndex,
                                pendingLeftClickIndex: pendingLeftClickIndex,
                                rowsLen: leftEntries().length,
                                ts: Date.now()
                            }))
                            pendingLeftClickIndex = hoveredLeftIndex
                            leftClickDelayTimer.restart()
                        }
                        onDoubleClicked: {
                            leftEventSeq += 1
                            console.log("[SunTree][L-Event#" + leftEventSeq + "] doubleclicked", JSON.stringify({
                                hoveredLeftIndex: hoveredLeftIndex,
                                pendingLeftClickIndex: pendingLeftClickIndex,
                                rowsLen: leftEntries().length,
                                ts: Date.now()
                            }))
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
                                if (full.length > 0) {
                                    sunTreeBackend.enterFolder(full)
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: cpdStack
                    x: layoutRoot.stackX
                    y: layoutRoot.shellTop + 10
                    width: layoutRoot.stackWidth
                    height: Math.max(80, layoutRoot.cwdY - y - 10)
                    radius: 10
                    color: "#1a2d35"
                    border.width: 0
                    visible: perspectiveState.active

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        onExited: hoveredCpdIndex = -1
                    }

                    Flickable {
                        anchors.fill: parent
                        anchors.margins: 8
                        contentHeight: Math.max(cpdColumn.implicitHeight, height)
                        clip: true

                        Column {
                            id: cpdColumn
                            y: Math.max(0, parent.height - implicitHeight)
                            width: parent.width
                            spacing: 6

                            Repeater {
                                id: cpdRepeater
                                model: cpdStackEntries()
                                delegate: Rectangle {
                                    property var rowData: modelData
                                    width: parent.width
                                    height: 30
                                    radius: 7
                                    color: "#355767"
                                    border.width: (index === 0 || index === (cpdRepeater.count - 1)) ? 1 : 0
                                    border.color: "#8cb8c4"

                                    Text {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        verticalAlignment: Text.AlignVCenter
                                        text: String((rowData && rowData.label) ? rowData.label : "")
                                        color: "#e4f6fb"
                                        font.pixelSize: 12
                                        elide: Text.ElideRight
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onEntered: hoveredCpdIndex = index
                                        onExited: if (hoveredCpdIndex === index) hoveredCpdIndex = -1
                                        onClicked: {
                                            if (index === 0) {
                                                // "Perspective OFF" should disable perspective mode entirely.
                                                sunTreeBackend.clearPerspective()
                                                sunTreeBackend.refreshAll()
                                                return
                                            }
                                            var targetCpd = String((rowData && rowData.cpd) ? rowData.cpd : "")
                                            if (targetCpd.length > 0) {
                                                sunTreeBackend.setPerspectiveCpd(targetCpd)
                                                // Trigger the normal backend->UI refresh path.
                                                sunTreeBackend.refreshAll()
                                            }
                                        }
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
                                            var target = String((rowData && rowData.path) ? rowData.path : "")
                                            if (target.length > 0) {
                                                sunTreeBackend.setCwd(target)
                                            }
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
                    visible: hoveredCpdIndex >= 0
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
