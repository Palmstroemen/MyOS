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
