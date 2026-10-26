.pragma library

// The crown's arithmetic (SunTree/Designdocument Krone.md), without drawing.
//
// One coordinate s runs through all levels of a half. Each level is [ri, T) - the field
// under the pointer grows until it fills the half (phase 1, p) - and [T, T + D) - the field
// is drawn into the stem while the pointer is pulled back to ri (phase 2, q); D = T - ri.
// Below ri (level 0 only) the pointer is in the stem's hollow (phase 0).
//
// Angles are degrees in a half's own frame: -90 at the top, 0 outward, 90 at the bottom.
// A level's u is a continuous folder index (folder i covers [i, i + 1)); lock[k] is the
// folder of level k drawn into the stem (the way down); over is how far the hand has pushed
// on past the first or last folder, towards the stem (pixels, negative at the top).

function clamp(x, a, b) {
    return Math.max(a, Math.min(b, x))
}

function smooth(x) {
    x = clamp(x, 0, 1)
    return x * x * (3 - 2 * x)
}

/// Where s is: {L: level, v: s within it, ph: 0 hollow / 1 growing / 2 drawn in, p, q}.
function phase(s, ri, T) {
    var D = T - ri
    if (s < ri) return { L: 0, v: s, ph: 0, p: 0, q: 0 }
    var L = Math.floor((s - ri) / (2 * D))
    var v = s - L * 2 * D
    if (v < T) return { L: L, v: v, ph: 1, p: (v - ri) / D, q: 0 }
    return { L: L, v: v, ph: 2, p: 1, q: (v - T) / D }
}

/// The pointer's distance from the centre: the hand's while growing, pulled back from T
/// to ri while the field is drawn in.
function pointerRadius(s, ri, T) {
    var st = phase(s, ri, T)
    if (st.ph < 2) return st.v
    return suckRadius(st.q, ri, T)
}

/// Outer edge of the growing field: R at first, T when it fills the half.
function fieldRadius(p, R, T) {
    return R - (R - T) * smooth(p)
}

/// Outer edge of the field being drawn in: T at first, ri when it is gone.
function suckRadius(q, ri, T) {
    return T - (T - ri) * smooth(q)
}

/// Angular spans (summing to 180) of n folders: a fish-eye of strength lens around u that
/// sharpens with p until the folder under u fills the half.
function spans(n, u, p, lens) {
    var out = []
    if (n <= 0) return out
    var e = smooth(p), w0 = [], w1 = [], s0 = 0, s1 = 0
    for (var i = 0; i < n; i++) {
        var d = i + 0.5 - u
        var a = 1 + lens * Math.exp(-Math.pow(d / 1.25, 2))
        var b = Math.exp(-Math.pow(d / 0.32, 2)) + 1e-9
        w0.push(a); w1.push(b); s0 += a; s1 += b
    }
    for (var j = 0; j < n; j++) out.push(180 * ((1 - e) * w0[j] / s0 + e * w1[j] / s1))
    return out
}

function startsOf(sp) {
    var out = [], a = -90
    for (var i = 0; i < sp.length; i++) { out.push(a); a += sp[i] }
    return out
}

/// The angle of the continuous index u in the spans.
function angleAt(sp, u) {
    var n = sp.length
    if (!n) return 0
    var i = clamp(Math.floor(u), 0, n - 1), f = clamp(u - i, 0, 1)
    return startsOf(sp)[i] + f * sp[i]
}

/// The pointer's angle: inside the fish-eye at first; the fuller the field, the more evenly
/// it moves with the hand, and the neighbouring field grows past it.
function pointerAngle(sp, u, p) {
    var n = sp.length
    if (!n) return 0
    var e = smooth(p)
    return (1 - e) * angleAt(sp, u) + e * (-90 + clamp(u / n, 0, 1) * 180)
}

