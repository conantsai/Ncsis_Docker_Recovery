
 
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
            # get the full backup data information
            for file in files:
                if file.startswith(search_id):
                    if files.index(file) == 0:
                        self.ui.textBrowser_backupinfoC.append("Full Backup Data :" )
                    self.ui.textBrowser_backupinfoC.append("    " + file[:-4])
            # get the incremental backup data information
            for dir in dirs:
                if dir.startswith(search_id) and root != "/usr/local/Ncsis_Docker_Backup/backup/":
                    if dirs.index(dir) == 0:
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

        
        # import the full backup status to image
        try:
            os.system("cat /usr/local/Ncsis_Docker_Recovery/recovery/*.tar " + "| docker import - " + recovery_id)
        except OSError as e:
            print(e) 

        # get the incremental backup list
        latest_backup = recovery_id[-10:]
        ib_sort = []
        ib_dirlist = os.listdir(backup_path + recovery_id[:-11] + "/incremental_backup/")
        for i in ib_dirlist:
            ib_sort.append(i[-10:])
        ib_sort.sort()

        try:
            dockerfile = open("/usr/local/Ncsis_Docker_Recovery/dockerfile", "a+")
            dockerfile.seek(0)
            dockerfile.truncate()
            dockerfile.writelines("FROM " + recovery_id + ":latest" + "\n")
        except: 
            pass
        finally:
            dockerfile.close()

        for i in ib_sort:
            if int(i) ==  int(latest_backup):
                recovery(i, backup_path + recovery_id[:-11] + "/incremental_backup/" + recovery_id[:-11], recovery_dirpath, recovery_id)
                break
            else:
                recovery(i, backup_path + recovery_id[:-11] + "/incremental_backup/" + recovery_id[:-11], recovery_dirpath, recovery_id)

        try:
            os.system("docker build -t ttttt .")
        except:
            pass 

        shutil.rmtree("/usr/local/Ncsis_Docker_Recovery/recovery/")
        os.mkdir("/usr/local/Ncsis_Docker_Recovery/recovery/")

def word_position(string, subStr, findCnt):
    listStr = string.split(subStr,findCnt)
    if len(listStr) <= findCnt:
        return "not find"
    return len(string)-len(listStr[-1])-len(subStr)

