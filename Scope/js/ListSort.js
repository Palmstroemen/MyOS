.pragma library

// Sorting of FilesPanel entries by a list column. Folders always come before files;
// unknown values (unmeasured folder size, embryo without date) always sort last.
var SORT_KEYS = ["name", "modified", "size"]

function _number(value) {
    var n = Number(value)
    return (value === undefined || value === null || !isFinite(n)) ? -1 : n
}

function _sortValue(entry, key) {
    if (key === "size") {
        return entry.isDir ? _number(entry.folderSizeBytes) : _number(entry.sizeBytes)
    }
    return _number(entry.modifiedTs)
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
    if (key === "size" || key === "modified") {
        var va = _sortValue(a, key)
        var vb = _sortValue(b, key)
        var knownA = va >= 0
        var knownB = vb >= 0
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
