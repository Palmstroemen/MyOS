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
    property int hoveredLeftIndex: -1
    property int hoveredRightIndex: -1
    property int hoveredCenterIndex: -1
    property int hoveredTopIndex: -1
    property int selectedLeftIndex: -1

    function refreshModels() {
        foldersModel = sunTreeBackend.listFolders()
        embryosModel = sunTreeBackend.listEmbryos()
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
            rows.push({
                kind: "template",
                label: String((embryosModel[i] && embryosModel[i].name) ? embryosModel[i].name : ""),
                entry: embryosModel[i]
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
                entry: foldersModel[i]
            })
        }
        return rows
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
                path: path
            })
        }
        return out
    }

    function templateRelativePathFor(label) {
        var leaf = String(label || "").trim()
        if (leaf.length === 0) {
            return ""
        }
        var rootName = String(selectedFilterName || "").trim()
        if (rootName.length === 0) {
            rootName = "Standard"
        }
        return "/Templates/" + rootName + "/" + leaf + "/"
    }

    function appendToCpdPath(label) {
        var leaf = String(label || "").trim().replace(/\//g, "")
        if (leaf.length === 0) {
            return cpdPath
        }
        var base = String(cpdPath || "")
        if (base.length === 0) {
            return templateRelativePathFor(leaf)
        }
        var parts = base.split("/").filter(function(p) { return p.length > 0 })
        if (parts.length === 0) {
            return templateRelativePathFor(leaf)
        }
        if (String(parts[parts.length - 1]).toLowerCase() !== leaf.toLowerCase()) {
            parts.push(leaf)
        }
        return "/" + parts.join("/") + "/"
    }

    function cpdStackEntries() {
        var raw = String(cpdPath || "")
        if (raw.length === 0) {
            return []
        }
        var parts = raw.split("/").filter(function(p) { return p.length > 0 })
        var out = []
        for (var i = 0; i < parts.length; i++) {
            out.push({ label: "/" + parts[i] + "/" })
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
                        border.width: 2
                        border.color: "#4e8b9a"
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
                                ctx.beginPath()
                                ctx.arc(cx, cy, layoutRoot.halfOuterRadius, a0, a1, false)
                                ctx.arc(cx, cy, layoutRoot.halfInnerRadius, a1, a0, true)
                                ctx.closePath()
                                ctx.fillStyle = selected ? "#4d7f8d" : (hovered ? "#5d95a6" : "#3b6b7d")
                                ctx.fill()
                                ctx.strokeStyle = selected ? "#d3f3ff" : (hovered ? "#c5ebff" : "#7ea8b4")
                                ctx.lineWidth = 1
                                ctx.stroke()
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
                        onDoubleClicked: {
                            var rows = leftEntries()
                            if (hoveredLeftIndex >= 0 && hoveredLeftIndex < rows.length) {
                                var label = String((rows[hoveredLeftIndex] && rows[hoveredLeftIndex].label) ? rows[hoveredLeftIndex].label : "")
                                var logical = appendToCpdPath(label)
                                if (logical.length > 0) {
                                    cpdPath = logical
                                    cpdLabel = label
                                    selectedLeftIndex = hoveredLeftIndex
                                    leftSectorCanvas.requestPaint()
                                }
                            }
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
                        border.width: 2
                        border.color: "#6d86ad"
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
                                ctx.beginPath()
                                ctx.arc(cx, cy, layoutRoot.halfOuterRadius, a0, a1, false)
                                ctx.arc(cx, cy, layoutRoot.halfInnerRadius, a1, a0, true)
                                ctx.closePath()
                                ctx.fillStyle = hovered ? "#6f89b8" : "#4e668f"
                                ctx.fill()
                                ctx.strokeStyle = hovered ? "#d4e2ff" : "#90a8ce"
                                ctx.lineWidth = 1
                                ctx.stroke()
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
                    border.width: 1
                    border.color: "#4e8b9a"
                    visible: cpdPath.length > 0

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
                                model: cpdStackEntries()
                                delegate: Rectangle {
                                    property var rowData: modelData
                                    width: parent.width
                                    height: 30
                                    radius: 7
                                    color: "#355767"
                                    border.width: 1
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
                    border.width: 1
                    border.color: "#4b5f86"

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
                                    color: hoveredCenterIndex === index ? "#546c97" : "#324663"
                                    border.width: 1
                                    border.color: hoveredCenterIndex === index ? "#c0d6ff" : "#6d82a8"

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
                    color: "#2f3d60"
                    border.width: 2
                    border.color: "#9cb7f0"

                    Column {
                        anchors.centerIn: parent
                        spacing: 2
                        width: parent.width - 24

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "CWD"
                            color: "#dbe5ff"
                            font.bold: true
                            font.pixelSize: 13
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: sunTreeBackend.refreshAll()
                    }
                }
            }
        }
    }
}
