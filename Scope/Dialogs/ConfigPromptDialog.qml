import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: root
    required property var window
    title: qsTr("Save desktop changes")
    modal: true
    focus: true
    standardButtons: Dialog.NoButton
    anchors.centerIn: Overlay.overlay
    width: Math.max(520, Math.round(window.width * 0.36))
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
    onClosed: {
        window.pendingConfigPrompt = ({ pending: false, options: [] })
        window.pendingConfigPromptContext = ""
    }
    contentItem: Column {
        spacing: 12
        padding: 14
        Text {
            text: qsTr("Desktop changes for context: ") + window.pendingConfigPromptContext
            color: window.dialogTextStrong
            wrapMode: Text.Wrap
            font.pixelSize: window.baseFont
        }
        Text {
            text: qsTr("Where should the configuration be saved?")
            color: window.dialogTextMuted
            wrapMode: Text.Wrap
            font.pixelSize: window.baseFont
        }
        Repeater {
            model: (window.pendingConfigPrompt && window.pendingConfigPrompt.options) ? window.pendingConfigPrompt.options : []
            delegate: Button {
                width: 460
                text: String(modelData.label || modelData.id || "")
                onClicked: {
                    if (window.hasBackend() && typeof window.backend.resolveConfigPrompt === "function") {
                        window.backend.resolveConfigPrompt(String(modelData.id || "discard"))
                    }
                    root.close()
                }
            }
        }
    }
}
