from flask import Flask, request, jsonify, render_template
from pypresence import Presence
from threading import Thread
import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QAction, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

app = Flask(__name__)

client_id = "1261655802502971443"
RPC = Presence(client_id)
RPC.connect()

def get_data_path():
    if os.name == 'nt':
        return os.path.join(os.environ['APPDATA'], 'DiscordSC')
    else:
        return os.path.dirname(os.path.abspath(__file__))

def load_data():
    try:
        with open(os.path.join(get_data_path(), 'data.json'), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"large_image": "", "large_text": "", "details": "", "state": ""}

def save_data(data):
    os.makedirs(get_data_path(), exist_ok=True)
    with open(os.path.join(get_data_path(), 'data.json'), 'w') as file:
        json.dump(data, file)

def get_icon_path():
    try:
        if getattr(sys, 'frozen', False):
            resources_path = sys._MEIPASS
        else:
            resources_path = os.path.dirname(os.path.abspath(__file__))

        return f"{resources_path}/icon.png"
    except Exception:
        return None

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', data=data)

@app.route('/update_presence', methods=['POST'])
def update_presence():
    data = request.json
    large_image = data.get('large_image', '')
    large_text = data.get('large_text', '')
    details = data.get('details', '')
    state = data.get('state', '')

    save_data(data)

    try:
        if not (large_image or large_text or details or state):
            RPC.clear()
        else:
            RPC.update(
                large_image=large_image if large_image != '' else None,
                large_text=large_text if large_text != '' else None,
                details=details if details != '' else None,
                small_image='watermark' if large_image != '' else None,
                small_text='Tsimbalist (GitHub)' if large_image != '' else None,
                state=state if state != '' else None
            )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def run_flask():
    app.run(debug=True, use_reloader=False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DiscordSC')
        self.setFixedSize(500, 650)
        self.setWindowIcon(QIcon(get_icon_path()))
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:5000"))
        self.setCentralWidget(self.browser)
        self.create_tray_icon()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(get_icon_path()))

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)

        github_action = QAction("GitHub", self)
        github_action.triggered.connect(self.open_github)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(github_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        self.tray_icon.show()

    def show_window(self):
        self.showNormal()
        self.show()
        self.activateWindow()

    def tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "DiscordSC",
            "Application minimized to tray",
            QSystemTrayIcon.Information,
            2000
        )

    def open_github(self):
        import webbrowser
        webbrowser.open_new_tab('https://github.com/Tsimbalist')

    def quit_application(self):
        QApplication.quit()
        RPC.close()
        os._exit(0)

def run_app():
    server = Thread(target=run_flask)
    server.start()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_app()
