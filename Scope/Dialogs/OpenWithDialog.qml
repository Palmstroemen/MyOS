import QtQuick 2.15
import QtQuick.Controls 2.15
import "../js/PathUtils.js" as PathUtils

Dialog {
    id: root
    required property var window
    title: qsTr("Oeffnen mit ...")
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
        window._setDialogButtonText(root, Dialog.Ok, qsTr("Oeffnen"))
        window._setDialogButtonText(root, Dialog.Cancel, qsTr("Abbrechen"))
        openWithCommandInput.forceActiveFocus()
        openWithCommandInput.selectAll()
    }
    onAccepted: {
        var ok = window.performOpenWith(window.pendingOpenWithPath, openWithCommandInput.text)
        if (!ok) {
            window.moveReportMessage = qsTr("Konnte Datei nicht mit dem gewaehlten Programm oeffnen.")
            window.moveReportDialog.open()
        }
        window.pendingOpenWithPath = ""
    }
    onRejected: window.pendingOpenWithPath = ""
    contentItem: Column {
        spacing: 8
        Text {
            text: qsTr("Programmkommando fuer \"%1\":").arg(PathUtils.basename(window.pendingOpenWithPath))
            wrapMode: Text.WordWrap
            color: window.dialogTextStrong
            font.pixelSize: window.baseFont
        }
        TextField {
            id: openWithCommandInput
            text: window.pendingOpenWithCommand
            placeholderText: qsTr("z.B. code, kate, libreoffice")
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
            onTextChanged: window.pendingOpenWithCommand = text
            Keys.onReturnPressed: root.accept()
            Keys.onEnterPressed: root.accept()
            Keys.onEscapePressed: root.reject()
        }
        Text {
            text: qsTr("Schnellwahl:")
            color: window.dialogTextMuted
            font.pixelSize: Math.max(window.baseFont - 1, 11)
            visible: window.openWithQuickCommands && window.openWithQuickCommands.length > 0
        }
        Flow {
            width: parent.width
            spacing: 6
            visible: window.openWithQuickCommands && window.openWithQuickCommands.length > 0
            Repeater {
                model: window.openWithQuickCommands
                delegate: Rectangle {
                    required property var modelData
                    radius: 8
                    height: Math.max(28, Math.round(window.baseFont * 1.8))
                    width: quickText.implicitWidth + 20
                    color: window.dialogInputBg
                    border.color: window.dialogInputBorder
                    border.width: 1
                    Text {
                        id: quickText
                        anchors.centerIn: parent
                        text: String(modelData || "")
                        color: window.dialogInputText
                        font.pixelSize: Math.max(window.baseFont - 1, 11)
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            var value = String(modelData || "").trim()
                            if (!value) return
                            openWithCommandInput.text = value
                            openWithCommandInput.forceActiveFocus()
                            openWithCommandInput.selectAll()
                        }
                    }
                }
            }
        }
    }
}
