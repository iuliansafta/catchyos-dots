import QtQuick 2.15
import SddmComponents 2.0

Rectangle {
    id: root

    property string currentUser: userModel.lastUser || ""
    property bool loginFailed: false
    property int logoFontSize: Math.max(72, Math.round(root.height * 0.105))
    property int entryWidth: Math.max(400, Math.round(root.width * 0.24))
    property int entryHeight: Math.max(64, Math.round(root.height * 0.065))
    property int sessionIndex: {
        var preferred = (config.PreferredSession || "niri").toString().toLowerCase();
        var fallback = sessionModel.lastIndex;
        for (var i = 0; i < sessionModel.rowCount(); i++) {
            var name = (sessionModel.data(sessionModel.index(i, 0), Qt.DisplayRole) || "").toString().toLowerCase();
            if (preferred !== "" && name.indexOf(preferred) !== -1)
                return i;

            if (name.indexOf("niri") !== -1)
                return i;

            if (name.indexOf("uwsm") !== -1)
                fallback = i;

        }
        return fallback;
    }

    function fallbackUser() {
        if (root.currentUser !== "")
            return root.currentUser;

        if (userModel.lastIndex >= 0)
            return (userModel.data(userModel.index(userModel.lastIndex, 0), Qt.DisplayRole) || "").toString();

        return "";
    }

    function submitLogin() {
        var user = fallbackUser();
        if (config.AllowUppercaseLettersInUsernames == "false")
            user = user.toLowerCase();

        sddm.login(user, password.text, root.sessionIndex);
    }

    width: config.ScreenWidth || Screen.width
    height: config.ScreenHeight || Screen.height
    color: config.BackgroundColor || "#1a1b26"
    Component.onCompleted: password.forceActiveFocus()

    Connections {
        function onLoginFailed() {
            root.loginFailed = true;
            password.text = "";
            password.forceActiveFocus();
        }

        function onLoginSucceeded() {
            root.loginFailed = false;
        }

        target: sddm
    }

    Image {
        id: backgroundImage

        anchors.fill: parent
        source: config.Background ? Qt.resolvedUrl(config.Background) : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: true
        visible: source != ""
    }

    Rectangle {
        anchors.fill: parent
        color: config.DimBackgroundColor || root.color
        opacity: backgroundImage.visible ? (Number(config.DimBackground) || 0.35) : 0
    }

    Column {
        anchors.centerIn: parent
        spacing: 48

        Text {
            id: logoText

            anchors.horizontalCenter: parent.horizontalCenter
            text: config.InputHeaderText || config.HeaderText || "•YES•"
            color: root.loginFailed ? config.WarningColor : config.HeaderTextColor
            font.family: config.Font || "JetBrainsMono Nerd Font"
            font.pixelSize: root.logoFontSize
            font.bold: true
            renderType: Text.QtRendering
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 20

            Text {
                id: lockIcon

                width: 52
                height: entryBox.height
                text: root.loginFailed ? "!" : ""
                color: root.loginFailed ? config.WarningColor : config.PasswordIconColor
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: root.loginFailed ? 48 : 46
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                renderType: Text.QtRendering
            }

            Item {
                id: entryBox

                width: root.entryWidth
                height: root.entryHeight

                Rectangle {
                    anchors.fill: parent
                    color: config.PasswordFieldBackgroundColor
                    opacity: root.loginFailed ? 0.45 : 0.32
                    radius: 0
                    border.width: 2
                    border.color: root.loginFailed ? config.WarningColor : (password.activeFocus ? config.HighlightBorderColor : "transparent")
                }

                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 28
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 7

                    Repeater {
                        model: Math.min(password.text.length, 21)

                        Rectangle {
                            width: 10
                            height: 10
                            radius: 5
                            color: root.loginFailed ? config.WarningColor : config.PasswordFieldTextColor
                        }

                    }

                }

                TextInput {
                    id: password

                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 28
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 34
                    font.letterSpacing: 7
                    passwordCharacter: "•"
                    color: "transparent"
                    selectionColor: "transparent"
                    selectedTextColor: "transparent"
                    focus: true
                    onTextChanged: root.loginFailed = false
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                            root.submitLogin();
                            event.accepted = true;
                        }
                    }

                    cursorDelegate: Item {
                    }

                }

            }

        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: config.TranslateLoginFailedWarning || "login failed"
            color: config.WarningColor
            font.family: config.Font || "JetBrainsMono Nerd Font"
            font.pixelSize: 20
            font.italic: true
            opacity: root.loginFailed ? 1 : 0
            renderType: Text.QtRendering
        }

    }

    MouseArea {
        anchors.fill: parent
        onClicked: password.forceActiveFocus()
    }

}
