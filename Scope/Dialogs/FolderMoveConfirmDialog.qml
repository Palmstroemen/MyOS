import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Confirm Folder Move")
    modal: true
    focus: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(440, Math.round(window.width * 0.34))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: {
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Apply"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
    }
    onAccepted: {
        window._performMove(window.pendingMoveSources, window.pendingMoveTargetDir)
        window.pendingMoveSources = []
        window.pendingMoveTargetDir = ""
        window.pendingMoveMessage = ""
    }
    onRejected: {
        window.pendingMoveSources = []
        window.pendingMoveTargetDir = ""
        window.pendingMoveMessage = ""
    }
    contentItem: Text {
        text: window.pendingMoveMessage
        wrapMode: Text.WordWrap
        color: window.dialogTextStrong
        font.pixelSize: window.baseFont
    }
}
