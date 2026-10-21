import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Batch Rename Files")
    modal: true
    focus: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(480, Math.round(window.width * 0.36))
    contentWidth: Math.max(160, width - 36)
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
        batchRenameToInput.forceActiveFocus()
        batchRenameToInput.selectAll()
    }
    onAccepted: {
        var fromText = String(window.pendingBatchReplaceFrom || "")
        var toText = String(batchRenameToInput.text || "")
        if (fromText.length === 0) {
            window.moveReportMessage = qsTr("No shared search text found.")
            window.moveReportDialog.open()
            window.pendingBatchRenamePaths = []
            window.pendingBatchReplaceFrom = ""
            window.pendingBatchReplaceTo = ""
            return
        }
        if (!window.hasBackend() || typeof backend.renameEntriesBatch !== "function") {
            window.moveReportMessage = qsTr("Batch rename is not available in this mode.")
            window.moveReportDialog.open()
            window.pendingBatchRenamePaths = []
            window.pendingBatchReplaceFrom = ""
            window.pendingBatchReplaceTo = ""
            return
        }
        var report = backend.renameEntriesBatch(window.pendingBatchRenamePaths, fromText, toText) || {}
        var renamedPaths = (report.renamed && report.renamed.length) ? report.renamed : []
        var unchangedCount = Number(report.unchanged || 0)
        var failedCount = Number(report.failed || 0)
        window.pendingBatchRenamePaths = []
        window.pendingBatchReplaceFrom = ""
        window.pendingBatchReplaceTo = ""
        window.selectedEntryPaths = renamedPaths
        window.updateFiles()
        window.moveReportMessage = qsTr("Renamed: %1\nUnchanged: %2\nFailed: %3")
            .arg(renamedPaths.length)
            .arg(unchangedCount)
            .arg(failedCount)
        window.moveReportDialog.open()
    }
    onRejected: {
        window.pendingBatchRenamePaths = []
        window.pendingBatchReplaceFrom = ""
        window.pendingBatchReplaceTo = ""
    }
    contentItem: Column {
        width: root.contentWidth
        spacing: 12
        Text {
            width: parent.width
            text: qsTr("Rename \"%1\" to").arg(window.pendingBatchReplaceFrom)
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: Math.max(window.baseFont + 1, 14)
            font.bold: true
        }
        TextField {
            id: batchRenameToInput
            width: parent.width
            text: window.pendingBatchReplaceTo
            placeholderText: window.pendingBatchReplaceFrom.length > 0
                ? window.pendingBatchReplaceFrom
                : qsTr("New text")
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
        Text {
            width: parent.width
            text: qsTr("For name conflicts, (1), (2), ... will be appended automatically.")
            wrapMode: Text.WordWrap
            color: window.dialogTextMuted
            font.pixelSize: Math.max(window.baseFont - 1, 11)
        }
    }
}
