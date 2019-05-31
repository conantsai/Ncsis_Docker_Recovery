import sys
import os 
from PyQt5.QtWidgets import QDialog, QApplication
from Ui_recovery import Ui_Dialog   
import docker

class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.onBindingUI()
        self.container_info()
        self.show()

    def container_info(self):
        cmd_conid = os.popen("sudo docker ps -a")
        result_conid = cmd_conid.readlines()
        strcon = ""
        for i in result_conid:
            self.ui.textBrowser_conifoC.append(str(i))

    def onBindingUI(self):
        self.ui.pushButton_search.clicked.connect(self.on_pushButton_search_click)
        self.ui.pushButton_backup.clicked.connect(self.op_pushButton_backup_click)

    def on_pushButton_search_click(self):
        return

    def op_pushButton_backup_click(self):
        return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())