def recovery(time_stamp, ib_path, dir_path, image_id):
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
    
    try:
        dockerfile = open("/usr/local/Ncsis_Docker_Recovery/dockerfile", "a+")

        # if have new folder, create it to recovery folder
        for i in add_dlist:
            key = 0
            i_position = word_position(i, "/", 9)
            for j in tar_dlist:
                j_position = word_position(j, "/", 6)
                if i[i_position:-1] == j[j_position:-1]:
                    key = 1
                    continue
            if key == 0:
                os.mkdir(dir_path + i[i_position:-1])

        # if have new file, copy it to recovery folder and write it to the dockerfile
        for i in range(len(add_flist)):
            # get the current file copy destination path
            i_position = word_position(add_flist[i], "/", 9)
            slash_cnt = add_flist[i].count("/")
            i_secposition = word_position(add_flist[i], "/", slash_cnt)

            # get the previous file copy destination path
            previousi_position = word_position(add_flist[i-1], "/", 9)
            slash_seccnt = add_flist[i-1].count("/")
            previousi_secposition = word_position(add_flist[i-1], "/", slash_seccnt)

            shutil.copy(add_flist[i][:-1], dir_path + add_flist[i][i_position:-1])

            if len(add_flist) == 1:
                dockerfile.writelines("COPY ." + dir_path[32:-1] + add_flist[i][i_position:-1] + " " + add_flist[i][i_position:i_secposition] + "/ \n")
            elif len(add_flist) != 1 and i == 0:
                dockerfile.writelines("COPY ." + dir_path[32:-1] + add_flist[i][i_position:-1] + " " )
            elif len(add_flist) != 1 and i == len(add_flist)-1:
                if add_flist[i][i_position:i_secposition] == add_flist[i-1][previousi_position:previousi_secposition]:
                    dockerfile.writelines(dir_path[32:-1] + add_flist[i][i_position:-1] + " " + add_flist[i][i_position:i_secposition] + "/ \n")
                elif add_flist[i][i_position:i_secposition] != add_flist[i-1][previousi_position:previousi_secposition]: 
                    dockerfile.writelines(add_flist[i-1][previousi_position:previousi_secposition] + "/ \n" )
                    dockerfile.writelines("COPY ." + dir_path[32:-1] + add_flist[i][i_position:-1] + " " + add_flist[i][i_position:i_secposition] + "/ \n")
            else:
                if add_flist[i][i_position:i_secposition] == add_flist[i-1][previousi_position:previousi_secposition]:
                    dockerfile.writelines(dir_path[32:-1] + add_flist[i][i_position:-1] + " ")
                elif add_flist[i][i_position:i_secposition] != add_flist[i-1][previousi_position:previousi_secposition]: 
                    dockerfile.writelines(add_flist[i-1][previousi_position:previousi_secposition] + "/ \n" )
                    dockerfile.writelines("COPY ." + dir_path[32:-1] + add_flist[i][i_position:-1] + " ")

        # if have modify file, copy it to recovery folder and write it to the dockerfile
        for i in range(len(modify_flist)):
            # get the current file copy destination path
            i_position = word_position(modify_flist[i], "/", 9)
            slash_cnt = modify_flist[i].count("/")
            i_secposition = word_position(modify_flist[i], "/", slash_cnt)

            # get the previous file copy destination path
            previousi_position = word_position(modify_flist[i-1], "/", 9)
            slash_seccnt = modify_flist[i-1].count("/")
            previousi_secposition = word_position(modify_flist[i-1], "/", slash_seccnt)

            shutil.copy(modify_flist[i][:-1], dir_path + modify_flist[i][i_position:-1])

            if len(modify_flist) == 1:
                dockerfile.writelines("COPY ." + dir_path[32:-1] + modify_flist[i][i_position:-1] + " " + modify_flist[i][i_position:i_secposition] + "/ \n")
            elif len(modify_flist) != 1 and i == 0:
                dockerfile.writelines("COPY ." + dir_path[32:-1] + modify_flist[i][i_position:-1] + " " )
            elif len(modify_flist) != 1 and i == len(modify_flist)-1:
                if modify_flist[i][i_position:i_secposition] == modify_flist[i-1][previousi_position:previousi_secposition]:
                    dockerfile.writelines(dir_path[32:-1] + modify_flist[i][i_position:-1] + " " + modify_flist[i][i_position:i_secposition] + "/ \n")
                elif modify_flist[i][i_position:i_secposition] != modify_flist[i-1][previousi_position:previousi_secposition]: 
                    dockerfile.writelines(modify_flist[i-1][previousi_position:previousi_secposition] + "/ \n" )
                    dockerfile.writelines("COPY ." + dir_path[32:-1] + modify_flist[i][i_position:-1] + " " + modify_flist[i][i_position:i_secposition] + "/ \n")
            else:
                if modify_flist[i][i_position:i_secposition] == modify_flist[i-1][previousi_position:previousi_secposition]:
                    dockerfile.writelines(dir_path[32:-1] + modify_flist[i][i_position:-1] + " ")
                elif modify_flist[i][i_position:i_secposition] != modify_flist[i-1][previousi_position:previousi_secposition]: 
                    dockerfile.writelines(modify_flist[i-1][previousi_position:previousi_secposition] + "/ \n" )
                    dockerfile.writelines("COPY ." + dir_path[32:-1] + modify_flist[i][i_position:-1] + " ")

        # if need to delete file, delete it
        try:
            delete_fp = open(ib + "/Delete/delete_list.txt", "r")
            if os.path.getsize(ib + "/Delete/delete_list.txt") > 0 :
                dockerfile.writelines("RUN rm " )
            for i in delete_fp.readlines():
                dockerfile.writelines("\\" + i[1:-1] + " \\ \n" + "       ")
        except IOError as e:
            print(e)
        finally:
            delete_fp.close() 
    except: 
        pass
    finally:
        dockerfile.close() 
 
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myshow = AppWindow()
    myshow.show()
    sys.exit(app.exec_())


