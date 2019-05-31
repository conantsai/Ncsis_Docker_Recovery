
 
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from Ui_recovery import Ui_Dialog  
import sys
from PyQt5.QtCore import *
import time
import os
import shutil
import tarfile
 
class Runthread_coninfo(QtCore.QThread):
    _signal = pyqtSignal(str)
 
    def __init__(self, parent=None):
        super(Runthread_coninfo, self).__init__()
 
    def __del__(self):
        self.wait()
 
    def run(self):
        while True:
            all_conid = ""
            cmd_conid = os.popen("sudo docker ps -a")
            result_conid = cmd_conid.readlines()
            for i in result_conid:
                all_conid = all_conid + "\n" + i
            self.callback(all_conid)
            time.sleep(1)
        
    def callback(self, msg):
        self._signal.emit(msg)
        
class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.start_getconinfo()
        self.onBindingUI()
 
    def start_getconinfo(self): 
        self.thread = Runthread_coninfo()
        self.thread._signal.connect(self.refresh_coninfo)
        self.thread.start()
 
    def refresh_coninfo(self, msg):
        self.ui.textBrowser_coninfoC.clear()
        self.ui.textBrowser_coninfoC.append(msg)
    
    def onBindingUI(self):
        self.ui.pushButton_search.clicked.connect(self.on_pushButton_search_click)
        self.ui.pushButton_backup.clicked.connect(self.op_pushButton_recovery_click)

    def on_pushButton_search_click(self):
        self.ui.textBrowser_backupinfoC.clear()
        search_id = self.ui.lineEdit_conidC.text()

        for root, dirs, files in os.walk("/usr/local/Ncsis_Docker_Backup/backup/"):
            for file in files:
                if file.startswith(search_id):
                    if files.index(file) == 0:
                        self.ui.textBrowser_backupinfoC.append("Full Backup Data :" )
                    self.ui.textBrowser_backupinfoC.append("    " + file[:-4])

            for dir in dirs:
                if dir.startswith(search_id) and root != "/usr/local/Ncsis_Docker_Backup/backup/":
                    if dirs.index(dir) == 0  :
                        self.ui.textBrowser_backupinfoC.append("Incremental Backup Data :" )  
                    self.ui.textBrowser_backupinfoC.append("    " + dir)
           
    def op_pushButton_recovery_click(self):
        recovery_id = self.ui.lineEdit_recoveryC.text()

        backup_path = "/usr/local/Ncsis_Docker_Backup/backup/"
        recovery_path = "/usr/local/Ncsis_Docker_Recovery/recovery/"
        recovery_dirpath = recovery_path + recovery_id + "/"

        try:
            os.mkdir(recovery_dirpath)
        except FileExistsError as e:
            print(e)

        # copy the full backup to recovery folder
        with os.popen("find " + backup_path + recovery_id[:-11] + "/full_backup/ -type f") as f:
            shutil.copy(f.readline()[:-1], recovery_path)
        
        # untar full backup file 
        with os.popen("find " + recovery_path  + " -type f") as f:
            try:
                tar = tarfile.open(f.readline()[:-1])  
                tar.extractall(path=recovery_dirpath)  
                os.remove(f.readline()[:-1])
            except Exception as e:
                pass
            # finally:
            #     tar.close()

        # get the incremental backup list
        latest_backup = recovery_id[-10:]
        ib_sort = []
        ib_dirlist = os.listdir(backup_path + recovery_id[:-11] + "/incremental_backup/")
        for i in ib_dirlist:
            ib_sort.append(i[-10:])
        ib_sort.sort()

        for i in ib_sort:
            if int(i) ==  int(latest_backup):
                recovery(i, backup_path + recovery_id[:-11] + "/incremental_backup/" + recovery_id[:-11], recovery_dirpath)
                break
            else:
                recovery(i, backup_path + recovery_id[:-11] + "/incremental_backup/" + recovery_id[:-11], recovery_dirpath)

        try:
            os.chdir(recovery_path)
            os.system("tar cvf " + latest_backup + ".tar " + recovery_dirpath)  
            os.system("cat " + latest_backup + ".tar " + "| docker import - " + recovery_id)
        except OSError as e:
            print(e)  

def recovery(time_stamp, ib_path, dir_path):
    ib = ib_path + "_" + time_stamp

    # list the incremental backup add file
    with os.popen("find " + ib + "/Add/ -type f") as f:
        add_flist = f.readlines()

    # list the incremental backup modify file
    with os.popen("find " + ib + "/Modify/ -type f") as f:
        modify_flist = f.readlines()

    # list the incremental backup add folder
    with os.popen("find " + ib + "/Add/ -type d") as f:
        add_dlist = f.readlines() 
        
    # list the full backup folder
    with os.popen("find " + dir_path + " -type d") as f:
        tar_dlist = f.readlines()

    # if have new folder, create it to recovery folder
    for i in add_dlist:
        e = 0
        for j in tar_dlist:
            if i[113:-1] == j[73:-1]:
                e = 1
                continue
        if e == 0:
            os.mkdir(dir_path + i[114:-1])
    
    # if have new file, copy it to recovery folder
    for i in add_flist:
        path = ""
        for j in i.split("/")[:-1]:
            if j == "":
                path = "/"
            else:
                path = path + j + "/" 
        shutil.copy(i[:-1], dir_path + i[114:-1])
    
    # if have modify file, copy it to recovery folder
    for i in modify_flist:
        path = ""
        for j in i.split("/")[:-1]:
            if j == "":
                path = "/"
            else:
                path = path + j + "/" 
        shutil.copy(i[:-1], dir_path + i[117:-1])

    # if need to delete file, delete it
    try:
        delete_fp = open(ib + "/Delete/delete_list.txt", "r")
        for i in delete_fp.readlines():
            os.remove(dir_path + i[1:-1])
    except IOError as e:
        print(e)
    finally:
        delete_fp.close() 

 

    
 
 
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myshow = AppWindow()
    myshow.show()
    sys.exit(app.exec_())


