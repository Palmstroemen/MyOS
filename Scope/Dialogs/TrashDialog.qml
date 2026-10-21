import QtQuick 2.15
import QtQuick.Controls 2.15

// Trash of the project shown in the FilesPanel (see "Designdocument Trash.md"): what was
// deleted, from where, when and by whom; restore it or delete it for good. Lists only
// entries the user could have deleted at their original place.
Dialog {
    id: root
    required property var window
    property string projectPath: ""
    property var entries: []
    property string confirmName: ""  // entry whose "delete for good" waits for a second click
    property bool confirmEmpty: false  // "empty the trash" waits for a second click
    property string errorText: ""
    /// Emitted after restoring or deleting (listing and side panel button refresh).
    signal trashChanged()

    title: qsTr("Trash")
    modal: true
    focus: true
    anchors.centerIn: Overlay.overlay
    width: Math.max(520, Math.round(window.width * 0.42))
    height: Math.min(Math.round(window.height * 0.7), 160 + entries.length * 64)
    standardButtons: Dialog.Close
    Overlay.modal: Rectangle { color: "black"; opacity: 0.38 }
    background: Rectangle {
        radius: 16
        color: window.dialogPanelBg
        border.color: window.dialogPanelBorder
        border.width: 2
    }

    function openFor(path) {
        projectPath = path
        confirmName = ""
        confirmEmpty = false
        errorText = ""
        reload()
        open()
    }

    function reload() {
        entries = backend.trashEntries(projectPath) || []
        if (entries.length === 0 && opened) close()
    }

    function formatDate(iso) {
        var d = new Date(iso)
        return isNaN(d.getTime()) ? iso : d.toLocaleString(Qt.locale(), Locale.ShortFormat)
    }

    function act(entry, restore) {
        var result = restore ? backend.trashRestore(projectPath, entry.name)
                             : backend.trashDeleteFinally(projectPath, entry.name)
        confirmName = ""
        if (!result || !result.ok) {
            errorText = result && result.reason === "permission"
                ? qsTr("You may not change this entry.")
                : qsTr("This did not work.")
            return
        }
        errorText = ""
        trashChanged()
        reload()
    }

    function emptyTrash() {
        var result = backend.trashEmpty(projectPath) || {}
        confirmEmpty = false
        errorText = (result.skipped || 0) > 0
            ? qsTr("Entries kept (no permission): %1").arg(result.skipped)
            : ""
        trashChanged()
        reload()
    }

    onOpened: window._setDialogButtonText(root, Dialog.Close, qsTr("Close"))

    contentItem: Column {
        spacing: 8

        Row {
            width: parent.width
            spacing: 8
            Text {
                width: parent.width - emptyButton.width - parent.spacing
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Deleted entries stay here for a while and can be restored.")
                wrapMode: Text.WordWrap
                color: root.window.dialogTextMuted
                font.pixelSize: root.window.baseFont * 0.9
            }
            Button {
                id: emptyButton
                objectName: "trashEmpty"
                // Permanent for all entries: the first click asks, the second empties.
                text: root.confirmEmpty ? qsTr("Really empty?") : qsTr("Empty trash")
                onClicked: {
                    if (root.confirmEmpty) root.emptyTrash()
                    else root.confirmEmpty = true
                }
            }
        }
        Text {
            width: parent.width
            visible: root.errorText.length > 0
            text: root.errorText
            color: "#b00020"
            wrapMode: Text.WordWrap
            font.pixelSize: root.window.baseFont * 0.9
        }

        ListView {
            id: trashList
            width: parent.width
            height: Math.max(60, root.availableHeight - y)
            clip: true
            spacing: 6
            model: root.entries
            delegate: Rectangle {
                width: trashList.width
                height: 58
                radius: 8
                color: Qt.rgba(0.5, 0.5, 0.5, 0.12)
                Column {
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.right: buttons.left
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2
                    Text {
                        width: parent.width
                        text: (modelData.isDir ? "📁 " : "") + modelData.original.split("/").pop()
                        font.bold: true
                        elide: Text.ElideMiddle
                        color: root.window.dialogTextStrong
                        font.pixelSize: root.window.baseFont
                    }
                    Text {
                        width: parent.width
                        text: qsTr("from /%1 · %2 · %3")
                            .arg(modelData.original)
                            .arg(root.formatDate(modelData.deletedAt))
                            .arg(modelData.deletedBy)
                        elide: Text.ElideMiddle
                        color: root.window.dialogTextMuted
                        font.pixelSize: root.window.baseFont * 0.8
                    }
                }
                Row {
                    id: buttons
                    anchors.right: parent.right
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 6
                    Button {
                        objectName: "trashRestore_" + modelData.name
                        text: qsTr("Restore")
                        onClicked: root.act(modelData, true)
                    }
                    Button {
                        objectName: "trashDelete_" + modelData.name
                        // Permanent: the first click asks, the second deletes.
                        text: root.confirmName === modelData.name ? qsTr("Really delete?") : qsTr("Delete for good")
                        onClicked: {
                            if (root.confirmName === modelData.name) root.act(modelData, false)
                            else root.confirmName = modelData.name
                        }
                    }
                }
            }
        }
    }
}
