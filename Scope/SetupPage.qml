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
    property int baseFont: 13
    property color textColor: darkTheme ? "#e8efff" : "#1a2233"
    property color mutedColor: darkTheme ? "#9fb0cc" : "#4a5670"
    property color panelColor: darkTheme ? "#1a2230" : "#eef1f8"
    property color pill: darkTheme ? "#2c3f5d" : "#dfe3f0"
    property color pillBorder: darkTheme ? "#5f7297" : "#c6ccdf"
    property alias currentTab: tabs.currentIndex

    signal switchTheme()
    signal switchLanguage()
    signal flipBack()

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

    // One value of the settings file as a slider, with its default.
    component SettingSlider: RowLayout {
        id: row
        property string key: ""
        property string label: ""
        property string unit: ""   // "%" shows shares as percent, "R" as shares of the radius
        property real stored: root.settings ? Number(root.settings.setting(key)) : 0
        property var limits: root.settings ? root.settings.settingLimits(key) : [0, 1]
        spacing: 12
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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Setup")
                color: root.textColor
                font.pixelSize: root.baseFont + 8
                font.bold: true
                Layout.fillWidth: true
            }
            Pill {
                objectName: "setupFlipBack"
                label: "⚙  " + qsTr("Done")
                onActivated: root.flipBack()
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
                Text {
                    text: qsTr("Colour schemes come here next.")
                    color: root.mutedColor
                    font.pixelSize: root.baseFont
                }
                Item { Layout.fillHeight: true }
            }

            ColumnLayout {  // Scope
                Text {
                    text: qsTr("Scope's settings come here as its top bar is taken away.")
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

            ColumnLayout {  // SunTree: the crown (SunTree/Designdocument Krone.md, 5)
                spacing: 8
                Text {
                    text: qsTr("SunTree reads these when it appears next.")
                    color: root.mutedColor
                    font.pixelSize: root.baseFont
                }
                SettingSlider { key: "SunTree/lineT"; label: qsTr("Line T"); unit: "R"; Layout.fillWidth: true }
                SettingSlider { key: "SunTree/inner"; label: qsTr("Inner radius"); unit: "R"; Layout.fillWidth: true }
                SettingSlider { key: "SunTree/enter"; label: qsTr("Drawing in begins at"); unit: "%"; Layout.fillWidth: true }
                SettingSlider { key: "SunTree/leave"; label: qsTr("Drawing in ends at"); unit: "%"; Layout.fillWidth: true }
                SettingSlider { key: "SunTree/lens"; label: qsTr("Fish-eye"); Layout.fillWidth: true }
                SettingSlider { key: "SunTree/softness"; label: qsTr("Softness"); Layout.fillWidth: true }
                SettingSlider { key: "SunTree/edge"; label: qsTr("Letting go at the end"); unit: "R"; Layout.fillWidth: true }
                Item { Layout.fillHeight: true }
            }
        }
    }
}
