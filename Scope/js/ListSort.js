.pragma library

// Sorting of FilesPanel entries by a list column. Folders always come before files;
// unknown values (unmeasured folder size, embryo without date, empty text) always sort last.
var NUMERIC_KEYS = ["modified", "accessed", "size"]
var TEXT_FIELDS = { type: "typeName", owner: "owner", group: "group", permissions: "permissions" }

/// First click on a column: dates and sizes start with the newest / largest on top.
function defaultAscending(key) {
    return NUMERIC_KEYS.indexOf(key) === -1
}

function _number(value) {
    var n = Number(value)
    return (value === undefined || value === null || !isFinite(n)) ? -1 : n
}

function _numericValue(entry, key) {
    if (key === "size") {
        return entry.isDir ? _number(entry.folderSizeBytes) : _number(entry.sizeBytes)
    }
    return _number(key === "accessed" ? entry.accessedTs : entry.modifiedTs)
}

function _textValue(entry, key) {
    if (key === "tags") {
        var tags = entry.tags || []
        var parts = []
        for (var i = 0; i < tags.length; i++) parts.push(String(tags[i]))
        return parts.join(" ").toLowerCase()
    }
    return String(entry[TEXT_FIELDS[key]] || "").toLowerCase()
}

function _byName(a, b) {
    var na = String(a.name || "").toLowerCase()
    var nb = String(b.name || "").toLowerCase()
    return na < nb ? -1 : (na > nb ? 1 : 0)
}

function compareEntries(a, b, key, ascending) {
    if (!!a.isDir !== !!b.isDir) {
        return a.isDir ? -1 : 1
    }
    var direction = ascending ? 1 : -1
    var numeric = NUMERIC_KEYS.indexOf(key) !== -1
    var text = key === "tags" || TEXT_FIELDS.hasOwnProperty(key)
    if (numeric || text) {
        var va = numeric ? _numericValue(a, key) : _textValue(a, key)
        var vb = numeric ? _numericValue(b, key) : _textValue(b, key)
        var knownA = numeric ? va >= 0 : va !== ""
        var knownB = numeric ? vb >= 0 : vb !== ""
        if (knownA !== knownB) {
            return knownA ? -1 : 1
        }
        if (knownA && va !== vb) {
            return (va < vb ? -1 : 1) * direction
        }
        return _byName(a, b)
    }
    return _byName(a, b) * direction
}

/// Sorted copy of entries; the entry objects themselves are shared, not copied.
function sortEntries(entries, key, ascending) {
    var list = (entries || []).slice(0)
    list.sort(function(a, b) { return compareEntries(a, b, key, ascending) })
    return list
}
