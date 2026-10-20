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

/// Size column text for a list entry (negative = not measured yet). Folders: "" while
/// unknown, "> x" while only a lower bound is known (pass 1), "x" when complete.
function entrySizeText(isDir, isEmbryo, sizeBytes, folderSizeBytes, folderSizeComplete, showFolderSizes) {
    if (!isDir) {
        return _known(sizeBytes) ? formatKilobytes(sizeBytes) : ""
    }
    if (isEmbryo || !showFolderSizes || !_known(folderSizeBytes)) {
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
/// font size. Titles are translated in QML (FilesPanel.listColumnTitle).
var LIST_COLUMNS = [
    { id: "modified", widthEm: 9 },
    { id: "size", widthEm: 7 }
]

/// Visible columns as [{id, width}] in display order.
function visibleListColumns(enabledIds, fontPx) {
    var out = []
    for (var i = 0; i < LIST_COLUMNS.length; i++) {
        var col = LIST_COLUMNS[i]
        if (enabledIds && enabledIds.indexOf(col.id) !== -1) {
            out.push({ id: col.id, width: Math.round(col.widthEm * fontPx) })
        }
    }
    return out
}

/// Cell text of one list row for a column id.
function listCellText(id, row, showFolderSizes) {
    if (id === "size") {
        return entrySizeText(row.isDir, row.isEmbryo, row.sizeBytes, row.folderSizeBytes,
            row.folderSizeComplete, showFolderSizes)
    }
    if (id === "modified") {
        return row.isEmbryo ? "" : formatModified(row.modifiedTs)
    }
    return ""
}
