.pragma library

/// Human-readable byte size with the locale's decimal separator, e.g. "1,5 MB".
function formatBytes(bytes) {
    var value = Number(bytes)
    if (!isFinite(value) || value < 0) return ""
    var units = ["B", "KB", "MB", "GB", "TB"]
    var unit = 0
    while (value >= 1024 && unit < units.length - 1) {
        value /= 1024
        unit += 1
    }
    var text = (unit === 0 || value >= 10) ? String(Math.round(value)) : value.toFixed(1)
    return text.replace(".", Qt.locale().decimalPoint) + " " + units[unit]
}

/// Size in whole KB with the locale's thousands separator, e.g. "4.403 KB". One unit for
/// all rows lets the digit count act as a bar: big folders stand out without reading.
/// Rounded up, so a non-empty file never shows "0 KB".
function formatKilobytes(bytes) {
    var value = Number(bytes)
    if (!isFinite(value) || value < 0) return ""
    return Math.ceil(value / 1024).toLocaleString(Qt.locale(), "f", 0) + " KB"
}

function _known(bytes) {
    return bytes !== undefined && bytes !== null && Number(bytes) >= 0
}

/// Size column text for a list entry (negative = not measured yet). Folders: "–" while
/// sizes are off (not asked for), "" while measuring, "> x" while only a lower bound is
/// known (pass 1), "x" when complete.
function entrySizeText(isDir, isEmbryo, sizeBytes, folderSizeBytes, folderSizeComplete, folderSizesActive) {
    if (!isDir) {
        return _known(sizeBytes) ? formatKilobytes(sizeBytes) : ""
    }
    if (isEmbryo) {
        return ""
    }
    if (!folderSizesActive) {
        return "–"
    }
    if (!_known(folderSizeBytes)) {
        return ""
    }
    var text = formatKilobytes(folderSizeBytes)
    return folderSizeComplete ? text : "> " + text
}

/// Local date and time in the locale's short format, e.g. "20.10.26 09:24".
function formatModified(ts) {
    var value = Number(ts)
    if (!isFinite(value) || value < 0) return ""
    // QML enums are not visible in .pragma library scripts; 1 == Locale.ShortFormat.
    var locale = Qt.locale()
    return new Date(value * 1000).toLocaleString(locale, locale.dateTimeFormat(1))
}

/// List view columns (right of the name), in display order. Width in multiples of the
/// font size; text left-aligned, numbers right-aligned. Titles are translated in QML
/// (FilesPanel.listColumnTitle).
var LIST_COLUMNS = [
    { id: "modified", widthEm: 8, align: "left" },
    { id: "size", widthEm: 7, align: "right" },
    { id: "type", widthEm: 13, align: "left" },
    { id: "tags", widthEm: 9, align: "left" },
    { id: "accessed", widthEm: 8, align: "left" },
    { id: "permissions", widthEm: 9, align: "left" },
    { id: "owner", widthEm: 6, align: "left" },
    { id: "group", widthEm: 6, align: "left" }
]

/// Gap between list columns, in multiples of the font size.
var LIST_COLUMN_GAP_EM = 1.2

/// Visible columns as [{id, width, align, x}] in display order; x is the offset from the
/// start of the first column, so header, rows and hover areas share one geometry.
function visibleListColumns(enabledIds, fontPx) {
    var out = []
    var x = 0
    var gap = Math.round(LIST_COLUMN_GAP_EM * fontPx)
    for (var i = 0; i < LIST_COLUMNS.length; i++) {
        var col = LIST_COLUMNS[i]
        if (enabledIds && enabledIds.indexOf(col.id) !== -1) {
            var width = Math.round(col.widthEm * fontPx)
            out.push({ id: col.id, width: width, align: col.align, x: x })
            x += width + gap
        }
    }
    return out
}

/// Total width of the visible columns including the gaps between them.
function listColumnsWidth(columns) {
    if (!columns || columns.length === 0) return 0
    var last = columns[columns.length - 1]
    return last.x + last.width
}

/// "#a #b" for the tags column. Rows carry it as tagsText: in a ListModel an array
/// role becomes a nested model, not a JS array.
function tagsText(tags) {
    var parts = []
    for (var i = 0; tags && i < tags.length; i++) parts.push("#" + tags[i])
    return parts.join(" ")
}

/// Cell text of one list row for a column id.
function listCellText(id, row, folderSizesActive) {
    if (id === "size") {
        return entrySizeText(row.isDir, row.isEmbryo, row.sizeBytes, row.folderSizeBytes,
            row.folderSizeComplete, folderSizesActive)
    }
    if (row.isEmbryo) return ""
    if (id === "modified") return formatModified(row.modifiedTs)
    if (id === "accessed") return formatModified(row.accessedTs)
    if (id === "type") return String(row.typeName || "")
    if (id === "tags") return String(row.tagsText || "")
    if (id === "permissions") return String(row.permissions || "")
    if (id === "owner") return String(row.owner || "")
    if (id === "group") return String(row.group || "")
    return ""
}
