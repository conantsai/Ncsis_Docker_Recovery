import os
import docker
import time
import tarfile
import shutil
import click

def recovery():
    fb_tarpath = "/home/uscc/Ncsis_Docker_IDS/backup/full_backup/"
    recovery_path = "/home/uscc/Ncsis_Docker_Recovery/recovery/"
    
    # copy the full backup to recovery folder
    shutil.copy(fb_tarpath + "8f324bcd75d6_busybox_1558453398.tar", recovery_path)
    os.mkdir(recovery_path + "8f324bcd75d6_busybox_1558453398")

    # untar full backup file 
    try:
        tar = tarfile.open(fb_tarpath + "8f324bcd75d6_busybox_1558453398.tar")  
        tar.extractall(path=recovery_path + "8f324bcd75d6_busybox_1558453398")  
        os.remove(recovery_path + "8f324bcd75d6_busybox_1558453398.tar")
    except Exception as e:
        print(e)
    finally:
        tar.close()

    # list the incremental backup add file
    with os.popen("find /home/uscc/Ncsis_Docker_IDS/backup/incremental_backup/8f324bcd75d6_busybox_1558453479_IB/Add/ -type f") as f:
        add_flist = f.readlines()

    # list the incremental backup modify file
    with os.popen("find /home/uscc/Ncsis_Docker_IDS/backup/incremental_backup/8f324bcd75d6_busybox_1558453479_IB/Modify/ -type f") as f:
        modify_flist = f.readlines()


    # list the incremental backup add folder
    with os.popen("find /home/uscc/Ncsis_Docker_IDS/backup/incremental_backup/8f324bcd75d6_busybox_1558453479_IB/Add/ -type d") as f:
        add_dlist = f.readlines() 

    # list the full backup folder
    tar_d = os.popen("find /home/uscc/Ncsis_Docker_Recovery/recovery/8f324bcd75d6_busybox_1558453398/ -type d")
    tar_dlist = tar_d.readlines()
    tar_d.close() 

    # if have new folder, create it to recovery folder
    for i in add_dlist:
        e = 0
        for j in tar_dlist:
            if i[92:-1] == j[68:-1]:
                e = 1
                continue
        if e == 0:
            os.mkdir(recovery_path + "8f324bcd75d6_busybox_1558453398" + i[92:-1])

    # if have new file, copy it to recovery folder
    for i in add_flist:
        path = ""
        for j in i.split("/")[:-1]:
            if j == "":
                path = "/"
            else:
                path = path + j + "/" 
        shutil.copy(i[:-1], recovery_path + "8f324bcd75d6_busybox_1558453398" + path[92:])

    # if have modify file, copy it to recovery folder
    for i in modify_flist:
        path = ""
        for j in i.split("/")[:-1]:
            if j == "":
                path = "/"
            else:
                path = path + j + "/" 
        shutil.copy(i[:-1], recovery_path + "8f324bcd75d6_busybox_1558453398" + path[95:])

    # if need to delete file, delete it
    try:
        delete_fp = open("/home/uscc/Ncsis_Docker_IDS/backup/incremental_backup/8f324bcd75d6_busybox_1558453479_IB/Delete/delete_list.txt", "r")
        for i in delete_fp.readlines():
            os.remove(recovery_path + "8f324bcd75d6_busybox_1558453398" + i[:-1])
    except IOError as e:
        print(e)
    finally:
        delete_fp.close() 

    try:
        os.chdir(recovery_path)
        os.system("tar cvf 8f324bcd75d6_busybox_1558453398.tar 8f324bcd75d6_busybox_1558453398")  
        os.system("cat 8f324bcd75d6_busybox_1558453398.tar| docker import - " + "test1234")
    except OSError as e:
        print(e)   


    # cmd_import = "cat " + tarfile + "| docker import - " + "test"
    # print(cmd_import)
    # os.popen(cmd_import)
    # add = os.popen("find /home/uscc/Ncsis_Docker_IDS/backup/incremental_backup/8a2174b8c11f_busybox_1558255250_IB/ -type f")
    # add_list = add.readlines()
    # add.close()

if __name__ == "__main__":
    recovery()