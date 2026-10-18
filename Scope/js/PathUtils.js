.pragma library

function trimTrailingSlash(path) {
    var value = String(path || "")
    if (value.length > 1 && value.endsWith("/")) {
        return value.slice(0, -1)
    }
    return value
}

function fromFileUrl(path) {
    var value = String(path || "").trim()
    if (value.indexOf("file://") !== 0) {
        return value
    }
    var raw = value.slice(7)
    if (raw.indexOf("/") === 0) {
        return raw
    }
    var slash = raw.indexOf("/")
    if (slash >= 0) {
        return raw.slice(slash)
    }
    return raw
}

function toFileUrl(path) {
    if (String(path || "").indexOf("file://") === 0) return path
    return "file://" + path
}

function normalizeFsPath(path) {
    var value = String(path || "").trim()
    if (value.length === 0) {
        return ""
    }
    if (value.indexOf("file://") === 0) {
        var raw = fromFileUrl(value)
        try {
            value = decodeURIComponent(raw)
        } catch (e) {
            value = raw
        }
    }
    return trimTrailingSlash(value)
}

function basename(path) {
    var text = String(path || "")
    if (text.length === 0) {
        return "(unknown)"
    }
    var parts = text.split("/")
    return parts.length > 0 ? (parts[parts.length - 1] || text) : text
}
