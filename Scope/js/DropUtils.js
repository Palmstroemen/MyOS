.pragma library

/// Text payload of a DropArea drop: plain text, the Scope drag source's
/// dragPayload (internal drags carry no mime text), or dropped URLs.
function payloadText(drop) {
    if (!drop) return ""
    var direct = String(drop.text || "").trim()
    if (direct.length > 0) {
        return direct
    }
    if (drop.source && drop.source.dragPayload !== undefined) {
        var fromSource = String(drop.source.dragPayload || "").trim()
        if (fromSource.length > 0) {
            return fromSource
        }
    }
    if (drop.getDataAsString) {
        var plain = String(drop.getDataAsString("text/plain") || "").trim()
        if (plain.length > 0) {
            return plain
        }
        var uriList = String(drop.getDataAsString("text/uri-list") || "").trim()
        if (uriList.length > 0) {
            return uriList
        }
    }
    if (drop.urls && drop.urls.length > 0) {
        var urls = []
        for (var i = 0; i < drop.urls.length; i++) {
            var value = String(drop.urls[i] || "").trim()
            if (value.length > 0) {
                urls.push(value)
            }
        }
        if (urls.length === 1) {
            return urls[0]
        }
        if (urls.length > 1) {
            return "__MYOS_PATHS__" + JSON.stringify(urls)
        }
    }
    return ""
}
