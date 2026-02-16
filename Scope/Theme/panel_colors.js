.pragma library

function _clamp01(value, fallback) {
    var v = Number(value)
    if (!(v >= 0.0)) {
        v = Number(fallback)
    }
    if (!(v >= 0.0)) {
        v = 0.0
    }
    if (v > 1.0) {
        v = 1.0
    }
    return v
}

function _blend(baseColor, tintColor, mix) {
    var t = _clamp01(mix, 0.65)
    return Qt.rgba(
        baseColor.r + (tintColor.r - baseColor.r) * t,
        baseColor.g + (tintColor.g - baseColor.g) * t,
        baseColor.b + (tintColor.b - baseColor.b) * t,
        1.0
    )
}

function uPanelColor(isProjectContext, backgroundColor, cwdColor, mix) {
    if (!isProjectContext) {
        return backgroundColor
    }
    return _blend(backgroundColor, cwdColor, mix)
}

function filesOverlayColor(baseLuma, alpha) {
    var a = _clamp01(alpha, 0.20)
    // dark base: brighten; light base: darken
    return (baseLuma < 0.5) ? Qt.rgba(1, 1, 1, a) : Qt.rgba(0, 0, 0, a)
}

