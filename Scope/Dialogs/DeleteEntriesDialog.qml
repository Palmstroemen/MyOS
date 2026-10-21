import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: window.pendingDeleteHasFolders ? qsTr("Delete") : qsTr("Delete Files")
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
    onOpened: {
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Delete"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
    }
    onAccepted: {
        window.performDeleteEntries(window.pendingDeletePaths)
        window.pendingDeletePaths = []
    }
    onRejected: window.pendingDeletePaths = []
    contentItem: Text {
        width: Math.max(120, root.width - 32)
        text: window.pendingDeleteHasFolders
            ? qsTr("Entries to delete: %1. Folders go with all their contents. They are moved to the trash and can be restored from there.")
                .arg(window.pendingDeletePaths.length)
            : qsTr("Move %1 files to the trash?").arg(window.pendingDeletePaths.length)
        wrapMode: Text.WordWrap
        color: window.dialogTextStrong
        font.pixelSize: window.baseFont
    }
}
