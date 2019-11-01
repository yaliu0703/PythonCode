# -*- coding: UTF-8 -*-
import os
global unknow_pad
unknow_pad = {}
try:
    fname="girl.bmp"
    unknow_pad[fname] = "pad"
    i = fname.index(".")
    name = fname[0:i]
    name = os.path.join('E:\\', (name))
    name = name + ".txt"
    print name
    file = open(name, 'rb')
    filesize = 0
    print "1111"
    while True:
        filedata = file.read(5)
        if not filedata:
            break
        else:
            filesize = filesize + len(filedata)
    print filesize
    file.close()
    file = open(name, 'rb')
    while True:
        if filesize > 5:
            filedata = file.read(5)
            filesize = filesize - 5
            print"down_file1:unpad:" + filedata
        elif filesize < 5 and filesize > 0:
            filedata = file.read(filesize)
            if unknow_pad[fname] == "pad":
                print"down_file1:pad:" + filedata
            elif unknow_pad[fname] == "unpad":
                print"down_file1:unpad:" + filedata
            break
    file.close()
    print("down_file1:EOF")
    print "send "
except:
    print "wrong"