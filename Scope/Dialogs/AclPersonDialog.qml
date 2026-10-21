import QtQuick 6.7
import QtQuick.Controls 2.15

// Groups of one person (right click on a person's ACL chip). People have no rules of their
// own: their rights come from their groups, written in "# Users" of ACLs.md and valid in
// the whole project. Next to each group: what it may do in the folder shown, so one sees
// where the person's rights here come from. See "Designdocument ACLs.md", 5.3.
Dialog {
    id: root
    required property var window
    property string folderPath: ""
    property string userKey: ""
    property string userName: ""
    property var groups: []
    property var chosen: ({})
    property string errorText: ""
    // All switches as wide as the longest name in bold (a switched-on group is drawn
    // bold), so the explanations line up.
    property real switchWidth: 90
    readonly property var rightWords: ({
        "read": qsTr("read"),
        "write": qsTr("write"),
        "execute": qsTr("execute"),
        "change": qsTr("change rights"),
        "delete": qsTr("delete")
    })
    /// Emitted after the groups were written (the panel recomputes its summary).
    signal membershipChanged()

    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    width: Math.max(380, Math.round(window.width * 0.28))
    padding: 14
    Overlay.modal: Rectangle { color: "black"; opacity: 0.25 }
    // The greys of the ACL chips, like the group dialog.
    background: Rectangle {
        radius: 8
        color: "#cfcfcf"
        border.color: "#9a9a9a"
    }

    function openFor(path, key) {
        // backend is the engine's context property (not a property of window).
        var data = window.hasBackend() ? backend.aclUserGroups(path, key) : null
        if (!data || !data.groups) return
        folderPath = path
        userKey = key
        userName = data.name
        groups = data.groups
        var next = {}
        for (var i = 0; i < groups.length; i++) next[groups[i].key] = !!groups[i].member
        chosen = next
        var widest = 0
        for (var j = 0; j < groups.length; j++) {
            boldMetrics.text = groups[j].name
            widest = Math.max(widest, boldMetrics.advanceWidth)
        }
        switchWidth = Math.max(90, Math.ceil(widest) + 24)
        errorText = ""
        open()
    }

    TextMetrics {
        id: boldMetrics
        font.bold: true
        font.pixelSize: root.window.baseFont * 0.9
    }

    function toggle(key) {
        var next = {}
        for (var k in chosen) next[k] = chosen[k]
        next[key] = !next[key]
        chosen = next
    }

    function chosenList() {
        var out = []
        for (var i = 0; i < groups.length; i++) {
            if (chosen[groups[i].key]) out.push(groups[i].key)
        }
        return out
    }

    function hereText(rights) {
        if (!rights || rights.length === 0) return qsTr("here: no access")
        var words = []
        for (var i = 0; i < rights.length; i++) words.push(rightWords[rights[i]] || rights[i])
        return qsTr("here: %1").arg(words.join(", "))
    }

    function apply() {
        var result = backend.aclSetUserGroups(folderPath, userKey, chosenList())
        if (result && result.ok) {
            close()
            membershipChanged()
            return
        }
        errorText = result && result.reason === "permission"
            ? qsTr("You may not change the rights here.")
            : result && result.reason === "lockout"
            ? qsTr("You would lose your own right to change the rights.")
            : String((result && result.message) || qsTr("The groups could not be changed."))
    }

    contentItem: Column {
        spacing: 8

        Text {
            width: parent.width
            text: qsTr("Groups of %1").arg(root.userName)
            font.bold: true
            font.pixelSize: root.window.baseFont
            color: "#333333"
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width
            text: qsTr("People get their rights through their groups. Groups apply in the whole project, not only in this folder.")
            font.pixelSize: root.window.baseFont * 0.9
            color: "#333333"
            wrapMode: Text.WordWrap
        }

        ScrollView {
            id: groupScroll
            width: parent.width
            height: Math.min(groupColumn.implicitHeight, Math.round(root.window.height * 0.45))
            clip: true
            contentWidth: availableWidth

            Column {
                id: groupColumn
                width: groupScroll.availableWidth
                spacing: 6

                Repeater {
                    model: root.groups
                    delegate: Row {
                        readonly property bool on: !!root.chosen[modelData.key]
                        width: groupColumn.width
                        spacing: 8

                        // A chip-shaped switch with the group's name, like the ACL chips.
                        Rectangle {
                            id: groupSwitch
                            objectName: "aclGroupSwitch_" + modelData.key
                            width: root.switchWidth
                            height: Math.round(root.window.baseFont * 1.7)
                            radius: height / 2
                            topLeftRadius: 2
                            bottomLeftRadius: 2
                            color: parent.on ? "#b5b5b5" : "#e4e4e4"
                            border.color: groupMouse.containsMouse ? Qt.rgba(0, 0, 0, 0.43) : Qt.rgba(0, 0, 0, 0.24)
                            Text {
                                id: groupName
                                anchors.centerIn: parent
                                text: modelData.name
                                font.bold: parent.parent.on
                                font.pixelSize: root.window.baseFont * 0.9
                                color: "#333333"
                            }
                            MouseArea {
                                id: groupMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.toggle(modelData.key)
                            }
                        }
                        Text {
                            objectName: "aclGroupMeaning_" + modelData.key
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - groupSwitch.width - parent.spacing
                            wrapMode: Text.WordWrap
                            text: (parent.on ? "✓ " + qsTr("member") : "✗ " + qsTr("not a member"))
                                + " · " + root.hereText(modelData.rights)
                            color: parent.on ? "#333333" : "#777777"
                            font.pixelSize: root.window.baseFont * 0.9
                        }
                    }
                }
            }
        }

        Text {
            width: parent.width
            visible: root.chosenList().length === 0
            text: qsTr("Without groups %1 has no rights and is removed from the list.").arg(root.userName)
            color: "#555555"
            font.pixelSize: root.window.baseFont * 0.85
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width
            visible: root.errorText.length > 0
            text: root.errorText
            color: "#b00020"
            font.pixelSize: root.window.baseFont * 0.85
            wrapMode: Text.WordWrap
        }

        Row {
            spacing: 6
            Button {
                objectName: "aclGroupsApply"
                text: qsTr("Apply")
                onClicked: root.apply()
            }
            Button {
                text: qsTr("Cancel")
                onClicked: root.close()
            }
        }
    }
}
