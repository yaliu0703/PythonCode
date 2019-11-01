# -*- coding: UTF-8 -*-
import socket, os, struct,sys

def main():
    HOST, PORT = socket.gethostname(), 5000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST,PORT))
    except:
        print 'Unable to connect'
        sys.exit()
    print 'Connected to remote host. '

    filepath = raw_input("Please Enter D:\XXXXX\\filename:\r\n")
    print filepath
    print len(filepath)
    if os.path.isfile(filepath):
        fileinfo_size = struct.calcsize('128sl')  # 定义打包规则
        # 定义文件头信息，包含文件名和文件大小
        fhead = struct.pack('128sl', os.path.basename(filepath), os.stat(filepath).st_size)
        s.send("down_file_head." + fhead)  # 加消息头
        print 'client filepath: ', filepath
        fo = open(filepath, 'rb')
        while True:
            filedata = fo.read(1024)
            if not filedata:
                break
            s.send("down_file_data." + filedata)  # 加消息头
        fo.close()
        print 'send over...'
if __name__ == "__main__":
    main()