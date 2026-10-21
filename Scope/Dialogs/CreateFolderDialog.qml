import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Create new folder")
    modal: true
    focus: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(420, Math.round(window.width * 0.32))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: {
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Create"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
        createFolderNameInput.forceActiveFocus()
        createFolderNameInput.selectAll()
    }
    onAccepted: {
        var folderName = String(createFolderNameInput.text || "").trim()
        var targetPath = String(window.pendingCreateFolderTargetPath || "").trim()
        if (!folderName || !targetPath) {
            window.pendingCreateFolderName = qsTr("New Folder")
            window.pendingCreateFolderTargetPath = ""
            return
        }
        if (!window.hasBackend() || typeof window.backend.createFolder !== "function") {
            window.pendingCreateFolderName = qsTr("New Folder")
            window.pendingCreateFolderTargetPath = ""
            return
        }
        var createdPath = window.backend.createFolder(targetPath, folderName)
        if (!createdPath || createdPath.length === 0) {
            window.moveReportMessage = qsTr("Could not create folder \"%1\".").arg(folderName)
            window.moveReportDialog.open()
            window.pendingCreateFolderName = qsTr("New Folder")
            window.pendingCreateFolderTargetPath = ""
            return
        }
        window.updateSubProjects()
        window.updateTemplates()
        window.standardFolders = window.listTemplates(window.templatesListingPath())
        window.updateStandardFolders()
        window.updateFiles()
        window.pendingCreateFolderName = qsTr("New Folder")
        window.pendingCreateFolderTargetPath = ""
    }
    onRejected: {
        window.pendingCreateFolderName = qsTr("New Folder")
        window.pendingCreateFolderTargetPath = ""
    }
    contentItem: Column {
        spacing: 10
        Text {
            text: qsTr("Target folder: %1").arg(String(window.pendingCreateFolderTargetPath || ""))
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        TextField {
            id: createFolderNameInput
            text: window.pendingCreateFolderName
            placeholderText: qsTr("New folder name")
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
