import QtQuick 6.7
import QtQuick.Controls 2.15

// Rights of one group on the folder shown in the FilesPanel (right click on its ACL chip).
// Same look and wording as PostFix's ACLRoleEditor: one switch per right in the chip
// pictogram (◂ read, ▸ write, x, c, d) with "✓ may …" / "✗ may not …" next to it.
// See "Designdocument ACLs.md", 5.3.
Dialog {
    id: root
    required property var window
    property string folderPath: ""
    property string roleKey: ""
    property string roleName: ""
    property bool ownRule: false
    property var chosen: ({})
    property string errorText: ""
    readonly property var rightRows: [
        { right: "read", symbol: "◂", verb: qsTr("read") },
        { right: "write", symbol: "▸", verb: qsTr("write") },
        { right: "execute", symbol: "x", verb: qsTr("execute") },
        { right: "change", symbol: "c", verb: qsTr("change rights") },
        { right: "delete", symbol: "d", verb: qsTr("delete") }
    ]
    /// Emitted after the rights were written (the panel recomputes its summary).
    signal rightsChanged()

    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    width: Math.max(360, Math.round(window.width * 0.26))
    padding: 14
    Overlay.modal: Rectangle { color: "black"; opacity: 0.25 }
    // The greys of the ACL chips.
    background: Rectangle {
        radius: 8
        color: "#cfcfcf"
        border.color: "#9a9a9a"
    }

    function openFor(path, key, name, rights) {
        folderPath = path
        roleKey = key
        roleName = name
        var next = {}
        for (var i = 0; i < (rights || []).length; i++) next[rights[i]] = true
        chosen = next
        errorText = ""
        // backend is the engine's context property (not a property of window).
        ownRule = window.hasBackend() && backend.aclHasOwnRule(path, key)
        open()
    }

    function toggle(right) {
        var next = {}
        for (var k in chosen) next[k] = chosen[k]
        next[right] = !next[right]
        chosen = next
    }

    function chosenList() {
        var out = []
        for (var i = 0; i < rightRows.length; i++) {
            if (chosen[rightRows[i].right]) out.push(rightRows[i].right)
        }
        return out
    }

    function apply(rights) {
        var result = backend.aclSetRoleRights(folderPath, roleKey, rights)
        if (result && result.ok) {
            close()
            rightsChanged()
            return
        }
        errorText = result && result.reason === "permission"
            ? qsTr("You may not change the rights here.")
            : result && result.reason === "lockout"
            ? qsTr("You would lose your own right to change the rights.")
            : String((result && result.message) || qsTr("The rights could not be changed."))
    }

    contentItem: Column {
        spacing: 8

        Text {
            width: parent.width
            text: qsTr("Rights of %1 for this folder").arg(root.roleName)
            font.bold: true
            font.pixelSize: root.window.baseFont
            color: "#333333"
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width
            text: qsTr("Control exactly what this group may do with this folder.")
            font.pixelSize: root.window.baseFont * 0.9
            color: "#333333"
            wrapMode: Text.WordWrap
        }

        Repeater {
            model: root.rightRows
            delegate: Row {
                readonly property bool on: !!root.chosen[modelData.right]
                spacing: 8

                // A chip-shaped switch: square left edge, rounded right edge.
                Rectangle {
                    objectName: "aclSwitch_" + modelData.right
                    width: 40
                    height: Math.round(root.window.baseFont * 1.7)
                    radius: height / 2
                    topLeftRadius: 2
                    bottomLeftRadius: 2
                    color: parent.on ? "#b5b5b5" : "#e4e4e4"
                    border.color: switchMouse.containsMouse ? Qt.rgba(0, 0, 0, 0.43) : Qt.rgba(0, 0, 0, 0.24)
                    Text {
                        anchors.centerIn: parent
                        text: modelData.symbol
                        font.bold: parent.parent.on
                        font.pixelSize: root.window.baseFont * 0.9
                        color: "#333333"
                    }
                    MouseArea {
                        id: switchMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggle(modelData.right)
                    }
                }
                Text {
                    objectName: "aclMeaning_" + modelData.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: parent.on
                        ? "✓ " + qsTr("may %1").arg(modelData.verb)
                        : "✗ " + qsTr("may not %1").arg(modelData.verb)
                    color: parent.on ? "#333333" : "#777777"
                    font.pixelSize: root.window.baseFont * 0.9
                }
            }
        }

        Text {
            width: parent.width
            text: root.ownRule
                ? qsTr("This folder has a rule of its own.")
                : qsTr("These rights are inherited from the parent folder.")
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
                objectName: "aclApply"
                text: qsTr("Apply")
                onClicked: root.apply(root.chosenList())
            }
            Button {
                objectName: "aclReset"
                text: qsTr("Back to inherited")
                enabled: root.ownRule
                onClicked: root.apply(null)
            }
            Button {
                text: qsTr("Cancel")
                onClicked: root.close()
            }
        }
    }
}
