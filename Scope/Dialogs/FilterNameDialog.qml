import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("New filter")
    modal: true
    focus: true
    standardButtons: Dialog.Ok | Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(460, Math.round(window.width * 0.34))
    Overlay.modal: Rectangle {
        color: "black"
        opacity: 0.38
    }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: {
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Apply"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
        filterNameInput.forceActiveFocus()
        filterNameInput.selectAll()
    }
    onAccepted: {
        window.pendingFilterNewName = String(filterNameInput.text || "").trim()
        window.applyFilterSave("new_named")
        root.close()
        window.filterSaveDialog.close()
    }
    contentItem: Column {
        spacing: 8
        Text {
            text: qsTr("Name for the new filter")
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        TextField {
            id: filterNameInput
            text: window.pendingFilterNewName
            placeholderText: qsTr("e.g. incoming invoices")
            selectByMouse: true
            color: window.dialogInputText
            placeholderTextColor: window.dialogInputPlaceholder
            topPadding: 10
            bottomPadding: 10
            leftPadding: 12
            rightPadding: 12
            background: Rectangle {
                radius: 10
                color: window.dialogInputBg
                border.color: window.dialogInputBorder
                border.width: 1
            }
        }
    }
}
