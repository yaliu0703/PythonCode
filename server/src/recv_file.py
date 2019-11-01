# -*- coding: UTF-8 -*-
import socket, time, SocketServer, struct, os, thread

#HOST, PORT = socket.gethostname(), 5000
HOST, PORT = '10.8.191.67', 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.bind((HOST, PORT))
#s.listen(1)


def recv_xml():
    #sock, address = s.accept()
    try:
        sock.settimeout(600)
        fileinfo_size = struct.calcsize('128sl')
        buf = sock.recv(fileinfo_size)         #15 是消息头长度
        filename, filesize = struct.unpack('128sl', buf)   #filesize 文件大小
        filename_f = filename.strip('\00')   #去除打包的空格符
        filenewname = os.path.join('E:\\', (filename_f))  #存在 哪个目录
        print 'file new name is %s, filesize is %s' % (filenewname, filesize)
        recvd_size = 0  # 定义接收了的文件大小
        file = open(filenewname, 'wb')
        print 'stat receiving...'
        while not recvd_size == filesize:                    #filesize 文件实际大小
            if filesize - recvd_size > 1024:
                rdata = sock.recv(1024 )
                recvd_size = recvd_size +len(rdata)     #15是消息头长度
            else:
                rdata = sock.recv(filesize - recvd_size)
                recvd_size = filesize
            file.write(rdata)
        file.close()
        print 'receive done'

    except socket.timeout:
        print "recv xml done"
