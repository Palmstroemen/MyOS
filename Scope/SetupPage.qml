import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// The back of Scope (Scope/Designdocument Setup.md): the settings of Scope, the Headline and
// SunTree in tabs. Values go to the one settings file through `settings` (Scope's backend:
// setting, setSetting, settingDefault, settingLimits, resetSetting); SunTree reads it when it
// appears. Light/dark and the language are switched by the host (signals), which keeps them.
Rectangle {
    id: root
    property var settings: null
    property bool darkTheme: true
    property string language: "de"
    property bool projectsRowShown: settings ? settings.setting("Scope/projectsRow") === true : false
    property bool templatesRowShown: true
    property int baseFont: 13
    property color textColor: darkTheme ? "#e8efff" : "#1a2233"
    property color mutedColor: darkTheme ? "#9fb0cc" : "#4a5670"
    property color panelColor: darkTheme ? "#1a2230" : "#eef1f8"
    property color pill: darkTheme ? "#2c3f5d" : "#dfe3f0"
    property color pillBorder: darkTheme ? "#5f7297" : "#c6ccdf"
    property alias currentTab: tabs.currentIndex
    // How pale embryos are, as one slides (Scope follows at once; without settings the default).
    readonly property real embryoOpacity: settings ? embryoSlider.value : 0.4
    readonly property real embryoBadgeOpacity: settings ? badgeSlider.value : 0.7
    // How both rows show themselves (Scope tab), kept in the settings file; Scope follows.
    property bool pathBarOn: settings ? settings.setting("Scope/pathBar") === true : true
    property bool previewOn: settings ? settings.setting("Scope/preview") === true : true
    property bool previewBackgroundOn: settings ? settings.setting("Scope/previewBackground") === true : false
    // The rest of what the rows' display menus held, the same for both rows.
    property bool showSuggestionsOn: settings ? settings.setting("Scope/showSuggestions") === true : true
    property bool showHiddenOn: settings ? settings.setting("Scope/showHidden") === true : false
    property string templatesStyle: settings ? String(settings.setting("Scope/templatesStyle")) : "smallIcon"
    property string projectsStyle: settings ? String(settings.setting("Scope/projectsStyle")) : "text"
    property bool instantReopenOn: settings ? settings.setting("Scope/instantReopen") === true : true
    property string previewTuning: settings ? String(settings.setting("Scope/previewTuning")) : "balanced"
    // The preview's timing per tuning (FolderBrowser: hover delay, settling before reopening,
    // collapsing, how far the row follows the pointer).
    readonly property var previewTimings: ({
        "soft": { hoverDelayMs: 110, reopenStabilizeMs: 280, collapseDurationMs: 700, pointerCarry: 0.35, systemPointerCarry: 0.72 },
        "balanced": { hoverDelayMs: 90, reopenStabilizeMs: 220, collapseDurationMs: 500, pointerCarry: 0.5, systemPointerCarry: 0.82 },
        "aggressive": { hoverDelayMs: 60, reopenStabilizeMs: 160, collapseDurationMs: 380, pointerCarry: 0.7, systemPointerCarry: 0.92 }
    })
    readonly property var previewTiming: previewTimings[previewTuning] || previewTimings["balanced"]
    function keep(key, value) {
        if (settings) settings.setSetting(key, value)
    }
    // The small fan's demo: the slider row under the mouse - until its slider is taken; then
    // the fan follows the slider, quiet until the mouse has left the row.
    property string hoveredDemo: ""
    property string quieted: ""
    property int slidersHeld: 0
    readonly property string demo: slidersHeld > 0 || hoveredDemo === quieted ? "" : hoveredDemo

    signal switchTheme()
    signal switchLanguage()
    signal flipBack()
    signal toggleProjectsRow()
    signal toggleTemplatesRow()

    color: panelColor

    MouseArea {
        // The back takes every click and hover: nothing reaches the front through it.
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
        onWheel: function(wheel) { wheel.accepted = true }
    }

    component Pill: Rectangle {
        id: pillButton
        property string label: ""
        signal activated()
        implicitWidth: pillText.implicitWidth + 24
        implicitHeight: 30
        radius: 6
        color: pillArea.containsMouse ? Qt.lighter(root.pill, 1.2) : root.pill
        border.color: root.pillBorder
        Text {
            id: pillText
            anchors.centerIn: parent
            text: pillButton.label
            color: root.textColor
            font.pixelSize: root.baseFont
        }
        MouseArea {
            id: pillArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: pillButton.activated()
        }
    }

    // A setting that is on or off: a check box and its name, the whole line clickable.
    component CheckItem: Item {
        id: checkItem
        property string label: ""
        property bool checked: false
        signal toggled()
        implicitWidth: checkRow.implicitWidth
        implicitHeight: 26
        Row {
            id: checkRow
            spacing: 10
            anchors.verticalCenter: parent.verticalCenter
            Rectangle {
                width: 18
                height: 18
                radius: 4
                anchors.verticalCenter: parent.verticalCenter
                color: checkItem.checked ? Qt.lighter(root.pill, 1.5) : (checkArea.containsMouse ? Qt.lighter(root.pill, 1.15) : root.pill)
                border.color: checkItem.checked ? root.textColor : root.pillBorder
                Text {
                    anchors.centerIn: parent
                    visible: checkItem.checked
                    text: "✓"
                    color: root.textColor
                    font.pixelSize: root.baseFont
                    font.bold: true
                }
            }
            Text {
                text: checkItem.label
                color: root.textColor
                font.pixelSize: root.baseFont
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        MouseArea {
            id: checkArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: checkItem.toggled()
        }
    }

    // One of a few choices side by side, pushed together; the chosen one lit.
    component Choices: Row {
        id: choices
        property string prefix: ""   // objectName prefix: <prefix>_<value>
        property var options: []     // [{ value, label }]
        property string current: ""
        signal chosen(string value)
        spacing: 2
        Repeater {
            model: choices.options
            Rectangle {
                objectName: choices.prefix + "_" + modelData.value
                readonly property bool on: choices.current === modelData.value
                width: choiceText.implicitWidth + 20
                height: 26
                radius: 5
                color: on ? Qt.lighter(root.pill, 1.5) : (choiceArea.containsMouse ? Qt.lighter(root.pill, 1.15) : root.pill)
                border.color: on ? root.textColor : root.pillBorder
                Text {
                    id: choiceText
                    anchors.centerIn: parent
                    text: modelData.label
                    color: root.textColor
                    font.pixelSize: root.baseFont - 1
                    font.bold: parent.on
                }
                MouseArea {
                    id: choiceArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: choices.chosen(modelData.value)
                }
            }
        }
    }

    // A small heading over a group of settings.
    component Heading: Text {
        color: root.textColor
        font.pixelSize: root.baseFont + 1
        font.bold: true
        Layout.topMargin: 6
    }

    // The rows as they really look, in one picture that follows the check items on the right:
    // the path bar (segments pushed together like tabs, the current one dropped), or only the
    // current folder; its folders, a suggested one pale, a hidden one; below, the preview of
    // the folder under the pointer, with or without its panel.
    component RowsExample: Rectangle {
        id: example
        property bool pathBar: true
        property bool preview: true
        property bool previewBackground: false
        property bool suggestions: true
        property bool hidden: false
        property string folderStyle: "smallIcon"
        readonly property int buttonHeight: folderStyle === "largeIcon" ? 64 : 28
        implicitWidth: 420  // in a layout: it sizes by these; wide enough for one line per row
        implicitHeight: exampleColumn.height + 24
        radius: 8
        color: Qt.darker(root.panelColor, root.darkTheme ? 1.25 : 1.04)
        border.color: root.pillBorder

        // kind: "path", "current", "folder", "suggestion", "hidden"
        function fill(kind) {
            var pale = kind === "suggestion" ? root.embryoOpacity : 1.0
            var base = kind === "current" ? Qt.lighter(root.pill, 1.6) : root.pill
            return Qt.rgba(base.r, base.g, base.b, pale)
        }
        function stroke(kind) {
            var pale = kind === "suggestion" ? root.embryoOpacity : 1.0
            return Qt.rgba(root.pillBorder.r, root.pillBorder.g, root.pillBorder.b, pale)
        }

        Column {
            id: exampleColumn
            x: 12
            y: 12
            width: example.implicitWidth - 24
            spacing: -2  // the rows touch, even overlap, as in Scope
            Row {
                // The path bar: the segments nearly touch, like tabs one behind the other.
                spacing: 2
                height: example.buttonHeight
                z: 1  // the current segment drops onto the folders
                Rectangle {
                    // Without the path bar: one folder up.
                    objectName: "exampleUp"
                    visible: !example.pathBar
                    width: 28
                    height: 28
                    radius: 5
                    color: root.pill
                    border.color: root.pillBorder
                    Text { anchors.centerIn: parent; text: "↑"; color: root.textColor; font.pixelSize: root.baseFont + 1; font.bold: true }
                }
                Repeater {
                    model: example.pathBar ? ["Projekte", "Job", "04_Finanz"] : ["04_Finanz ▾"]
                    FolderItem {
                        objectName: "exampleSegment_" + index
                        readonly property bool current: index === (example.pathBar ? 2 : 0)
                        y: current ? 4 : 0
                        style: example.folderStyle
                        label: modelData
                        iconSource: Qt.resolvedUrl("Theme/icons/folder.svg")
                        compactHeight: 28
                        largeHeight: 64
                        iconSmall: 16
                        iconLarge: 34
                        textSize: root.baseFont - 1
                        textColor: root.textColor
                        flatBottomCorners: current
                        fillColor: example.fill(current ? "current" : "path")
                        strokeColor: example.stroke(current ? "current" : "path")
                    }
                }
            }
            Flow {
                // Its folders.
                width: parent.width
                height: implicitHeight
                spacing: 6
                Repeater {
                    model: [{ name: "Aufträge", kind: "folder" }, { name: "Belege", kind: "folder" },
                            { name: "Steuer", kind: "suggestion" }, { name: ".cache", kind: "hidden" }]
                    FolderItem {
                        objectName: "exampleFolder_" + index
                        visible: modelData.kind === "suggestion" ? example.suggestions
                                 : (modelData.kind === "hidden" ? example.hidden : true)
                        style: example.folderStyle
                        label: modelData.name
                        iconSource: Qt.resolvedUrl("Theme/icons/folder.svg")
                        compactHeight: 28
                        largeHeight: 64
                        iconSmall: 16
                        iconLarge: 34
                        textSize: root.baseFont - 1
                        textColor: root.textColor
                        textBold: index === 0 && example.preview  // under the pointer
                        batchText: modelData.kind === "suggestion" ? "€" : ""
                        badgeOpacity: modelData.kind === "suggestion" ? root.embryoBadgeOpacity : 1.0
                        fillColor: example.fill(modelData.kind)
                        strokeColor: example.stroke(modelData.kind)
                    }
                }
            }
            Rectangle {
                // The preview of "Aufträge", the folder under the pointer.
                visible: example.preview
                width: previewRow.implicitWidth + 16
                height: previewRow.implicitHeight + 12
                radius: 6
                color: example.previewBackground ? Qt.rgba(root.pill.r, root.pill.g, root.pill.b, 0.55) : "transparent"
                border.color: example.previewBackground ? root.pillBorder : "transparent"
                Row {
                    id: previewRow
                    x: 8
                    y: 6
                    spacing: 6
                    Repeater {
                        model: ["2025", "2026", "Angebote"]
                        FolderItem {
                            style: "text"
                            label: modelData
                            compactHeight: 24
                            textSize: root.baseFont - 2
                            textColor: root.textColor
                            fillColor: root.pill
                            strokeColor: root.pillBorder
                        }
                    }
                }
            }
        }
    }

    // One value of the settings file as a slider, with its default and a line saying what it
    // does.
    component SettingSlider: ColumnLayout {
        id: row
        property string key: ""
        property string label: ""
        property string help: ""
        property int labelWidth: 180
        property string unit: ""   // "%" shows shares as percent, "R" as shares of the radius
        property color mark: "transparent"  // the colour of its line in the small crown
        property alias value: slider.value
        property real stored: root.settings ? Number(root.settings.setting(key)) : 0
        property var limits: root.settings ? root.settings.settingLimits(key) : [0, 1]
        readonly property string demo: key.split("/").pop()
        spacing: 2
        HoverHandler {
            onHoveredChanged: {
                if (hovered) root.hoveredDemo = row.demo
                else {
                    if (root.hoveredDemo === row.demo) root.hoveredDemo = ""
                    if (root.quieted === row.demo) root.quieted = ""
                }
            }
        }
        RowLayout {
        objectName: "row_" + row.key
        spacing: 12
        Layout.fillWidth: true
        Rectangle {
            width: 10
            height: 10
            radius: 5
            color: row.mark
        }
        Text {
            text: row.label
            color: root.textColor
            font.pixelSize: root.baseFont
            wrapMode: Text.WordWrap
            Layout.preferredWidth: row.labelWidth
        }
        Slider {
            id: slider
            objectName: "setting_" + row.key
            from: row.limits[0]
            to: row.limits[1]
            value: row.stored
            stepSize: (to - from) / 100
            Layout.fillWidth: true
            Layout.minimumWidth: 120
            onPressedChanged: {
                root.slidersHeld += pressed ? 1 : -1
                if (pressed) root.quieted = row.demo
            }
            onValueChanged: {
                if (!root.settings || Math.abs(value - row.stored) < 1e-9) return
                if (root.settings.setSetting(row.key, value)) row.stored = value
            }
        }
        Text {
            text: row.unit === "%" ? Math.round(slider.value * 100) + " %"
                : (row.unit === "R" ? slider.value.toFixed(2) + " R" : slider.value.toFixed(2))
            color: root.textColor
            font.pixelSize: root.baseFont
            Layout.preferredWidth: 60
        }
        Pill {
            objectName: "reset_" + row.key
            label: qsTr("Default")
            onActivated: {
                if (!root.settings) return
                root.settings.resetSetting(row.key)
                row.stored = Number(root.settings.setting(row.key))
                slider.value = row.stored
            }
        }
        }
        Text {
            objectName: "help_" + row.key
            text: row.help
            color: root.mutedColor
            font.pixelSize: root.baseFont - 1
            wrapMode: Text.WordWrap
            leftPadding: 22
            Layout.fillWidth: true
            Layout.bottomMargin: 6
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            // Top left, where ⚙ is on the front: one turns the panel back where one turned it.
            Layout.fillWidth: true
            spacing: 16
            Pill {
                objectName: "setupFlipBack"
                label: "⚙  " + qsTr("Done")
                onActivated: root.flipBack()
            }
            Text {
                objectName: "setupTitle"
                text: qsTr("Setup")
                color: root.textColor
                font.pixelSize: root.baseFont + 8
                font.bold: true
                Layout.fillWidth: true
            }
        }

        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { objectName: "tabGeneral"; text: qsTr("General") }
            TabButton { objectName: "tabScope"; text: qsTr("Scope") }
            TabButton { objectName: "tabHeadline"; text: qsTr("Headline") }
            TabButton { objectName: "tabSunTree"; text: qsTr("SunTree") }
        }

        StackLayout {
            currentIndex: tabs.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {  // General
                spacing: 12
                RowLayout {
                    spacing: 12
                    Text { text: qsTr("Appearance"); color: root.textColor; font.pixelSize: root.baseFont; Layout.preferredWidth: 180 }
                    Pill {
                        objectName: "setupTheme"
                        label: root.darkTheme ? qsTr("Light") : qsTr("Dark")
                        onActivated: root.switchTheme()
                    }
                }
                RowLayout {
                    spacing: 12
                    Text { text: qsTr("Language"); color: root.textColor; font.pixelSize: root.baseFont; Layout.preferredWidth: 180 }
                    Pill {
                        objectName: "setupLanguage"
                        label: root.language.toUpperCase()
                        onActivated: root.switchLanguage()
                    }
                }
                // For the user embryos are "suggested MyOS folders" (the code keeps embryo): the
                // examples left, a suggestion beside a present one; the two sliders right of them.
                RowLayout {
                    spacing: 28
                    Layout.fillWidth: true
                    Grid {
                        // The live preview, in each style Scope draws folders in (text only, small
                        // icon, large icon), drawn as Scope's rows draw them: fill and frame pale,
                        // the badge as its own slider says.
                        columns: 2
                        columnSpacing: 16
                        rowSpacing: 10
                        leftPadding: 22
                        Layout.alignment: Qt.AlignTop
                        Repeater {
                            model: [{ style: "text", suggestion: true }, { style: "text", suggestion: false },
                                    { style: "smallIcon", suggestion: true }, { style: "smallIcon", suggestion: false },
                                    { style: "largeIcon", suggestion: true }, { style: "largeIcon", suggestion: false }]
                            FolderItem {
                                objectName: (modelData.suggestion ? "suggestionPreview_" : "presentPreview_") + modelData.style
                                style: modelData.style
                                width: 130
                                label: modelData.suggestion ? qsTr("Suggestion") : qsTr("Present")
                                iconSource: Qt.resolvedUrl("Theme/icons/folder.svg")
                                compactHeight: 30
                                largeHeight: 76
                                iconSmall: 18
                                iconLarge: 44
                                textSize: root.baseFont
                                batchText: "€"
                                fillColor: Qt.rgba(root.pill.r, root.pill.g, root.pill.b, modelData.suggestion ? root.embryoOpacity : 1.0)
                                strokeColor: Qt.rgba(root.pillBorder.r, root.pillBorder.g, root.pillBorder.b, modelData.suggestion ? root.embryoOpacity : 1.0)
                                textColor: root.textColor
                                badgeOpacity: modelData.suggestion ? root.embryoBadgeOpacity : 1.0
                            }
                        }
                    }
                    ColumnLayout {
                        spacing: 12
                        Layout.alignment: Qt.AlignTop
                        Layout.fillWidth: true
                        Layout.maximumWidth: 560
                        SettingSlider {
                            id: embryoSlider
                            key: "General/embryoOpacity"
                            label: qsTr("Suggested MyOS folders")
                            labelWidth: 130
                            unit: "%"
                            Layout.fillWidth: true
                            help: qsTr("How pale MyOS folders appear that are only suggested here, not made yet.")
                        }
                        SettingSlider {
                            id: badgeSlider
                            key: "General/embryoBadgeOpacity"
                            label: qsTr("Their badges")
                            labelWidth: 130
                            unit: "%"
                            Layout.fillWidth: true
                            help: qsTr("How pale the badges (€, § ...) on suggested MyOS folders are.")
                        }
                    }
                }
                Text {
                    text: qsTr("Colour schemes come here next.")
                    color: root.mutedColor
                    font.pixelSize: root.baseFont
                }
                Item { Layout.fillHeight: true }
            }

            Flickable {  // Scope: the example left, what it shows set on the right
                contentHeight: scopeTab.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                RowLayout {
                    id: scopeTab
                    width: parent.width
                    spacing: 28
                    RowsExample {
                        objectName: "rowsExample"
                        Layout.alignment: Qt.AlignTop
                        pathBar: root.pathBarOn
                        preview: root.previewOn
                        previewBackground: root.previewBackgroundOn
                        suggestions: root.showSuggestionsOn
                        hidden: root.showHiddenOn
                        folderStyle: root.templatesStyle
                    }
                    ColumnLayout {
                        spacing: 6
                        Layout.alignment: Qt.AlignTop
                        Layout.fillWidth: true
                        Heading { text: qsTr("Display") }
                        RowLayout {
                            // The MyOS folders' row is the upper one.
                            spacing: 8
                            CheckItem {
                                objectName: "checkTemplatesRow"
                                label: qsTr("MyOS folders")
                                checked: root.templatesRowShown
                                onToggled: root.toggleTemplatesRow()
                                Layout.preferredWidth: 118
                            }
                            Choices {
                                prefix: "templatesStyle"
                                options: [{ value: "text", label: qsTr("Text") }, { value: "smallIcon", label: qsTr("Small") }, { value: "largeIcon", label: qsTr("Large") }]
                                current: root.templatesStyle
                                onChosen: function(value) { root.templatesStyle = value; root.keep("Scope/templatesStyle", value) }
                            }
                        }
                        RowLayout {
                            spacing: 8
                            CheckItem {
                                objectName: "checkProjectsRow"
                                label: qsTr("Projects")
                                checked: root.projectsRowShown
                                onToggled: root.toggleProjectsRow()
                                Layout.preferredWidth: 118
                            }
                            Choices {
                                prefix: "projectsStyle"
                                options: [{ value: "text", label: qsTr("Text") }, { value: "smallIcon", label: qsTr("Small") }, { value: "largeIcon", label: qsTr("Large") }]
                                current: root.projectsStyle
                                onChosen: function(value) { root.projectsStyle = value; root.keep("Scope/projectsStyle", value) }
                            }
                        }
                        Heading { text: qsTr("Both rows show") }
                        CheckItem {
                            objectName: "checkPathBar"
                            label: qsTr("Path bar")
                            checked: root.pathBarOn
                            onToggled: { root.pathBarOn = !root.pathBarOn; root.keep("Scope/pathBar", root.pathBarOn) }
                        }
                        CheckItem {
                            objectName: "checkSuggestions"
                            label: qsTr("Suggested MyOS folders")
                            checked: root.showSuggestionsOn
                            onToggled: { root.showSuggestionsOn = !root.showSuggestionsOn; root.keep("Scope/showSuggestions", root.showSuggestionsOn) }
                        }
                        CheckItem {
                            objectName: "checkHidden"
                            label: qsTr("Hidden folders")
                            checked: root.showHiddenOn
                            onToggled: { root.showHiddenOn = !root.showHiddenOn; root.keep("Scope/showHidden", root.showHiddenOn) }
                        }
                        CheckItem {
                            objectName: "checkPreview"
                            label: qsTr("Preview")
                            checked: root.previewOn
                            onToggled: { root.previewOn = !root.previewOn; root.keep("Scope/preview", root.previewOn) }
                        }
                        CheckItem {
                            objectName: "checkPreviewBackground"
                            label: qsTr("Preview background")
                            checked: root.previewBackgroundOn
                            onToggled: { root.previewBackgroundOn = !root.previewBackgroundOn; root.keep("Scope/previewBackground", root.previewBackgroundOn) }
                        }
                        Heading { text: qsTr("Preview behaviour") }
                        CheckItem {
                            objectName: "checkInstantReopen"
                            label: qsTr("Reopen at once")
                            checked: root.instantReopenOn
                            onToggled: { root.instantReopenOn = !root.instantReopenOn; root.keep("Scope/instantReopen", root.instantReopenOn) }
                        }
                        RowLayout {
                            spacing: 12
                            Text { text: qsTr("Timing"); color: root.textColor; font.pixelSize: root.baseFont; Layout.preferredWidth: 100 }
                            Choices {
                                prefix: "tuning"
                                options: [{ value: "soft", label: qsTr("Soft") }, { value: "balanced", label: qsTr("Balanced") }, { value: "aggressive", label: qsTr("Quick") }]
                                current: root.previewTuning
                                onChosen: function(value) { root.previewTuning = value; root.keep("Scope/previewTuning", value) }
                            }
                        }
                        Text {
                            text: qsTr("Soft waits longer before the preview opens and closes it slowly; quick answers at once.")
                            color: root.mutedColor
                            font.pixelSize: root.baseFont - 1
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            ColumnLayout {  // Headline
                Text {
                    text: qsTr("The Headline's settings come here with the Headline.")
                    color: root.mutedColor
                    font.pixelSize: root.baseFont
                }
                Item { Layout.fillHeight: true }
            }

            RowLayout {  // SunTree: the crown (SunTree/Designdocument Krone.md, 5)
                spacing: 24
                CrownPreview {
                    // What the values do, at once: SunTree's arithmetic on sample folders.
                    id: crownPreview
                    objectName: "crownPreview"
                    Layout.preferredWidth: 220
                    Layout.preferredHeight: 420
                    Layout.alignment: Qt.AlignTop
                    darkTheme: root.darkTheme
                    lineT: lineTSlider.value
                    inner: innerSlider.value
                    enter: enterSlider.value
                    leave: leaveSlider.value
                    lens: lensSlider.value
                    softness: softnessSlider.value
                    edge: edgeSlider.value
                    demo: root.demo
                }
                ColumnLayout {
                    spacing: 8
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    // For the user: SunTree is "the folder fan", drawing in is "the change" (the
                    // design documents keep crown and drawing in). From the inside out, as the
                    // lines lie in the small crown; then the three that are no line.
                    Text {
                        text: qsTr("The folder fan for quick dropping. It reads these when it appears next. Move the mouse through the small fan on the left: it answers as the real one does. Over a slider it shows what the slider changes.")
                        color: root.mutedColor
                        font.pixelSize: root.baseFont
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.bottomMargin: 8
                    }
                    SettingSlider { id: innerSlider; key: "SunTree/inner"; label: qsTr("Size of the middle"); unit: "R"; mark: crownPreview.innerColor; Layout.fillWidth: true
                        help: qsTr("The empty middle at the stem: every level starts there, and back there the fan lets go.") }
                    SettingSlider { id: leaveSlider; key: "SunTree/leave"; label: qsTr("Landing"); unit: "%"; mark: crownPreview.leaveColor; Layout.fillWidth: true
                        help: qsTr("How far among the subfolders you already are after the change.") }
                    SettingSlider { id: lineTSlider; key: "SunTree/lineT"; label: qsTr("Way per level"); unit: "R"; mark: crownPreview.lineColor; Layout.fillWidth: true
                        help: qsTr("How far you move the mouse outward until the folder fills the whole fan and you go one level deeper.") }
                    SettingSlider { id: enterSlider; key: "SunTree/enter"; label: qsTr("Change begins"); unit: "%"; mark: crownPreview.enterColor; Layout.fillWidth: true
                        help: qsTr("How deep in the folder the pointer is when the change into its subfolders begins.") }
                    SettingSlider { id: lensSlider; key: "SunTree/lens"; label: qsTr("Magnifier"); Layout.fillWidth: true
                        help: qsTr("How much the folder under the pointer is enlarged already at the start of a level.") }
                    SettingSlider { id: softnessSlider; key: "SunTree/softness"; label: qsTr("Softness"); Layout.fillWidth: true
                        help: qsTr("How fast everything follows the hand: smaller is softer, larger is more direct.") }
                    SettingSlider { id: edgeSlider; key: "SunTree/edge"; label: qsTr("Exit at the edge"); unit: "R"; mark: crownPreview.exitColor; Layout.fillWidth: true
                        help: qsTr("How far you push past the first or last folder until the fan lets go (the rim running on, green).") }
                }
            }
        }
    }
}
