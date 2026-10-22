import QtQuick 2.15
import QtQuick.Controls 2.15
import "../js/PathUtils.js" as PathUtils

// Asked only when a project that is to become an ordinary folder again has settings of its
// own (changed rights, tags, a trash, ...): they are not deleted but go into the parent
// project's trash as "MyOS settings" (see core/project_unmake.py).
Dialog {
    id: root
    required property var window
    property string targetPath: ""
    property var ownNames: []

    title: qsTr("No longer a project")
    modal: true
    focus: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(440, Math.round(window.width * 0.32))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }

    function openFor(path, names) {
        targetPath = path
        ownNames = names || []
        open()
    }

    onOpened: {
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Make it a folder"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
    }
    onAccepted: window.removeProjectAt(targetPath, true)

    contentItem: Text {
        width: Math.max(120, root.width - 32)
        text: qsTr("“%1” has settings of its own: %2. They are not deleted: they go into the trash of the project above, as “MyOS settings”, and can be restored from there.")
            .arg(PathUtils.basename(root.targetPath)).arg(root.ownNames.join(", "))
        wrapMode: Text.WordWrap
        color: window.dialogTextStrong
        font.pixelSize: window.baseFont
    }
}
