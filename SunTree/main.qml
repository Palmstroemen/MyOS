import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Effects
import "js/Crown.js" as Crown

ApplicationWindow {
    id: root
    width: 1180
    height: 780
    visible: !sunTreeStartHidden
    title: "SunTree"
    color: "transparent"  // only the crown and the stem are drawn
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint

    property var foldersModel: []
    property var embryosModel: []
    property real embryoOpacity: 0.4  // as in Scope; the setting is read on appearing
    property var clipboardModel: []
    property var parentModel: []
    property int hoveredFrameIndex: -1
    property var pendingLeftRow: null
    property string cwdPath: ""  // where one stands, shared with Scope: it glows
    property string ctdPath: ""  // what SunTree shows in its middle: looking around moves it
    property string cwdGlow: "#ffffff"  // the CWD's project colour, lit up
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
        ctdPath = String(sunTreeBackend.ctd() || "")
        foldersModel = sunTreeBackend.listFolders()
        currentProjectColor = String(sunTreeBackend.effectiveProjectColor(ctdPath) || "")
        var own = String(sunTreeBackend.effectiveProjectColor(cwdPath) || "")
        cwdGlow = own ? (_adjustColor(own, 1.7) || "#ffffff") : "#ffffff"
        var reply = sunTreeBackend.lens("state", {})
        lensState = (reply && reply.ok) ? reply.result : ({ active: false })
        embryosModel = sunTreeBackend.listEmbryosAt(leftListingPath())
        clipboardModel = sunTreeBackend.listClipboardEntries()
        parentModel = sunTreeBackend.listParents()
        crownCache = ({})
        if (typeof crownCanvas !== "undefined") crownCanvas.requestPaint()
    }

    /// The left half: the MyOS folders of the CTD; with a lens on, the lens' folder.
    function leftListingPath() {
        return lensInProject ? String(lensState.target || "") : ctdPath
    }

    /// Whether path is the CWD: it glows wherever it shows (oval, stem, crown).
    function isCwd(path) {
        return String(path || "").replace(/\/+$/, "") === cwdPath.replace(/\/+$/, "")
    }

    /// Ask the session (look_at, move_to, take_off, ...) and show the lens afterwards.
    function lensRequest(method, params) {
        var reply = sunTreeBackend.lens(method, params || ({}))
        if (!reply || !reply.ok) {
            console.log("lens", method, "failed:", reply ? reply.error : "no reply")
            return false
        }
        refreshModels()
        return true
    }

    /// A MyOS folder (born or embryo): a double click on it puts on its lens.
    function isMyosFolder(entry) {
        if (entry && entry.folderType !== undefined && !isNaN(Number(entry.folderType))) {
            return Number(entry.folderType) > 0
        }
        return !!(entry && entry.isEmbryo === true)
    }

    /// Go to path: with a lens on, the lens goes along, keeping its depth - into the project
    /// there (a folder inside one: its project), or onto the shelf of a folder of projects.
    /// It stays on until taken off (✕), also outside the projects (Scope's projects row).
    function navigateTo(path) {
        var target = String(path || "")
        if (target.length === 0) return
        if (lensOn) sunTreeBackend.lens("move_to", { "path": target })
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
        putAway()
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
        if (pointerGliding) return  // on its way: SunTree shows when it is there
        if (visible) {
            putAway()
            return
        }
        turnedTo()  // the loading first, while the pointer stands: then nothing holds up its ride
        sunTreeBackend.showCwd()  // it starts where one stands
        if (!appearUnderPointer()) showNow()
    }

    function showNow() {
        refreshBackdrop()  // before showing: what lies behind, not SunTree
        visible = true
        raise()
        requestActivate()
    }

    // One action, then gone (Designdocument Krone.md): a drop, a double click, the lens put
    // on or taken off put SunTree away; a single click only goes in, to look further.
    property real wentInAt: 0  // when a single click last went in: its double click goes away

    /// Cancelling, or an action done: SunTree goes away, and the pointer rides back where
    /// SunTree picked it up. True while it rides.
    /// It does not vanish at once: a snapshot of it blurs and fades out (fadeOut), meanwhile
    /// the pointer rides back.
    function putAway() {
        if (fading) return
        crownRelease(false)
        crownTimer.stop()  // the crown stands still for the snapshot
        fadeOut()
        var back = pickedUpAt
        pickedUpAt = null
        if (!back) return
        ridingBack = true
        sunTreeBackend.glidePointerTo(back.x, back.y, 350)
    }

    property bool fading: false
    property real fadeProgress: 0  // 0: whole, 1: blurred away
    property bool ridingBack: false

    function fadeOut() {
        fadeSnapshot.scheduleUpdate()
        fading = true
        fadeAnimation.restart()
        fadeOpacity.restart()
        fadeScale.restart()
    }

    function fadeDone() {
        visible = false
        fading = false
        fadeProgress = 0
        crownReset()  // at rest for the next time
        maybeQuit()
    }

    /// Ctrl+Q: away as always, and SunTree ends once it has faded and the pointer is back.
    /// Otherwise it stays, ready for the shortcut (there is no exit button).
    property bool quitting: false
    function quitForGood() {
        quitting = true
        putAway()
    }

    function maybeQuit() {
        if (quitting && !fading && !ridingBack) Qt.quit()
    }

    /// Whether (x, y) in the main area is on the crown (either half, its hollow included) or
    /// on the stem between them.
    function onCrown(x, y) {
        for (var side = -1; side <= 1; side += 2) {
            var p = crownPolar(side, x, y)
            if (p.lx >= 0 && p.r <= crownGeo(side).R) return true
        }
        var l = crownGeo(-1), r = crownGeo(1)
        return x >= l.cx && x <= r.cx && y >= layoutRoot.shellTop && y <= layoutRoot.shellBottom
    }

    /// The CWD oval in the main area: centre, width, height (its round ends: radius h / 2).
    function cwdOval() {
        return { cx: layoutRoot.centerX, cy: layoutRoot.cwdY + layoutRoot.cwdHeight / 2,
                 w: layoutRoot.cwdWidth, h: layoutRoot.cwdHeight }
    }

    /// The middle of the stem (the CWD) in the window.
    function stemCentre() {
        var o = mainAreaOrigin()
        return { x: o.x + layoutRoot.centerX, y: o.y + layoutRoot.cwdY + layoutRoot.cwdHeight / 2 }
    }

    function mainAreaOrigin() {
        return { x: layoutRoot.x + mainArea.x, y: layoutRoot.y + mainArea.y }
    }

    /// The stem under the pointer, the window whole on its screen: where the edge pushes it
    /// aside, the pointer rides into the middle of the stem (as the crown pulls it anyway) and
    /// SunTree shows when it is there - showing would hold the ride up, and the eye should
    /// follow it. True while it rides.
    function appearUnderPointer() {
        var at = sunTreeBackend.pointerAt()
        pickedUpAt = { x: at.x, y: at.y }
        var stem = stemCentre()
        var x = at.x - stem.x, y = at.y - stem.y
        if (at.sw > 0) x = Math.max(at.sx, Math.min(x, at.sx + at.sw - width))
        if (at.sh > 0) y = Math.max(at.sy, Math.min(y, at.sy + at.sh - height))
        root.x = Math.round(x)
        root.y = Math.round(y)
        crownReset()
        var o = mainAreaOrigin()
        crownPointer = { x: stem.x - o.x, y: stem.y - o.y }
        var put = { x: Math.round(root.x + stem.x), y: Math.round(root.y + stem.y) }
        if (put.x === at.x && put.y === at.y) return false
        pointerGliding = true
        sunTreeBackend.glidePointerTo(put.x, put.y, 350)
        return true
    }

    /// The stem's panel: a snapshot of what lies behind it, drawn blurred.
    function refreshBackdrop() {
        var at = stemPanel.mapToGlobal(0, 0)
        stemPanel.backdrop = sunTreeBackend.takeBackdrop(Math.round(at.x), Math.round(at.y),
                                                         Math.round(stemPanel.width), Math.round(stemPanel.height))
    }

    /// Scope and SunTree always share the place: turned to, go where Scope went.
    function turnedTo() {
        applyCrownSettings()
        sunTreeBackend.followPlace()
        sunTreeBackend.homeIfOutside()
        refreshModels()
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
        var base = String(sunTreeBackend.ctd() || "")
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

    /// An embryo (a MyOS folder not born here) is drawn pale, as in Scope.
    function leftRowOpacity(index) {
        var rows = leftEntries()
        var row = rows[index]
        return (row && row.entry && row.entry.isEmbryo === true) ? embryoOpacity : 1.0
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
        var cwd = String(ctdPath || "")
        var parts = cwd.split("/").filter(function(p) { return p.length > 0 })
        if (parts.length === 0) {
            return "/"
        }
        return String(parts[parts.length - 1] || "/")
    }

    function projectNameFromCwd() {
        var parsed = parseApdFromPath(String(ctdPath || ""))
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
        applyLeftRow(leftEntries()[index])
    }

    /// A single click on the left only looks (an embryo cannot be shown); the lens changes
    /// only by a double click or on its frame.
    function applyLeftRow(row) {
        if (!row || lensOn) return
        sunTreeBackend.showFolder(row.path)
    }

    /// A double click: on a MyOS folder it puts on its lens and the CWD stays; with a lens
    /// on it gets sharper, or another department's lens is put on (A3).
    function applyLeftDoubleClick(index) {
        applyLeftRowDouble(leftEntries()[index])
    }

    function applyLeftRowDouble(row) {
        if (!row) return
        if (lensOn || isMyosFolder(row.entry)) {
            lensRequest("look_at", { "path": row.path })
        } else {
            sunTreeBackend.enterFolder(row.path)
        }
    }

    // --- The crown (SunTree/Designdocument Krone.md) ------------------------------------
    // Moving outward a folder's field grows; beyond the line T it is drawn into the stem and
    // the pointer is pulled inward. Diving only shows: a click goes in, a drop puts the file
    // into the folder under the pointer. Crown.js does the arithmetic; here the hand moves
    // it, springs soften it and one canvas draws both halves and the stem.
    property real crownLineT: 0.7    // T as a share of R
    property real crownInner: 0.2    // ri as a share of R
    property real crownLens: 2.2     // the fish-eye at the start of a level
    property real crownSoftness: 10  // spring rate of the shown values, per second
    property real crownEdge: 0.08    // push past a level's end that lets go, as a share of R
    property real crownEnter: 0.75   // where in the field drawing in begins
    property real crownLeave: 0.25   // how far into the outer ring it ends
    // The values come from the settings (core/settings.py), set on the back of Scope.
    function applyCrownSettings() {
        var s = sunTreeBackend.crownSettings()
        if (!s) return
        crownLineT = s.lineT; crownInner = s.inner; crownEnter = s.enter; crownLeave = s.leave
        crownLens = s.lens; crownSoftness = s.softness; crownEdge = s.edge
        embryoOpacity = sunTreeBackend.embryoOpacitySetting()
        crownCache = ({})
    }
    // Per half (-1 left, 1 right): target (where the hand put it), shown (the springs) and
    // lensK (the fish-eye fading in and out).
    property var crownHalves: ({ "-1": { target: null, shown: null, lensK: 0 }, "1": { target: null, shown: null, lensK: 0 } })
    property int crownActive: 0      // the half holding the pointer, 0: none
    property int crownLetGo: 0       // the half that let go, until the hand has left it
    property bool pointerGliding: false  // riding to the stem before SunTree shows
    property var pickedUpAt: null        // where the pointer was when SunTree was called
    property var crownPointer: null  // where the pointer was last seen or put (main area)
    // The pointer put by the crown, until X reports the put back (the motion event it makes at
    // the put place, after any the hand made before it): [{x, y, at}]. Meanwhile motion
    // events are from before the put - only their steps from handBefore are the hand's.
    property var putsPending: []
    property var handBefore: null
    property var crownCache: ({})
    property var stemGlide: ({})     // shown y of the stem's entries, by path
    property var stemHits: []

    function crownGeo(side) {
        var R = layoutRoot.halfOuterRadius
        var h = crownHalves[side]
        return { ri: crownInner * R, T: crownLineT * R, R: R, lens: crownLens * (h ? h.lensK : 0), speed: 1,
                 edge: crownEdge * R, enter: crownEnter, leave: crownLeave,
                 cx: side < 0 ? leftHalf.x + leftHalf.width : rightHalf.x, cy: leftHalf.y + leftHalf.height / 2 }
    }

    /// The folders of a level of a half: way are folder indices from the CWD (left: from
    /// the lens' folder) down.
    function crownRows(side, way) {
        var key = side + "|" + way.join("/")
        if (crownCache[key]) return crownCache[key]
        var rows = []
        if (way.length === 0) {
            var base = side < 0 ? leftEntries() : rightEntries()
            for (var i = 0; i < base.length; i++) {
                rows.push({ label: base[i].label, path: side < 0 ? base[i].path : fullPathFromEntry(base[i].entry),
                            color: base[i].color, entry: base[i].entry })
            }
        } else {
            var parent = crownRows(side, way.slice(0, way.length - 1))[way[way.length - 1]]
            if (parent) {
                var list = side < 0 ? sunTreeBackend.listEmbryosAt(parent.path) : sunTreeBackend.listFoldersAt(parent.path)
                for (var j = 0; j < list.length; j++) {
                    var name = String(list[j].name || "")
                    rows.push({ label: name.split("/").pop(), color: String(list[j].color || ""), entry: list[j],
                                path: String(list[j].path || "") || parent.path.replace(/\/+$/, "") + "/" + name })
                }
            }
        }
        crownCache[key] = rows
        return rows
    }

    function crownCount(side) {
        return function(way) { return crownRows(side, way).length }
    }

    function crownPolar(side, x, y) {
        var g = crownGeo(side), lx = side * (x - g.cx), ly = y - g.cy
        return { r: Math.sqrt(lx * lx + ly * ly), th: Math.atan2(ly, lx) * 180 / Math.PI, lx: lx }
    }

    function crownToLocal(side, r, th) {
        var g = crownGeo(side), a = th * Math.PI / 180
        return { x: g.cx + side * r * Math.cos(a), y: g.cy + r * Math.sin(a) }
    }

    /// The hand moved the pointer to (x, y) in the main area: take a half, or dive in it.
    function handMoved(x, y) {
        if (fading) return  // the pointer rides back across it: no half takes it again
        var last = crownPointer || { x: x, y: y }
        var dx = x - last.x, dy = y - last.y
        crownPointer = { x: x, y: y }
        var now = Date.now()
        while (putsPending.length && now - putsPending[0].at > 200) putsPending.shift()  // no report came
        if (putsPending.length) {
            for (var i = 0; i < putsPending.length; i++) {
                var put = putsPending[i]
                if (Math.abs(x - put.x) <= 1 && Math.abs(y - put.y) <= 1) {
                    // X reports the put: from here on, motion is the hand's again.
                    putsPending = putsPending.slice(i + 1)
                    crownPointer = putsPending.length ? last : { x: put.x, y: put.y }
                    return
                }
            }
            // From before the put: the hand's step from where it was; the pointer stays put.
            dx = x - handBefore.x
            dy = y - handBefore.y
            handBefore = { x: x, y: y }
            crownPointer = last
        }
        if (crownActive === 0) {
            for (var side = -1; side <= 1; side += 2) {
                var g = crownGeo(side), p = crownPolar(side, x, y)
                var n = crownRows(side, []).length
                var inside = n > 0 && p.lx > 0 && p.r >= g.ri && p.r <= g.R && Math.abs(p.th) <= 90
                if (crownLetGo === side) {
                    if (inside) continue  // it let go here: not caught again at once
                    crownLetGo = 0
                }
                if (inside) {
                    var h = crownHalves[side]
                    h.target = Crown.start(p.r, p.th, n)
                    h.shown = { s: p.r, u: h.target.u.slice(), lock: [] }
                    crownActive = side
                    crownTimer.start()
                    return
                }
            }
            return
        }
        var half = crownHalves[crownActive], geo = crownGeo(crownActive), count = crownCount(crownActive)
        var a = Crown.pointer(half.target, geo, count).th * Math.PI / 180
        var lx = crownActive * dx, ly = dy
        var dr = lx * Math.cos(a) + ly * Math.sin(a), dt = -lx * Math.sin(a) + ly * Math.cos(a)
        var next = Crown.move(half.target, dr, dt, geo, count)
        if (next.released) {
            crownRelease(true)
            return
        }
        if (next.lock.join("/") !== half.target.lock.join("/")) {
            // A new folder drawn in: its subfolders start under the pointer, not swept to.
            half.shown.u[next.lock.length] = next.u[next.lock.length]
        }
        half.target = next
        crownTimer.start()
    }

    /// The half lets go: the crown runs back softly, the pointer is free. holdOff: the hand
    /// is still on the half (past a level's end, Esc), which takes it again only after the
    /// hand has left it.
    function crownRelease(holdOff) {
        if (crownActive === 0) return
        crownLetGo = holdOff ? crownActive : 0
        var h = crownHalves[crownActive]
        h.target = { s: 0, u: h.target.u, lock: h.target.lock, released: true }
        crownActive = 0
        crownTimer.start()
    }

    /// Back to rest at once (a new CWD: the folders changed).
    function crownReset() {
        crownActive = 0
        crownLetGo = 0
        crownHalves = ({ "-1": { target: null, shown: null, lensK: 0 }, "1": { target: null, shown: null, lensK: 0 } })
        crownCache = ({})
        crownCanvas.requestPaint()
    }

    function crownTick(dt) {
        var k = 1 - Math.exp(-dt * crownSoftness), moving = false
        for (var side = -1; side <= 1; side += 2) {
            var h = crownHalves[side]
            if (!h.target) continue
            var lensGoal = crownActive === side ? 1 : 0
            h.lensK += (lensGoal - h.lensK) * k
            if (Math.abs(lensGoal - h.lensK) > 0.01) moving = true
            var sh = h.shown
            sh.s += (h.target.s - sh.s) * k
            if (Math.abs(h.target.s - sh.s) > 0.3) moving = true
            for (var i = 0; i < h.target.u.length; i++) {
                if (sh.u[i] === undefined) { sh.u[i] = h.target.u[i]; continue }
                sh.u[i] += (h.target.u[i] - sh.u[i]) * k
                if (Math.abs(h.target.u[i] - sh.u[i]) > 0.002) moving = true
            }
            sh.lock = h.target.lock.slice()
            if (crownActive !== side && sh.s < crownGeo(side).ri && h.lensK < 0.02) {
                h.target = null; h.shown = null  // settled back
            }
        }
        if (crownActive !== 0) {
            // The pointer is where the crown draws it: pulled inward beyond the line.
            var half = crownHalves[crownActive]
            var p = Crown.pointer(half.shown, crownGeo(crownActive), crownCount(crownActive))
            var at = crownToLocal(crownActive, p.r, p.th)
            if (!crownPointer || Math.abs(at.x - crownPointer.x) > 0.5 || Math.abs(at.y - crownPointer.y) > 0.5) {
                var g = mainArea.mapToGlobal(at.x, at.y)
                sunTreeBackend.pointerTo(Math.round(g.x), Math.round(g.y))
                if (!putsPending.length) handBefore = crownPointer || at
                putsPending = putsPending.concat([{ x: at.x, y: at.y, at: Date.now() }])
                crownPointer = at
            }
        }
        crownCanvas.requestPaint()
        if (!moving) crownTimer.stop()
    }

    /// The folder under the pointer: {side, row}, or null.
    function crownHit() {
        if (crownActive === 0) return null
        var h = crownHalves[crownActive]
        if (!h.shown) return null
        var geo = crownGeo(crownActive)
        var rings = Crown.layout(h.shown, geo, function(way) { return crownRows(crownActive, way) })
        for (var i = 0; i < rings.length; i++) {
            var ring = rings[i]  // the ring the pointer is in: the field, or once the border
            if (ring.point) {    // has passed it, the subfolders drawing in brings
                return ring.hi >= 0 ? { side: crownActive, row: ring.items[ring.hi] } : null
            }
        }
        return null
    }

    function crownClicked(x, y, twice) {
        var hit = crownHit()
        if (twice && !(hit && hit.side < 0)) {
            // The first click looked there already: the second goes there - the CWD - and away.
            if (Date.now() - wentInAt < 1000) {
                navigateTo(ctdPath)
                putAway()
            }
            return
        }
        for (var i = 0; i < stemHits.length; i++) {
            var s = stemHits[i]
            if (x >= s.x && x <= s.x + s.w && y >= s.y && y <= s.y + s.h) {
                wentInAt = Date.now()
                if (s.kind === "clipboard") sunTreeBackend.showFolder(sunTreeBackend.clipboardPath())
                else if (s.kind === "parent") goUpTo(s.path)
                else sunTreeBackend.refreshAll()
                return
            }
        }
        if (!hit) {
            if (!onCrown(x, y)) putAway()
            return
        }
        wentInAt = Date.now()
        if (hit.side > 0) {
            glideIntoStem(hit.row.path)
            crownReset()
            sunTreeBackend.showFolder(hit.row.path)
            return
        }
        // The left half: a click looks into a born folder, a double click puts on its lens
        // (with a lens on: sharper).
        if (twice) {
            leftClickDelayTimer.stop()
            pendingLeftRow = null
            crownReset()
            applyLeftRowDouble(hit.row)
            putAway()
        } else {
            pendingLeftRow = hit.row
            glideIntoStem(hit.row.path)
            leftClickDelayTimer.restart()
        }
    }

    /// A file dropped: into the folder under the pointer, or onto the Clipboard.
    function crownDropped(drop) {
        if (crownDropUrls(drop.urls || [])) drop.accept(Qt.MoveAction)
        crownRelease()
    }

    function crownDropUrls(urls) {
        var target = ""
        var p = crownPointer
        for (var i = 0; p && i < stemHits.length; i++) {
            var s = stemHits[i]
            if (s.kind === "clipboard" && p.x >= s.x && p.x <= s.x + s.w && p.y >= s.y && p.y <= s.y + s.h) target = sunTreeBackend.clipboardPath()
        }
        var hit = crownHit()
        if (!target && hit) target = hit.row.path
        if (!target) return false
        var sources = []
        for (var j = 0; j < urls.length; j++) sources.push(decodeURIComponent(String(urls[j]).replace(/^file:\/\//, "")))
        var done = sunTreeBackend.dropFiles(sources, target)
        if (!done || !done.count) return false
        showNotice(done.count, done.place)
        putAway()
        return true
    }

    /// After a drop: where the files went, with undo - SunTree itself is gone.
    function showNotice(count, place) {
        var parts = String(place || "").split("/").filter(function(p) { return p.length > 0 })
        var where = parts.slice(-2).join("/")
        dropNotice.text = count === 1 ? qsTr("1 file → %1").arg(where) : qsTr("%1 files → %2").arg(count).arg(where)
        // Sized here: the platform writes a window's size back and so loses a binding.
        dropNotice.width = noticeText.implicitWidth + noticeRow.spacing + undoButton.width + 32
        dropNotice.x = dropNotice.screen.virtualX + (dropNotice.screen.width - dropNotice.width) / 2
        dropNotice.y = dropNotice.screen.virtualY + dropNotice.screen.height - dropNotice.height - 60
        dropNotice.visible = true
        noticeTimer.restart()
    }

    function noticeUndo() {
        sunTreeBackend.undoDrop()
        noticeTimer.stop()
        dropNotice.visible = false
    }

    /// Up the stem to a parent, the way back of drawing in: the stem's entries glide to their
    /// new places, and the folders between the parent and the CWD come out of the stem - the
    /// crown starts as if one had dived from the parent down to the old CWD and runs back to
    /// rest, as when letting go (Designdocument Krone.md, 3).
    function goUpTo(path) {
        var from = ctdPath
        for (var key in stemGlide) {
            var at = key.indexOf(":")
            if (at > 0) stemGlide[key.slice(at + 1)] = stemGlide[key]  // the same folder, another kind
        }
        crownReset()
        sunTreeBackend.showFolder(path)
        spitOut(from)
    }

    /// The crown as if dived from the CWD down to the folder from; it runs back to rest.
    function spitOut(from) {
        var base = ctdPath.replace(/\/+$/, "")
        if (from.indexOf(base + "/") !== 0) return
        var names = from.slice(base.length + 1).split("/").filter(function(n) { return n.length > 0 })
        for (var side = 1; side >= -1; side -= 2) {
            var way = []
            for (var i = 0; i < names.length; i++) {
                var rows = crownRows(side, way), found = -1
                for (var j = 0; j < rows.length; j++) {
                    if (String(rows[j].path).replace(/\/+$/, "").split("/").pop() === names[i]) { found = j; break }
                }
                if (found < 0) break
                way.push(found)
            }
            if (way.length !== names.length) continue
            var g = crownGeo(side), u = []
            for (var k = 0; k < way.length; k++) u.push(way[k] + 0.5)
            u.push(crownRows(side, way).length / 2)
            var h = crownHalves[side]
            h.shown = { s: g.ri + way.length * 2 * (g.T - g.ri), u: u, lock: way.slice() }
            h.target = { s: 0, u: u.slice(), lock: way.slice(), released: true }
            h.lensK = 1
            crownTimer.start()
            return
        }
    }

    /// A folder gone into glides from where it was into the stem.
    function glideIntoStem(path) {
        if (crownPointer) stemGlide[path] = crownPointer.y
    }

    // --- drawing -----------------------------------------------------------------------

    function crownSector(ctx, side, cx, cy, r0, r1, a0, a1) {
        var A0 = side > 0 ? a0 * Math.PI / 180 : Math.PI - a0 * Math.PI / 180
        var A1 = side > 0 ? a1 * Math.PI / 180 : Math.PI - a1 * Math.PI / 180
        ctx.beginPath()
        ctx.arc(cx, cy, r1, A0, A1, side < 0)
        ctx.arc(cx, cy, r0, A1, A0, side > 0)
        ctx.closePath()
    }

    /// The CWD's light around the current path: strokes widening and fading outward (the
    /// canvas' shadowBlur is far too slow - it stalled the animations).
    function glowStroke(ctx, alpha) {
        var rings = [[12, 0.10], [8, 0.18], [5, 0.30], [2, 1.0]]
        ctx.save()
        ctx.strokeStyle = cwdGlow
        for (var i = 0; i < rings.length; i++) {
            ctx.lineWidth = rings[i][0]
            ctx.globalAlpha = rings[i][1] * alpha
            ctx.stroke()
        }
        ctx.restore()
    }

    function crownLabel(ctx, side, cx, cy, r0, r1, a0, a1, text, alpha, bold) {
        var mid = (a0 + a1) / 2, arc = (a1 - a0) * Math.PI / 180 * (r0 + r1) / 2, width = r1 - r0 - 18
        if (alpha < 0.05 || arc < 13 || width < 26) return
        ctx.save()
        ctx.font = (bold ? "bold " : "") + "12px sans-serif"
        var t = text
        while (t.length > 2 && ctx.measureText(t).width > width) t = t.slice(0, t.length - 2) + "…"
        var a = mid * Math.PI / 180, r = r0 + 10
        ctx.translate(cx + side * r * Math.cos(a), cy + r * Math.sin(a))
        ctx.rotate(side > 0 ? a : -a)
        ctx.globalAlpha = alpha
        ctx.fillStyle = "#eaf3ff"
        ctx.textAlign = side > 0 ? "left" : "right"
        ctx.textBaseline = "middle"
        ctx.fillText(t, 0, 0)
        ctx.restore()
    }

    function crownPaintHalf(ctx, side, hit) {
        var g = crownGeo(side), h = crownHalves[side]
        var state = h.shown || { s: 0, u: [], lock: [] }
        var rings = Crown.layout(state, g, function(way) { return crownRows(side, way) })
        var fallback = side < 0 ? "#3b6b7d" : "#4e668f"
        crownSector(ctx, side, g.cx, g.cy, 0, g.R + 6, -90, 90)
        ctx.fillStyle = side < 0 ? "#273847" : "#2d3750"
        ctx.fill()
        var glowing = []
        for (var r = 0; r < rings.length; r++) {
            var ring = rings[r], a = ring.start
            for (var i = 0; i < ring.items.length; i++) {
                var a0 = a, a1 = a + ring.sp[i]
                a = a1
                if (a1 - a0 < 0.05) continue
                var row = ring.items[i]
                var embryo = !!(row.entry && row.entry.isEmbryo === true)
                var isHit = !!hit && hit.row === row
                var color = String(row.color || "") || fallback
                var f = ring.kind === "kids" ? 0.95 : 0.82
                if (ring.kind === "field" && i === ring.hi) f = 0.92
                if (isHit) f = 1.12
                ctx.globalAlpha = ring.alpha * (embryo ? embryoOpacity : 1)
                crownSector(ctx, side, g.cx, g.cy, ring.r0, ring.r1, a0, a1)
                ctx.fillStyle = _adjustColor(color, f) || color
                ctx.fill()
                ctx.lineWidth = 1
                ctx.strokeStyle = embryo ? "rgba(220,235,255,0.45)" : "rgba(15,17,23,0.9)"
                ctx.setLineDash(embryo ? [4, 4] : [])
                ctx.stroke()
                ctx.setLineDash([])
                ctx.globalAlpha = 1
                var cwd = isCwd(row.path)
                if (cwd) glowing.push({ r0: ring.r0, r1: ring.r1, a0: a0, a1: a1, alpha: ring.alpha })
                crownLabel(ctx, side, g.cx, g.cy, ring.r0, ring.r1, a0, a1, row.label, ring.labels * (embryo ? 0.7 : 1), cwd)
            }
        }
        // The CWD glows, drawn last so no neighbour covers its light.
        for (var k = 0; k < glowing.length; k++) {
            var gl = glowing[k]
            crownSector(ctx, side, g.cx, g.cy, gl.r0, gl.r1, gl.a0, gl.a1)
            glowStroke(ctx, gl.alpha)
        }
    }

    /// The stem from top to bottom: the Clipboard, (the lens' frame), the folders drawn in
    /// as a preview, the CWD, its parents (Designdocument Krone.md, 4).
    function stemEntries() {
        var out = []
        for (var side = -1; side <= 1; side += 2) {
            var h = crownHalves[side]
            if (!h.shown) continue
            var g = crownGeo(side), st = Crown.phase(h.shown.s, g.ri, g.T)
            if (st.ph === 0) continue
            var dive = []
            for (var k = 0; k <= st.L; k++) {
                if (k === st.L && st.ph !== 2) break
                var row = crownRows(side, h.shown.lock.slice(0, k))[h.shown.lock[k]]
                if (!row) break
                dive.push({ label: row.label, path: row.path, w: k < st.L ? 1 : Crown.smooth(st.q), kind: "preview",
                           glow: isCwd(row.path) })
            }
            out = out.concat(dive.reverse())
        }
        out.push({ label: cwdLeafName(), sub: projectNameFromCwd(), path: ctdPath, w: 1, kind: "ctd", glow: isCwd(ctdPath) })
        var parents = centerStackEntries()
        for (var i = 0; i < parents.length; i++) {
            out.push({ label: parents[i].label, path: parents[i].path, w: 1, kind: "parent", glow: isCwd(parents[i].path) })
        }
        return out
    }

    /// Where the stem's entries belong (before gliding): slot 0 is the middle, as big as the
    /// oval; each entry one slot below the one above it. A folder being drawn in (the top
    /// preview, weight q) comes down from above: its slot is q - 1, so it reaches the middle
    /// just as the CTD has slid one slot down - never piled on it.
    function stemPlaces() {
        var cy = layoutRoot.cwdY + layoutRoot.cwdHeight / 2
        var ovalH = layoutRoot.cwdHeight, ovalW = layoutRoot.cwdWidth, pillH = 30, gap = 8, pillW = layoutRoot.stackWidth - 16
        var entries = stemEntries(), out = []
        var shift = entries.length && entries[0].kind === "preview" ? entries[0].w - 1 : 0
        for (var i = 0; i < entries.length; i++) {
            var e = entries[i], slot = i + shift
            var y = slot < 1 ? cy + slot * (ovalH / 2 + gap + pillH / 2)
                             : cy + (ovalH / 2 + gap + pillH / 2) + (slot - 1) * (pillH + gap)
            var big = 1 - Math.min(1, Math.abs(slot))
            out.push({ e: e, kind: e.kind, weight: e.w, slot: slot, y: y, big: big,
                       w: pillW + (ovalW - pillW) * big, h: pillH + (ovalH - pillH) * big })
        }
        return out
    }

    function stemPaint(ctx, dt) {
        var k = 1 - Math.exp(-dt * crownSoftness)
        var cx = layoutRoot.centerX
        var hits = []
        // The Clipboard on top: one drops onto it like onto any folder.
        var cbY = layoutRoot.shellTop + 4, cbW = layoutRoot.stackWidth
        ctx.beginPath()
        ctx.rect(layoutRoot.stackX, cbY, cbW, layoutRoot.clipboardHeight)
        ctx.fillStyle = "#2c3f5d"; ctx.fill()
        ctx.strokeStyle = "#5f7297"; ctx.lineWidth = 1; ctx.stroke()
        ctx.fillStyle = "#e8efff"; ctx.font = "12px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle"
        ctx.fillText(qsTr("Clipboard (%1)").arg(clipboardModel.length), layoutRoot.stackX + cbW / 2, cbY + layoutRoot.clipboardHeight / 2)
        hits.push({ kind: "clipboard", path: "", x: layoutRoot.stackX, y: cbY, w: cbW, h: layoutRoot.clipboardHeight })

        var places = stemPlaces(), ops = [], seen = ({})
        for (var i = 0; i < places.length; i++) {
            var pl = places[i], e = pl.e, y = pl.y, w = pl.w, hh = pl.h
            var key = e.kind + ":" + e.path
            seen[key] = true
            var cur = stemGlide[key]
            if (cur === undefined) cur = stemGlide[e.path] !== undefined ? stemGlide[e.path] : y
            cur += (y - cur) * k
            stemGlide[key] = cur
            if (Math.abs(y - cur) > 0.5) crownTimer.start()
            ops.push({ e: e, x: cx - w / 2, y: cur - hh / 2, w: w, h: hh, big: pl.big, cy: cur })
            if (e.kind !== "preview") hits.push({ kind: e.kind, path: e.path, x: cx - w / 2, y: cur - hh / 2, w: w, h: hh })
        }
        for (var key2 in stemGlide) if (!seen[key2]) delete stemGlide[key2]
        // the deepest last: on top
        for (var j = ops.length - 1; j >= 0; j--) {
            var o = ops[j]
            if (o.y > layoutRoot.shellBottom) continue
            ctx.save()
            ctx.globalAlpha = Math.min(1, o.e.w * 1.2)
            ctx.beginPath()
            var rad = o.h / 2 * o.big  // square pills; the CWD oval round, growing as one glides into it
            ctx.roundedRect(o.x, o.y, o.w, o.h, rad, rad)
            var projectColor = o.e.kind === "ctd" ? (_adjustColor(currentProjectColor, 0.72) || "#2f3d60") : "#324663"
            ctx.fillStyle = o.big > 0.5 ? projectColor : "#324663"
            ctx.fill()
            if (o.e.glow) {
                glowStroke(ctx, ctx.globalAlpha)  // the CWD: light around it, a bright frame, bold
            } else {
                ctx.lineWidth = o.big > 0.5 ? 2 : 1
                ctx.strokeStyle = o.big > 0.5 ? (_adjustColor(currentProjectColor, 1.1) || "#9cb7f0") : "#6d82a8"
                ctx.setLineDash(o.e.kind === "preview" ? [5, 4] : [])
                ctx.stroke()
                ctx.setLineDash([])
            }
            ctx.fillStyle = "#dbe5ff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"
            ctx.font = (o.big > 0.5 || o.e.glow ? "bold " : "") + (o.big > 0.5 ? "13px " : "12px ") + "sans-serif"
            ctx.fillText(o.e.label, cx, o.cy - (o.big > 0.5 && o.e.sub ? 7 : 0))
            if (o.big > 0.5 && o.e.sub) {
                ctx.font = "11px sans-serif"; ctx.fillStyle = "#b7c8ef"
                ctx.fillText(o.e.sub, cx, o.cy + 9)
            }
            ctx.restore()
        }
        stemHits = hits
    }

    property real crownLastPaint: 0
    function crownPaint(ctx) {
        var now = Date.now(), dt = crownLastPaint ? Math.min(0.05, (now - crownLastPaint) / 1000) : 0.016
        crownLastPaint = now
        ctx.reset()
        var hit = crownHit()
        crownPaintHalf(ctx, -1, hit)
        crownPaintHalf(ctx, 1, hit)
        stemPaint(ctx, dt)
    }

    Window {
        // The notice after a drop, at the bottom of the screen: it outlives SunTree's window.
        id: dropNotice
        objectName: "dropNotice"
        property string text: ""
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
        transientParent: null  // its own window: SunTree's goes away as it shows
        color: "transparent"
        visible: false
        width: 240
        height: 46

        Rectangle {
            anchors.fill: parent
            radius: 12
            color: "#1f2a3d"
            border.width: 1
            border.color: "#5f7297"

            Row {
                id: noticeRow
                anchors.centerIn: parent
                spacing: 14

                Text {
                    id: noticeText
                    anchors.verticalCenter: parent.verticalCenter
                    text: dropNotice.text
                    color: "#e8efff"
                    font.pixelSize: 13
                }

                Rectangle {
                    id: undoButton
                    width: undoLabel.implicitWidth + 20
                    height: 28
                    radius: 7
                    color: undoMouse.containsMouse ? "#496a97" : "#2c3f5d"
                    border.width: 1
                    border.color: "#9ec2ff"

                    Text {
                        id: undoLabel
                        anchors.centerIn: parent
                        text: qsTr("Undo")
                        color: "#e8efff"
                        font.pixelSize: 12
                    }

                    MouseArea {
                        id: undoMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.noticeUndo()
                    }
                }
            }
        }

        Timer {
            id: noticeTimer
            interval: 6000
            onTriggered: dropNotice.visible = false
        }
    }

    Timer {
        id: crownTimer
        interval: 16
        repeat: true
        onTriggered: crownTick(0.016)
    }

    Shortcut {
        sequence: "Ctrl+Q"
        onActivated: root.quitForGood()
    }

    Shortcut {
        sequence: "Escape"
        onActivated: crownRelease(true)
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
        function onPointerGlideDone() {
            if (root.ridingBack) {
                root.ridingBack = false
                root.maybeQuit()
            }
            if (!root.pointerGliding) return
            root.pointerGliding = false
            root.showNow()
        }
        function onDataChanged() { root.refreshModels() }
        function onCwdChanged() { root.refreshModels() }
    }

    Component.onCompleted: {
        refreshModels()
        if (!sunTreeStartHidden) refreshBackdrop()
    }
    // The lens is shared with Scope: coming back, show what it is now.
    onActiveChanged: if (active) turnedTo()
    // Whole again for the next time (the animators write their end values after they finish).
    onVisibleChanged: if (visible) { fadeLayer.opacity = 1; fadeLayer.scale = 1 }

    Timer {
        id: leftClickDelayTimer
        interval: 170
        repeat: false
        onTriggered: {
            var row = pendingLeftRow
            pendingLeftRow = null
            applyLeftRow(row)
        }
    }

    // Going away: the blur on the GUI thread; fading out and drawing together (towards the
    // stem, the window's centre) as animators on the render thread, smooth even when the GUI
    // thread is busy for a moment.
    NumberAnimation {
        id: fadeAnimation
        target: root
        property: "fadeProgress"
        from: 0
        to: 1
        duration: 300
        easing.type: Easing.InQuad
        onFinished: root.fadeDone()
    }

    OpacityAnimator {
        id: fadeOpacity
        target: fadeLayer
        from: 1
        to: 0
        duration: 300
        easing.type: Easing.InQuad
    }

    ScaleAnimator {
        id: fadeScale
        target: fadeLayer
        from: 1
        to: 0.6
        duration: 300
        easing.type: Easing.InQuad
    }

    ShaderEffectSource {
        // SunTree's last picture as it goes away; the real one is hidden meanwhile.
        id: fadeSnapshot
        anchors.fill: scene
        sourceItem: scene
        live: false
        hideSource: root.fading
        visible: false
    }

    MultiEffect {
        id: fadeLayer
        objectName: "fadeLayer"
        anchors.fill: scene
        z: 1  // above the scene: it takes the clicks while fading
        transformOrigin: Item.Center
        source: fadeSnapshot
        visible: root.fading
        autoPaddingEnabled: false
        blurEnabled: true
        blurMax: 64  // MultiEffect's most
        blur: root.fadeProgress

        MouseArea {
            anchors.fill: parent  // nothing reacts while it fades, not even to hovering
            hoverEnabled: true
        }
    }

    Item {
        id: scene
        anchors.fill: parent

        MouseArea {
            // The margin around the crown: beside it, too.
            anchors.fill: parent
            onClicked: root.putAway()
        }

        Item {
            id: layoutRoot
            anchors.fill: parent
            anchors.margins: 20
            // The stem is as wide as the space between the halves' centres, which are the
            // centres of the CWD oval's round ends: the hollow lies around them.
            property real stackWidth: 154
            property real shellDiameter: Math.min(mainArea.height * 0.86, mainArea.width * 0.54)
            property real shellHalfWidth: shellDiameter * 0.5
            property real shellTop: (mainArea.height - shellDiameter) * 0.5
            property real shellBottom: shellTop + shellDiameter
            property real centerX: width * 0.5
            property real stackX: centerX - stackWidth * 0.5
            property real leftX: stackX - shellHalfWidth
            property real rightX: stackX + stackWidth
            property real cwdHeight: 72
            property real cwdWidth: stackWidth + cwdHeight
            property real cwdY: shellTop + shellDiameter * 0.5 - cwdHeight * 0.5
            property real halfOuterRadius: Math.min(shellHalfWidth - 8, shellDiameter * 0.5 - 8)
            property real clipboardHeight: 30

            Item {
                id: mainArea
                x: 0
                y: 0
                width: parent.width
                height: parent.height - y

                Item {
                    // The halves only place the crown: its centres are their inner edges.
                    id: leftHalf
                    x: layoutRoot.leftX
                    y: layoutRoot.shellTop
                    width: layoutRoot.shellHalfWidth
                    height: layoutRoot.shellDiameter
                }

                Item {
                    id: rightHalf
                    x: layoutRoot.rightX
                    y: layoutRoot.shellTop
                    width: layoutRoot.shellHalfWidth
                    height: layoutRoot.shellDiameter
                }

                Item {
                    // Between the halves, behind the stem: what lies behind, blurred and
                    // darkened. The compositor offers no blur behind windows (Muffin), so it
                    // is a snapshot taken before SunTree shows; without one only the tint.
                    id: stemPanel
                    objectName: "stemPanel"
                    property string backdrop: ""
                    x: leftHalf.x + leftHalf.width
                    y: layoutRoot.shellTop
                    width: rightHalf.x - x
                    height: layoutRoot.shellDiameter

                    Image {
                        id: backdropImage
                        anchors.fill: parent
                        source: stemPanel.backdrop
                        cache: false
                        visible: false
                    }

                    Rectangle {
                        id: panelShape
                        anchors.fill: parent
                        radius: 16
                        visible: false
                        layer.enabled: true
                    }

                    MultiEffect {
                        anchors.fill: parent
                        source: backdropImage
                        visible: stemPanel.backdrop !== ""
                        autoPaddingEnabled: false
                        blurEnabled: true
                        blur: 1.0
                        blurMax: 32  // about a 10 px blur: unreadable, light and dark still show
                        maskEnabled: true
                        maskSource: panelShape
                    }

                    Rectangle {
                        objectName: "stemPanelTint"
                        anchors.fill: parent
                        radius: 16
                        color: Qt.rgba(0, 0, 0, 0.35)
                    }
                }

                Canvas {
                    id: crownCanvas
                    objectName: "crownCanvas"
                    anchors.fill: parent
                    antialiasing: true
                    onPaint: crownPaint(getContext("2d"))
                }

                MouseArea {
                    id: crownMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onPositionChanged: function(mouse) { handMoved(mouse.x, mouse.y) }
                    onExited: crownRelease()
                    onClicked: function(mouse) { crownClicked(mouse.x, mouse.y, false) }
                    onDoubleClicked: function(mouse) { crownClicked(mouse.x, mouse.y, true) }
                }

                DropArea {
                    // Files dragged in (from Nemo, ...) dive like the pointer and land in the
                    // folder under it.
                    anchors.fill: parent
                    onEntered: function(drag) { handMoved(drag.x, drag.y) }
                    onPositionChanged: function(drag) { handMoved(drag.x, drag.y) }
                    onExited: crownRelease()
                    onDropped: function(drop) { crownDropped(drop) }
                }

                Rectangle {
                    // The lens' frame (A3): ✕ takes it off (one stays where it looked); a
                    // level makes the lens flatter. Nearest to the CWD stands the deepest.
                    id: lensFrame
                    x: layoutRoot.stackX
                    y: layoutRoot.shellTop + layoutRoot.clipboardHeight + 18
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
            }
        }
    }
}
