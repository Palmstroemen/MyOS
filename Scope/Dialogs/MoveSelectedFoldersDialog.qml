import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("In neuen Ordner verschieben")
    modal: true
    focus: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(460, Math.round(window.width * 0.35))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: {
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Uebernehmen"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Abbrechen"))
        folderBatchNameInput.forceActiveFocus()
        folderBatchNameInput.selectAll()
    }
    onAccepted: {
        var folderName = String(folderBatchNameInput.text || "").trim()
        if (!folderName) {
            window.pendingFolderBatchSources = []
            window.pendingFolderBatchName = qsTr("Neuer Ordner")
            return
        }
        if (!window.hasBackend() || typeof window.backend.createFolder !== "function") {
            window.pendingFolderBatchSources = []
            window.pendingFolderBatchName = qsTr("Neuer Ordner")
            return
        }
        var targetPath = window.backend.createFolder(window.cwp, folderName)
        if (!targetPath || targetPath.length === 0) {
            window.moveReportMessage = qsTr("Konnte Zielordner \"%1\" nicht erstellen.").arg(folderName)
            window.moveReportDialog.open()
            window.pendingFolderBatchSources = []
            window.pendingFolderBatchName = qsTr("Neuer Ordner")
            return
        }
        window._performMove(window.pendingFolderBatchSources, targetPath)
        window.pendingFolderBatchSources = []
        window.pendingFolderBatchName = qsTr("Neuer Ordner")
    }
    onRejected: {
        window.pendingFolderBatchSources = []
        window.pendingFolderBatchName = qsTr("Neuer Ordner")
    }
    contentItem: Column {
        spacing: 10
        Text {
            text: qsTr("Erstellt einen Ordner und verschiebt die ausgewaehlten Eintraege hinein.")
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        TextField {
            id: folderBatchNameInput
            text: window.pendingFolderBatchName
            placeholderText: qsTr("Neuer Ordnername")
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
        }
    }
}
