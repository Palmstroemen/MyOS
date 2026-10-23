.pragma library

function pathPartsFull(path) {
    return String(path || "").split("/").filter(function(p) { return p.length > 0 })
}

function prefixParts(path, pathDisplayPrefix) {
    if (!pathDisplayPrefix || pathDisplayPrefix.length === 0) return []
    var prefix = pathDisplayPrefix
    if (prefix.endsWith("/") && prefix.length > 1) {
        prefix = prefix.slice(0, -1)
    }
    var pathStr = String(path || "")
    if (prefix === pathStr) {
        return prefix.split("/").filter(function(p) { return p.length > 0 })
    }
    if (pathStr.indexOf(prefix + "/") === 0) {
        return prefix.split("/").filter(function(p) { return p.length > 0 })
    }
    return []
}

function pathPartsDisplay(path, pathDisplayPrefix) {
    var fullParts = pathPartsFull(path)
    var prefix = prefixParts(path, pathDisplayPrefix)
    if (prefix.length === 0) return fullParts
    var remainder = fullParts.slice(prefix.length)
    var lastPrefix = prefix[prefix.length - 1]
    return (remainder.length === 0) ? [lastPrefix] : [lastPrefix].concat(remainder)
}

// --- The lens' frame (Designdocument Perspective Resolver MVP.md, A3) ------------------
// Projekte › Job › [✕ 04_Finanz › Ausgaben]: the frame holds the segments below the
// project the lens looks into (frameRoot); "" means no lens.

function _trimSlash(path) {
    var p = String(path || "")
    return (p.length > 1 && p.endsWith("/")) ? p.slice(0, -1) : p
}

/// Whether path lies strictly below folder.
function isBelow(path, folder) {
    var f = _trimSlash(folder)
    return f.length > 0 && String(path || "").indexOf(f + "/") === 0
}

/// Index of the first segment path inside the frame (paths.length: no frame).
function lensFrameStart(paths, frameRoot) {
    for (var i = 0; i < paths.length; i++) {
        if (isBelow(paths[i], frameRoot)) return i
    }
    return paths.length
}

/// [from, ..., to - 1]
function indexRange(from, to) {
    var out = []
    for (var i = from; i < to; i++) out.push(i)
    return out
}
