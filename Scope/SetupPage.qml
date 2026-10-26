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
    property bool projectsRowShown: true
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

    // One value of the settings file as a slider, with its default and a line saying what it
    // does.
    component SettingSlider: ColumnLayout {
        id: row
        property string key: ""
        property string label: ""
        property string help: ""
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
            Layout.preferredWidth: 180
        }
        Slider {
            id: slider
            objectName: "setting_" + row.key
            from: row.limits[0]
            to: row.limits[1]
            value: row.stored
            stepSize: (to - from) / 100
            Layout.fillWidth: true
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
            Layout.preferredWidth: 70
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
                // For the user embryos are "suggested MyOS folders" (the code keeps embryo).
                SettingSlider {
                    id: embryoSlider
                    key: "General/embryoOpacity"
                    label: qsTr("Suggested MyOS folders")
                    unit: "%"
                    Layout.fillWidth: true
                    help: qsTr("How pale MyOS folders appear that are only suggested here, not made yet.")
                }
                SettingSlider {
                    id: badgeSlider
                    key: "General/embryoBadgeOpacity"
                    label: qsTr("Their badges")
                    unit: "%"
                    Layout.fillWidth: true
                    help: qsTr("How pale the badges (€, § ...) on suggested MyOS folders are.")
                }
                Grid {
                    // The live preview: a present MyOS folder beside a suggestion, in each style
                    // Scope draws folders in (text only, small icon, large icon), drawn as Scope's
                    // rows draw them: fill and frame pale, the badge as its own slider says.
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 10
                    leftPadding: 22
                    Repeater {
                        model: [{ style: "text", suggestion: false }, { style: "text", suggestion: true },
                                { style: "smallIcon", suggestion: false }, { style: "smallIcon", suggestion: true },
                                { style: "largeIcon", suggestion: false }, { style: "largeIcon", suggestion: true }]
                        FolderItem {
                            objectName: (modelData.suggestion ? "suggestionPreview_" : "presentPreview_") + modelData.style
                            style: modelData.style
                            width: 150
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
                Text {
                    text: qsTr("Colour schemes come here next.")
                    color: root.mutedColor
                    font.pixelSize: root.baseFont
                }
                Item { Layout.fillHeight: true }
            }

            ColumnLayout {  // Scope
                spacing: 12
                RowLayout {
                    spacing: 12
                    Text { text: qsTr("Rows"); color: root.textColor; font.pixelSize: root.baseFont; Layout.preferredWidth: 180 }
                    Pill {
                        objectName: "setupProjectsRow"
                        label: qsTr("Projects") + " " + (root.projectsRowShown ? qsTr("ON") : qsTr("OFF"))
                        onActivated: root.toggleProjectsRow()
                    }
                    Pill {
                        objectName: "setupTemplatesRow"
                        label: qsTr("MyOS folders") + " " + (root.templatesRowShown ? qsTr("ON") : qsTr("OFF"))
                        onActivated: root.toggleTemplatesRow()
                    }
                }
                Text {
                    text: qsTr("Views of their own come here later.")
                    color: root.mutedColor
                    font.pixelSize: root.baseFont
                }
                Item { Layout.fillHeight: true }
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