/// The folder whose span holds the angle th.
function indexAt(sp, th) {
    var st = startsOf(sp)
    for (var i = sp.length - 1; i >= 0; i--) if (th >= st[i]) return i
    return 0
}

/// The u whose fish-eye puts the pointer at angle th (bisection: the angle grows with u).
function uAtAngle(n, th, lens) {
    var lo = 0, hi = n - 1e-4
    for (var i = 0; i < 40; i++) {
        var mid = (lo + hi) / 2
        if (angleAt(spans(n, mid, 0, lens), mid) < th) lo = mid
        else hi = mid
    }
    return (lo + hi) / 2
}

/// A half taken at distance s and angle th, with n folders on its first level (the
/// fish-eye starts flat, so the even layout places the pointer).
function start(s, th, n) {
    return { s: s, u: [clamp((th + 90) / 180 * n, 0, n - 1e-4)], lock: [], over: 0, released: false }
}

/// Where the pointer is drawn for a state: {r, th, L, ph, index} - index is the folder
/// under it (of level L; while drawn in, of the level below).
function pointer(state, geo, childCount) {
    var st = phase(state.s, geo.ri, geo.T)
    var way = state.lock.slice(0, st.L)
    var n = childCount(way)
    if (st.ph === 2) {
        var kids = childCount(way.concat([state.lock[st.L]]))
        var uc = state.u[st.L + 1] !== undefined ? state.u[st.L + 1] : kids / 2
        var csp = spans(kids, uc, 0, geo.lens)
        var th2 = angleAt(csp, uc)
        return { r: suckRadius(st.q, geo.ri, geo.T), th: th2, L: st.L, ph: 2, index: indexAt(csp, th2) }
    }
    var u = state.u[st.L] !== undefined ? state.u[st.L] : n / 2
    var sp = spans(n, u, st.p, geo.lens)
    var th = pointerAngle(sp, u, st.p)
    return { r: st.v, th: th, L: st.L, ph: st.ph, index: indexAt(sp, th) }
}

function copyState(state) {
    return { s: state.s, u: state.u.slice(), lock: state.lock.slice(), over: state.over || 0,
             released: !!state.released }
}

/// The hand moved by dr (outward) and dt (along the half, downward) pixels. childCount(way)
/// gives the number of folders below the way of folder indices. Returns the new state;
/// released: the half lets go of the pointer - back into the hollow, or pushed on past the
/// first or last folder of any level by geo.edge pixels (towards the stem, where one is
/// otherwise caught sideways); moving back from the end starts the push again.
function move(state, dr, dt, geo, childCount) {
    var next = copyState(state)
    var st = phase(state.s, geo.ri, geo.T)
    var way = state.lock.slice(0, st.L)
    var level = st.ph === 2 ? st.L + 1 : st.L
    var levelWay = st.ph === 2 ? way.concat([state.lock[st.L]]) : way
    var n = Math.max(1, childCount(levelWay))

    // Along the half: scroll through the level.
    var slot = Math.PI * geo.R * 0.55 / n / (geo.speed || 1)
    var u = (next.u[level] !== undefined ? next.u[level] : n / 2) + dt / slot
    var over = next.over
    if (u < 0) next.over = Math.min(0, over) + u * slot
    else if (u > n) next.over = Math.max(0, over) + (u - n) * slot
    else next.over = 0
    if (Math.abs(next.over) > (geo.edge || 0.08 * geo.R)) {
        next.released = true
        return next
    }
    next.u[level] = clamp(u, 0, n - 1e-4)

    // Outward and back: deeper, or out again.
    var s = state.s + dr
    var base = st.L * 2 * (geo.T - geo.ri)
    if (st.ph === 1 && s >= base + geo.T) {
        var here = pointer(next, geo, childCount)
        var hi = indexAt(spans(n, next.u[st.L], 1, geo.lens), here.th)
        var kids = childCount(way.concat([hi]))
        if (!kids) {
            s = base + geo.T - 0.01  // no subfolders: it fills the half, nothing to draw in
        } else {
            next.lock = way.concat([hi])
            next.u = next.u.slice(0, st.L + 1)
            next.u.push(uAtAngle(kids, here.th, geo.lens))
        }
    }
    if (s < geo.ri) next.released = true
    next.s = s
    return next
}

