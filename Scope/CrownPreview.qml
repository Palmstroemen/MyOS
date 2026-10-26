import QtQuick 2.15
import "../SunTree/js/Crown.js" as Crown

// A small SunTree crown for the SunTree tab of Scope's back (Scope/Designdocument Setup.md):
// one half with sample folders, drawn with SunTree's own arithmetic, and softly glowing lines
// where the values put their borders. One plays with it oneself: the hand over it moves the
// pointer as in SunTree, and the fan follows with the softness set. A new value plays nothing;
// over a slider its demo plays (demo: the setting's name) - the pointer goes where the value
// counts and its line pulses, the fan breathes around the magnifier, the pointer wiggles as
// softly as set - until the slider is taken (demo "").
Item {
    id: root
    property real lineT: 0.7
    property real inner: 0.2
    property real enter: 0.75
    property real leave: 0.25
    property real lens: 2.2
    property real softness: 10
    property real edge: 0.08
    property bool darkTheme: true

    // The colours of the lines; the sliders show the same as their marks.
    readonly property color innerColor: "#9aa7bd"
    readonly property color lineColor: "#f2b84b"
    readonly property color enterColor: "#4fd6e6"
    readonly property color leaveColor: "#e66fd8"
    readonly property color exitColor: "#7ee08a"

    // Where the hand puts the crown (target) and where the springs show it (shown).
    property real targetS: 0
    property real targetU: 2.0
    property real shownS: 0
    property real shownU: 2.0
    property string demo: ""  // inner, leave, lineT, enter, lens, softness, edge, or none
    readonly property string highlight: ["inner", "leave", "lineT", "enter", "edge"].indexOf(demo) >= 0 ? demo : ""
    readonly property bool playing: demo !== ""
    property real breath: 0  // -1 .. 1 while the fan breathes around the magnifier
    property real pulse: 0   // 0 .. 1 while a line pulses
    // The hand itself as a ring, while one plays with the fan or softness is shown: the fan
    // (the filled pointer) follows it as softly as set.
    property bool handOver: false
    readonly property bool handShown: handOver || demo === "softness"
    readonly property real shownLens: demo === "lens" ? Math.max(0, lens + Math.max(0.8, 0.5 * lens) * breath) : lens

    // Half of the stem on the left, so one sees at once what this is: the centre of the
    // half is where the CWD oval's round end has its centre, as in SunTree.
    readonly property real cx: 34
    readonly property real cy: height / 2
    readonly property real radius: Math.max(20, Math.min(width - cx - 6, height / 2 - 10))

    function stemShape() {
        return { width: cx, ovalRadius: 0.12 * radius }
    }

    function geo() {
        return { ri: inner * radius, T: lineT * radius, R: radius, lens: shownLens, speed: 1,
                 enter: enter, leave: leave }
    }

    /// Where the lines are (from the centre): the hollow, the line T, the field's edge when
    /// drawing in begins (enter), where it ends and the next level starts (leave); exit is
    /// how far the rim runs on past the first and last folder.
    function guides() {
        var g = geo()
        return { R: g.R, inner: g.ri, line: g.T, enter: Crown.fieldEnd(g), leave: Crown.levelStart(g),
                 exit: edge * g.R }
    }

    // Sample folders: four, each with three, each with three again.
    readonly property var names: [["Aufträge", "Belege", "Rechnungen", "Team"], ["A", "B", "C"], ["1", "2", "3"]]
    function childrenOf(way) {
        var level = names[Math.min(way.length, names.length - 1)]
        var out = []
        for (var i = 0; i < level.length; i++) out.push({ label: level[i] })
        return out
    }

    /// The hand at (x, y): from the hollow out to the rim it dives through a level and a half
    /// (the small fan has no room for more); up and down it picks the folder.
    function handAt(x, y) {
        var lx = x - cx, ly = y - cy
        if (lx < 0) return false
        var g = geo(), r = Math.sqrt(lx * lx + ly * ly), th = Math.atan2(ly, lx) * 180 / Math.PI
        var deepest = g.ri + 2.6 * (g.T - g.ri)
        targetS = r <= g.ri ? r : g.ri + (Math.min(r, g.R) - g.ri) / (g.R - g.ri) * (deepest - g.ri)
        targetU = Math.max(0, Math.min(3.999, (th + 90) / 180 * 4))
        handOver = true
        spring.start()
        return true
    }

    function handGone() {
        handOver = false
        targetS = 0
        spring.start()
    }

    function pointerRadius() {
        return Crown.pointer(demoState(), geo(), function(way) { return childrenOf(way).length }).r
    }

    /// Over a slider: the pointer goes where its value counts.
    onDemoChanged: {
        var g = geo(), D = g.T - g.ri
        if (demo === "inner") { targetS = g.ri; targetU = 2.0 }
        else if (demo === "leave") { targetS = g.T + D; targetU = 1.5 }        // the next level starts
        else if (demo === "lineT" || demo === "enter") { targetS = g.T - 0.01; targetU = 1.5 }  // drawing in begins
        else if (demo === "lens") { targetS = g.ri + 2; targetU = 1.5 }        // a level's start
        else if (demo === "softness") { targetS = g.ri + 0.4 * D }
        else if (demo === "edge") { targetS = g.ri + 0.3 * D; targetU = 0.02 } // at the first folder
        else { targetS = 0; targetU = 2.0 }
        spring.start()
        canvas.requestPaint()
    }

    function demoState() {
        var g = geo()
        var drawnIn = shownS >= g.T
        return { s: shownS, u: [shownU, 1.5, 1.5], lock: drawnIn ? [Math.floor(Math.max(0, Math.min(3.999, shownU)))] : [],
                 released: false }
    }

    onLineTChanged: canvas.requestPaint()
    onInnerChanged: canvas.requestPaint()
    onEnterChanged: canvas.requestPaint()
    onLeaveChanged: canvas.requestPaint()
    onEdgeChanged: canvas.requestPaint()
    onShownLensChanged: canvas.requestPaint()
    onPulseChanged: canvas.requestPaint()
    onTargetUChanged: if (handShown) canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    Timer {
        // The springs, at the softness set: as SunTree follows the hand.
        id: spring
        interval: 16
        repeat: true
        onTriggered: {
            var k = 1 - Math.exp(-0.016 * root.softness)
            root.shownS += (root.targetS - root.shownS) * k
            root.shownU += (root.targetU - root.shownU) * k
            canvas.requestPaint()
            if (Math.abs(root.targetS - root.shownS) < 0.2 && Math.abs(root.targetU - root.shownU) < 0.002 && !wiggle.running) stop()
        }
    }

    SequentialAnimation on breath {
        // The fan opening and closing around the magnifier set.
        running: root.demo === "lens"
        loops: Animation.Infinite
        NumberAnimation { to: 1; duration: 700; easing.type: Easing.InOutSine }
        NumberAnimation { to: -1; duration: 1400; easing.type: Easing.InOutSine }
        NumberAnimation { to: 0; duration: 700; easing.type: Easing.InOutSine }
        onRunningChanged: if (!running) root.breath = 0
    }

    SequentialAnimation on pulse {
        running: root.highlight !== ""
        loops: Animation.Infinite
        NumberAnimation { to: 1; duration: 600; easing.type: Easing.InOutSine }
        NumberAnimation { to: 0; duration: 600; easing.type: Easing.InOutSine }
        onRunningChanged: if (!running) root.pulse = 0
    }

    SequentialAnimation on targetU {
        // The hand glides up and down; the fan follows as softly as set - far behind and not
        // to the ends when soft, close to the hand when direct.
        id: wiggle
        running: root.demo === "softness"
        loops: Animation.Infinite
        NumberAnimation { to: 3.6; duration: 650; easing.type: Easing.InOutSine }
        NumberAnimation { to: 0.4; duration: 650; easing.type: Easing.InOutSine }
        onRunningChanged: if (running) spring.start()
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onPositionChanged: function(mouse) { root.handAt(mouse.x, mouse.y) }
        onExited: root.handGone()
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        function sector(ctx, r0, r1, a0, a1) {
            ctx.beginPath()
            ctx.arc(root.cx, root.cy, r1, a0 * Math.PI / 180, a1 * Math.PI / 180, false)
            ctx.arc(root.cx, root.cy, r0, a1 * Math.PI / 180, a0 * Math.PI / 180, true)
            ctx.closePath()
        }

        function glowLine(ctx, r, color, lit) {
            var widths = [[9, 0.10], [6, 0.18], [3, 0.35], [1.5, 1.0]]
            var grow = lit ? 1 + 1.2 * root.pulse : 1
            for (var i = 0; i < widths.length; i++) {
                ctx.beginPath()
                ctx.arc(root.cx, root.cy, r, -Math.PI / 2, Math.PI / 2, false)
                ctx.lineWidth = widths[i][0] * grow
                ctx.globalAlpha = Math.min(1, widths[i][1] * grow)
                ctx.strokeStyle = color
                ctx.stroke()
            }
            ctx.globalAlpha = 1
        }

        function paintStem(ctx, g) {
            var stem = root.stemShape()
            ctx.fillStyle = root.darkTheme ? "#20283a" : "#c9d0e0"
            ctx.fillRect(0, root.cy - g.R, stem.width, 2 * g.R)
        }

        // Over the crown, as in SunTree: the oval's round end lies in the hollow.
        function paintOval(ctx, g) {
            var stem = root.stemShape(), h = stem.ovalRadius
            ctx.beginPath()  // the CWD oval, its round end around the centre of the half
            ctx.moveTo(0, root.cy - h)
            ctx.lineTo(root.cx, root.cy - h)
            ctx.arc(root.cx, root.cy, h, -Math.PI / 2, Math.PI / 2, false)
            ctx.lineTo(0, root.cy + h)
            ctx.closePath()
            ctx.fillStyle = "#2f3d60"
            ctx.fill()
            ctx.lineWidth = 1.5
            ctx.strokeStyle = "#9cb7f0"
            ctx.stroke()
            ctx.fillStyle = "#324663"  // two parents below it
            for (var i = 0; i < 2; i++) ctx.fillRect(4, root.cy + h + 6 + i * (0.09 * g.R + 4), stem.width - 8, 0.09 * g.R)
        }

        // The rim running on past the first and last folder, towards the stem: so far one
        // pushes on until the fan lets go.
        function glowExit(ctx, r, angle, lit) {
            var widths = [[9, 0.10], [6, 0.18], [3, 0.35], [2, 1.0]]
            var grow = lit ? 1 + 1.2 * root.pulse : 1
            for (var i = 0; i < widths.length; i++) {
                ctx.lineWidth = widths[i][0] * grow
                ctx.globalAlpha = Math.min(1, widths[i][1] * grow)
                ctx.strokeStyle = root.exitColor
                ctx.beginPath()
                ctx.arc(root.cx, root.cy, r, -Math.PI / 2 - angle, -Math.PI / 2, false)
                ctx.stroke()
                ctx.beginPath()
                ctx.arc(root.cx, root.cy, r, Math.PI / 2, Math.PI / 2 + angle, false)
                ctx.stroke()
            }
            ctx.globalAlpha = 1
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var g = root.geo()
            paintStem(ctx, g)
            sector(ctx, 0, g.R + 4, -90, 90)
            ctx.fillStyle = root.darkTheme ? "#2d3750" : "#d8deec"
            ctx.fill()
            var rings = Crown.layout(root.demoState(), g, root.childrenOf)
            var tones = ["#4e668f", "#5b7aa8", "#6a8bbb"]
            for (var r = 0; r < rings.length; r++) {
                var ring = rings[r], a = ring.start
                for (var i = 0; i < ring.items.length; i++) {
                    var a0 = a, a1 = a + ring.sp[i]
                    a = a1
                    if (a1 - a0 < 0.05) continue
                    ctx.globalAlpha = ring.alpha
                    sector(ctx, ring.r0, ring.r1, a0, a1)
                    ctx.fillStyle = Qt.lighter(tones[(i + r) % tones.length], ring.kind === "field" && i === ring.hi ? 1.25 : 1.0)
                    ctx.fill()
                    ctx.lineWidth = 1
                    ctx.strokeStyle = "rgba(15,17,23,0.9)"
                    ctx.stroke()
                }
            }
            ctx.globalAlpha = 1
            paintOval(ctx, g)
            var lines = root.guides()
            glowLine(ctx, lines.inner, root.innerColor, root.highlight === "inner")
            glowLine(ctx, lines.line, root.lineColor, root.highlight === "lineT")
            glowLine(ctx, lines.enter, root.enterColor, root.highlight === "enter")
            glowLine(ctx, lines.leave, root.leaveColor, root.highlight === "leave")
            glowExit(ctx, g.R, lines.exit / g.R, root.highlight === "edge")
            if (root.handShown) {
                var target = { s: root.targetS, u: [root.targetU, 1.5, 1.5], released: false,
                               lock: root.targetS >= g.T ? [Math.floor(Math.max(0, Math.min(3.999, root.targetU)))] : [] }
                var h = Crown.pointer(target, g, function(way) { return root.childrenOf(way).length })
                var ht = h.th * Math.PI / 180
                ctx.beginPath()
                ctx.arc(root.cx + h.r * Math.cos(ht), root.cy + h.r * Math.sin(ht), 8, 0, 2 * Math.PI)
                ctx.lineWidth = 2
                ctx.strokeStyle = "rgba(255,255,255,0.75)"
                ctx.stroke()
            }
            var p = Crown.pointer(root.demoState(), g, function(way) { return root.childrenOf(way).length })
            var t = p.th * Math.PI / 180
            ctx.beginPath()
            ctx.arc(root.cx + p.r * Math.cos(t), root.cy + p.r * Math.sin(t), 5, 0, 2 * Math.PI)
            ctx.fillStyle = "#ffffff"
            ctx.fill()
            ctx.lineWidth = 2
            ctx.strokeStyle = "#0f1117"
            ctx.stroke()
        }
    }
}
