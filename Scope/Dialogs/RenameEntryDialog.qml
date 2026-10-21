import QtQuick 2.15
import QtQuick.Controls 2.15
import "../js/PathUtils.js" as PathUtils

Dialog {
    id: root
    required property var window
    title: qsTr("Rename")
    modal: true
    focus: true
    standardButtons: Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(420, Math.round(window.width * 0.30))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: {
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
        renameEntryInput.forceActiveFocus()
        renameEntryInput.selectAll()
    }
    onAccepted: {
        var nextName = String(renameEntryInput.text || "").trim()
        if (!nextName) {
            window.pendingRenamePath = ""
            window.pendingRenameName = ""
            return
        }
        var renamed = backend.renameEntry(window.pendingRenamePath, nextName)
        if (!renamed || renamed.length === 0) {
            window.moveReportMessage = qsTr("Could not rename \"%1\".").arg(PathUtils.basename(window.pendingRenamePath))
            window.moveReportDialog.open()
            window.pendingRenamePath = ""
            window.pendingRenameName = ""
            return
        }
        window.selectedEntryPaths = [renamed]
        window.updateFiles()
        window.pendingRenamePath = ""
        window.pendingRenameName = ""
    }
    onRejected: {
        window.pendingRenamePath = ""
        window.pendingRenameName = ""
    }
    contentItem: Column {
        spacing: 8
        Text {
            text: qsTr("Enter a new name and press Return to apply.")
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        TextField {
            id: renameEntryInput
            text: window.pendingRenameName
            placeholderText: qsTr("New name")
            selectByMouse: true
            color: window.dialogInputText
            placeholderTextColor: window.dialogInputPlaceholder
            topPadding: 10
            bottomPadding: 10
            leftPadding: 12
            rightPadding: 12
            background: Rectangle {
                radius: 12
                color: window.dialogInputBg
                border.color: window.dialogInputBorder
                border.width: 2
            }
            Keys.onReturnPressed: root.accept()
            Keys.onEnterPressed: root.accept()
            Keys.onEscapePressed: root.reject()
        }
    }
}
