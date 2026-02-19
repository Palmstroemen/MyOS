.pragma library

// Mirrors PostFix Theme/tag_chips.py QPushButton geometry.
var CHIP_LEFT_RADIUS = 2
var CHIP_RIGHT_RADIUS = 12
var CHIP_PADDING_V = 4
var CHIP_PADDING_H = 8
var CHIP_MARGIN = 3

var CHIP_BORDER_IDLE_ALPHA = 0.24   // rgba(0,0,0,60)
var CHIP_BORDER_HOVER_ALPHA = 0.37  // rgba(0,0,0,95)

function textColorForBg(colorValue) {
    var c = colorValue
    var luma = (0.2126 * c.r) + (0.7152 * c.g) + (0.0722 * c.b)
    return luma < 0.45 ? "#ffffff" : "#1f1f1f"
}

