import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Save filter")
    modal: true
    focus: true
    standardButtons: Dialog.Cancel
    anchors.centerIn: Overlay.overlay
    width: Math.max(560, Math.round(window.width * 0.44))
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }
    onOpened: window._setDialogButtonText(root, Dialog.Cancel, qsTr("Cancel"))
    contentItem: Column {
        spacing: 10
        Text {
            text: qsTr("You changed the filter. Where should this change apply?")
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        Repeater {
            model: window.filterSaveTargets || []
            delegate: Button {
                width: Math.max(420, root.width - 60)
                text: String(modelData.label || modelData.id || "")
                onClicked: {
                    var targetId = String(modelData.id || "")
                    if (targetId === "new_named") {
                        window.filterNameDialog.open()
                        return
                    }
                    window.applyFilterSave(targetId)
                    root.close()
                }
            }
        }
    }
}
