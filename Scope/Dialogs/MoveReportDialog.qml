import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Move Report")
    modal: true
    focus: true
    standardButtons: Dialog.Ok
    anchors.centerIn: Overlay.overlay
    width: Math.max(520, Math.round(window.width * 0.42))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: window._setDialogButtonText(root, Dialog.Ok, qsTr("Close"))
    onAccepted: window.moveReportMessage = ""
    onRejected: window.moveReportMessage = ""
    contentItem: Text {
        text: window.moveReportMessage
        wrapMode: Text.WordWrap
        color: window.dialogTextStrong
        font.pixelSize: window.baseFont
    }
}
