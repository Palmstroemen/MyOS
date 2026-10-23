import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Move into New Folder")
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
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Apply"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
        // "Apply" is the default: highlighted, and Return in the name field presses it.
        var applyButton = root.standardButton(Dialog.Ok)
        if (applyButton) applyButton.highlighted = true
        folderBatchNameInput.forceActiveFocus()
        folderBatchNameInput.selectAll()
    }
    onAccepted: {
        var folderName = String(folderBatchNameInput.text || "").trim()
        if (!folderName) {
            window.pendingFolderBatchSources = []
            window.pendingFolderBatchName = qsTr("New Folder")
            return
        }
        if (!window.hasBackend() || typeof backend.createFolder !== "function") {
            window.pendingFolderBatchSources = []
            window.pendingFolderBatchName = qsTr("New Folder")
            return
        }
        var targetPath = backend.createFolder(window.cwp, folderName)
        if (!targetPath || targetPath.length === 0) {
            window.moveReportMessage = qsTr("Could not create target folder \"%1\".").arg(folderName)
            window.moveReportDialog.open()
            window.pendingFolderBatchSources = []
            window.pendingFolderBatchName = qsTr("New Folder")
            return
        }
        window._performMove(window.pendingFolderBatchSources, targetPath)
        window.pendingFolderBatchSources = []
        window.pendingFolderBatchName = qsTr("New Folder")
    }
    onRejected: {
        window.pendingFolderBatchSources = []
        window.pendingFolderBatchName = qsTr("New Folder")
    }
    contentItem: Column {
        spacing: 10
        Text {
            text: qsTr("Create a folder and move the selected entries into it.")
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        TextField {
            id: folderBatchNameInput
            text: window.pendingFolderBatchName
            placeholderText: qsTr("New folder name")
            selectByMouse: true
            Keys.onReturnPressed: root.accept()
            Keys.onEnterPressed: root.accept()
            Keys.onEscapePressed: root.reject()
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