/// The rings a half shows for a state: [{kind, way, items, r0, r1, start, sp, alpha, labels,
/// hi, under}]. childrenOf(way) gives the folders below a way of folder indices (any
/// objects; the rings carry them through). kind "base" (no field grows), "field" (the level
/// the pointer is on, or the one being drawn in) or "kids" (subfolders: of each field in
/// its slice while growing, of the field drawn in on the whole half); hi is the folder the
/// pointer is on in a field, under marks the subfolders of that folder.
function layout(state, geo, childrenOf) {
    var st = phase(state.s, geo.ri, geo.T)
    var way = state.lock.slice(0, st.L)
    var items = childrenOf(way), n = items.length
    var u = state.u[st.L] !== undefined ? state.u[st.L] : n / 2
    if (st.ph === 0 || n === 0) {
        return [{ kind: "base", way: way, items: items, r0: geo.ri, r1: geo.R, start: -90,
                  sp: spans(n, u, 0, geo.lens), alpha: 1, labels: 1, hi: -1, under: false }]
    }
    var rings = []
    if (st.ph === 1) {
        var e = smooth(st.p)
        var sp = spans(n, u, st.p, geo.lens), starts = startsOf(sp)
        var Ro = fieldRadius(st.p, geo.R, geo.T)
        var th = pointerAngle(sp, u, st.p), hi = indexAt(sp, th)
        rings.push({ kind: "field", way: way, items: items, r0: geo.ri, r1: Ro, start: -90, sp: sp,
                     alpha: 1, labels: 1, hi: hi, under: false })
        for (var i = 0; i < n; i++) {
            var kidWay = way.concat([i]), kids = childrenOf(kidWay)
            if (!kids.length || sp[i] < 0.5) continue
            var under = i === hi
            var uc = under ? clamp((th - starts[i]) / sp[i], 0, 0.9999) * kids.length : kids.length / 2
            var csp = spans(kids.length, uc, 0, under ? geo.lens : 0)
            for (var j = 0; j < csp.length; j++) csp[j] = csp[j] * sp[i] / 180
            rings.push({ kind: "kids", way: kidWay, items: kids, r0: Ro, r1: geo.R, start: starts[i], sp: csp,
                         alpha: clamp(e * 1.6, 0, 1), labels: e, hi: -1, under: under })
        }
        return rings
    }
    // Drawn in: the field fills the half and shrinks into the stem; its subfolders take over.
    var q = smooth(st.q), locked = clamp(state.lock[st.L] !== undefined ? state.lock[st.L] : Math.floor(u), 0, n - 1)
    var Rp = suckRadius(st.q, geo.ri, geo.T)
    var was = spans(n, u, 1, geo.lens), full = smooth(st.q * 5), psp = []
    for (var k = 0; k < n; k++) psp.push((1 - full) * was[k] + full * (k === locked ? 180 : 0))
    rings.push({ kind: "field", way: way, items: items, r0: geo.ri, r1: Rp, start: -90, sp: psp,
                 alpha: 1 - q * 0.5, labels: 1 - q, hi: locked, under: false })
    var downWay = way.concat([locked]), down = childrenOf(downWay)
    var ud = state.u[st.L + 1] !== undefined ? state.u[st.L + 1] : down.length / 2
    var dsp = spans(down.length, ud, 0, geo.lens)
    rings.push({ kind: "kids", way: downWay, items: down, r0: Rp, r1: geo.R, start: -90, sp: dsp,
                 alpha: 1, labels: 1, hi: indexAt(dsp, angleAt(dsp, ud)), under: true })
    return rings
}
