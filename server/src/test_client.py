# -*- coding: UTF-8 -*-
'''
Created on 2016年6月30日

@author: lfy
'''
from socket import *
from string import *
from sys import *
from threading import *
from select import *
from time import *
import socket, string, select, sys, threading, time, os, struct

#main function
if __name__ == "__main__":

    #host, port = socket.gethostname(), 5000
    host, port = '10.8.177.221', 5000
     
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
     
    # connect to remote host
    try :
        sock.connect((host, port))
    except :
        print 'Unable to connect'
        sys.exit()
     
    print 'Connected to remote host. '
     
    while 1:
        #user entered a message
        #msg = sys.stdin.readline()
        msg = raw_input()
        print"i say:"+msg
        sock.send(msg)
        print sock.recv(2048)
        if msg[0:17] == "group_msg:up_file":
            filepath = "D:\girl.bmp"
            if os.path.isfile(filepath):
                fileinfo_size = struct.calcsize('128sl')  # 定义打包规则
                # 定义文件头信息，包含文件名和文件大小
                fhead = struct.pack('128sl', os.path.basename(filepath), os.stat(filepath).st_size)
                sock.send("group_msg:up_file_head." + fhead)  # 加消息头
                print 'client filepath: ', filepath
                fo = open(filepath, 'rb')
                while True:
                    filedata = fo.read(1024)
                    if not filedata:
                        break
                    sock.send("group_msg:up_file_data." + filedata)  # 加消息头
                fo.close()
                # sock.close()
                print 'send over...'
        elif msg[0:19] =="group_msg:down_file":#格式group_msg:down_file20161
            sock.settimeout(600)
            fileinfo_size = struct.calcsize('128sl')
            buf = sock.recv(fileinfo_size + 25)  # 25 是消息头长度
            buf = buf[25:]
            filename, filesize = struct.unpack('128sl', buf)  # filesize 文件大小
            filename_f = filename.strip('\00')  # 去除打包的空格符
            filenewname = os.path.join('C:\\', (filename_f))  # 存在 E 根目录
            print 'file new name is %s, filesize is %s' % (filenewname, filesize)
            recvd_size = 0  # 定义接收了的文件大小
            file = open(filenewname, 'wb')
            print 'stat receiving...'
            while not recvd_size == filesize:  # filesize 文件实际大小
                if filesize - recvd_size > 1024:
                    rdata = sock.recv(1024 + 25)
                    recvd_size = recvd_size + len(rdata) - 25  # 15是消息头长度
                else:
                    rdata = sock.recv(filesize - recvd_size + 25)
                    recvd_size = filesize
                rdata = rdata[25:]
                file.write(rdata)
            file.close()
            print 'receive done'
