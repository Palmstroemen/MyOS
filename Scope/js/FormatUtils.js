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

function _known(bytes) {
    return bytes !== undefined && bytes !== null && Number(bytes) >= 0
}

/// Size column text for a list entry (negative = not measured yet). Folders: "" while
/// unknown, "> x" while only a lower bound is known (pass 1), "x" when complete.
function entrySizeText(isDir, isEmbryo, sizeBytes, folderSizeBytes, folderSizeComplete, showFolderSizes) {
    if (!isDir) {
        return _known(sizeBytes) ? formatBytes(sizeBytes) : ""
    }
    if (isEmbryo || !showFolderSizes || !_known(folderSizeBytes)) {
        return ""
    }
    var text = formatBytes(folderSizeBytes)
    return folderSizeComplete ? text : "> " + text
}
