import sys
reload(sys)
sys.setdefaultencoding('gbk')
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
import socket, string, select, sys, threading, time,MySQLdb,rsa,os,struct
from new_gen_xml import genxml
# default globals
global HOST, PORT,RECV_BUFFER,connection_lists,loged_list,user_names,u_states,u_info,friends_list,ip_list,ID,group_id,group_gono,group_msg,file_buffer
global u_skey,u_svector,unknow_pad
#HOST, PORT = gethostbyname(gethostname()), 5000
HOST, PORT = '10.204.32.227', 5000
ID = 20165
RECV_BUFFER = 4096
ip_list = {}              #保存每个socket的IP
connection_lists = [""]   #为socket连接列表 fileno()型
loged_list = [""]         #保存登录成功在线的sock列表，防止重复登录
id_list = {}              #每个用户的账号,ID唯一标识,主键
user_names = {}           #每个用户的昵称
u_info = {}               #每个用户的信息（昵称：ip：端口）
u_states = {}             #每个用户的在线状态
friends_list = {}         #每个用户的好友列表
group_id = {}             #群所有成员id
group_gono = {}           #是否屏蔽群消息
group_msg = {}            #暂存屏蔽了的群消息
file_buffer = {}          #缓存群文件信息,用上传者的ID来区分文件文件名
u_skey = {}               #群聊中每个群成员公钥加密的会话密钥
u_svector = {}            #群聊中每个群成员公钥加密的向量
unknow_pad = {}           #文件最后一条是否填充

def main():
   initialization()
   class Listen_for_connections(Thread):
       def __init__(self):
           Thread.__init__(self)

       # start background job
       def run(self):
           try:
               server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
               server.bind((HOST, PORT))
               server.listen(1)
               print "Chat server started on port " + str(PORT)
           except socket.error, detail:
               print detail
           while 1:
               connection_lists = [server.fileno()]
               """当服务器已经处于listening状态下此方法返回一个描述socket的整数描述符号。
                                  这个方法通常传递给select.select(),以便允许在同一个进程中多个server对socket的监听。"""
               # ADD new connections
               for sock in user_names.keys():
                   connection_lists.append(sock.fileno())  # 向socket列表添加新连接
               print connection_lists
               try:
                   read, write, error = select.select(connection_lists, [], [],3)  # select for reading from all sockets
               except select.error, detail:
                   print detail
                   break
               print read
               for n in read:
                   if n == server.fileno():  # 该消息是新的连接请求
                       print"new connection"
                       sock, addr = server.accept()
                       ip_list[sock] = addr
                       id_list[sock] = None
                       user_names[sock] = None
                   else:  # 该信息是来自已连接的客户端
                       for sock in user_names.keys():
                           if sock.fileno() == n: break
                       name = user_names[sock]  # 用户名nickname
                       try:
                           message = sock.recv(RECV_BUFFER)
                           print message
                           if message[0:8] == "register":
                               register(sock,message)
                           elif message[0:3] == "log":
                               login(sock, ip_list[sock], message)
                           elif message[0:4] == "call": #离线消息格式 call:id:0:说的话，在线格式call:id:任意
                               call_to(sock, message)
                           elif message[0:9] == "change_pw":
                               change_pw(sock,message)
                           elif message[0:11] == "change_name":
                               change_name(sock, ip_list[sock], message)
                           elif message[0:3] == "add":
                               add_friend(sock, message)
                           elif message[0:3] == "del":
                               del_friend(sock, message)
                           elif message[0:10]=="group_chat":  #消息格式 group_chat:id:id:id:
                               group_chat(sock,message)
                           elif message[0:9]=="group_msg":    #消息格式 group_msg:封装好的消息  PS:封装好的消息指客户端要显示的消息格式 id:昵称：时间：xxx
                               group_messag(sock,message)
                           elif message[0:4] == "quit":
                               u_states[id_list[sock]] = "off"
                               broadto_friends_info(sock, ip_list[sock])  # 通知该用户的好友，我下线了
                               del user_names[sock]
                               del id_list[sock]
                               loged_list.remove(sock)
                               sock.close();

                           else:
                               sock.send("go no")
                       except socket.error, detail:
                           print detail
                           break
                       #if (sock in loged_list and friends_list[sock] != None):
                       #   sock.send(friends_list[sock])
                       print message + " from: " + str(name)

   Listen_for_connections().start()

def register(s,msg):
    if msg[8]=="0":
        s.send("250nick_pw.please input nick name and pw")
    elif msg[8]=="1":
        nick_pw = msg[10:]
        i = nick_pw.index(":")
        nick = nick_pw[0:i]
        pw = nick_pw[i + 1:]
        (pubkey, privkey) = rsa.newkeys(1024)
        pubn = str(pubkey.n)
        pube = str(pubkey.e)
        publikey = pubn + "," + pube #公钥字符串
        privn = str(privkey.n)
        prive = str(privkey.e)
        privd = str(privkey.d)
        privp = str(privkey.p)
        privq = str(privkey.q)
        privatekey = privn +","+prive+","+privd+","+privp+","+privq   #私钥字符串
        global ID
        genxml(str(ID), privatekey, publikey)

        try:
            # s.send(证书）
            conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
            cur = conn.cursor()  # 使用cursor()方法获取操作游标
            cur.execute('insert into user_list values("%s", "%s","%s","","")' % (str(ID), str(hash(pw)), publikey))
            conn.commit()
            cur.execute('insert into id_nick values("%s", "%s")' % (str(ID), nick))
            conn.commit()
            cur.execute('insert into group_msg values("%s", "","","")' % (str(ID)))
            conn.commit()
            s.send("250register:" + str(ID))
            ID = ID + 1
        except:
            # Rollback in case there is any error
            conn.rollback()
            s.send("505register.something wrong with the SQL,Please try again!")
        conn.close()

def login(s,ip_port,msg):
    msg = msg[4:]
    j = msg.index(":")
    t_id = msg[0:j]  # 得到id
    pw = msg[j + 1:]  # 得到password

    onlined = 0
    for t_sock in user_names.keys():
        if t_sock in loged_list and id_list[t_sock]==t_id:
           onlined=1
    if onlined==1:
        s.send("505log.you have loged already!")
    else:
        n_lists = []  # 保存已存在的ID
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
        cur = conn.cursor()  # 使用cursor()方法获取操作游标
        cur.execute('select ID from user_list')
        results = cur.fetchall()
        for row in results:
            temp = str(row)
            n_lists.append(temp[2:len(temp) - 3])  # 所有已注册的id保存到n_lists
        cur.execute('select pw from user_list where id="%s"' % t_id)
        t_pw = cur.fetchone()  # 数据库中查询该昵称的密码
        temp_pw = str(t_pw)
        real_pw = temp_pw[2:len(temp_pw) - 3]
        print real_pw
        if t_id in n_lists and real_pw == str(hash(pw)):  # id存在且密码正确
            s.send("250log.login successfully")
            id_list[s] = t_id
            u_states[id_list[s]] = "on"

            send_xml(s)

            cur.execute('select nickname from id_nick where id="%s"' % t_id)  # 得到该用户昵称信息
            t_results = str(cur.fetchone())
            t_results = t_results[2:len(t_results) - 3]
            user_names[s] = t_results
            cur.execute('select friends_list from user_list where id="%s"' % t_id)  # 得到该用户好友列表信息
            t_results = str(cur.fetchone())
            friends_list[s] = t_results[2:len(t_results) - 3]
            get_friends_states(s, friends_list[s])  # 得到该用户的好友在线情况
            loged_list.append(s)
            broadto_friends_info(s, ip_port)  # 通知该用户的好友，我上线了

            #发群聊列表
            group_offline(s)

            cur.execute('select message from user_list where id="%s"' % t_id)
            t_results = str(cur.fetchone())
            if len(t_results) <10:    #没有离线消息
                pass
            else:                      #有离线消息
                s.send("OFFLINE."+ t_results[2:len(t_results)-3])
                cur.execute('update user_list set message = "" where id="%s"' % (t_id))  #清空message
                conn.commit()
            conn.close()
        else:
            s.send("505log.the id have not register yet or password wrong.try again!")

def send_xml(sock):
    filepath = id_list[sock]+".xml"
    print filepath
    if os.path.isfile(filepath):
        print "find xml"
        fileinfo_size = struct.calcsize('128sl')  # 定义打包规则
        # 定义文件头信息，包含文件名和文件大小
        fhead = struct.pack('128sl', os.path.basename(filepath), os.stat(filepath).st_size)
        sock.send(fhead)  # 加消息头
        fo = open(filepath, 'rb')
        while True:
            filedata = fo.read(1024)
            if not filedata:
                break
            sock.send(filedata)  # 加消息头
        fo.close()
        print 'send xml over...'

def change_pw(s,msg):
    if msg[9] =="0":s.send("250old_pw.please input your old password:")
    elif msg[9]=="1"or msg[9]=="2":
        if msg[9]=="1":
            w = msg[11:]
            conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
            cur = conn.cursor()  # 使用cursor()方法获取操作游标
            cur.execute('select pw from user_list where id="%s"' % id_list[s])
            t_pw = cur.fetchone()  # 数据库中查询该昵称的密码
            temp_pw = str(t_pw)
            real_pw = temp_pw[2:len(temp_pw) - 3]
            if real_pw == str(hash(w)):
                s.send("250new_pw.input your new password:")
            else:
                s.send("505change_pw.wrong old password!")
            conn.close()
        elif msg[9]=="2":
            new_password = msg[11:]
            conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
            cur = conn.cursor()  # 使用cursor()方法获取操作游标
            try:
                cur.execute('update user_list set pw ="%s" where id="%s"' % (str(hash(new_password)), id_list[s]))
                conn.commit()
                s.send("250change_pw.password have changed successfully!")
            except:
                # Rollback in case there is any error
                conn.rollback()
                s.send("505change_pw.something wrong with the SQL,Please try again!")
            conn.close()

def change_name(s,ip_port,msg):
    msg = msg[12:]
    if len(msg)>0:
        user_names[s] = msg
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
        cur = conn.cursor()  # 使用cursor()方法获取操作游标
        cur.execute('update id_nick set nickname ="%s" where id="%s"' % (msg, id_list[s]))
        conn.commit()
        conn.close()
        s.send("250change_name.change nickname successfully!")
        broadto_friends_info(s,ip_port)
    else:
        s.send("505change_name.illegal nickname.you can try again!")
def call_to(s,msg):
    msg = msg[5:]
    i = msg.index(":")
    t_id = msg[0:i]
    msg = msg[i+1:]
    lianjieguo = ""
    for t_sock in user_names.keys():
        if t_sock in loged_list:
           lianjieguo = lianjieguo + id_list[t_sock] + ""
    if t_id in lianjieguo and u_states[t_id] == "on":  # 如果对方在线，返回其IP和pubkey
        for temp_sock in user_names.keys():
            if id_list[temp_sock] == t_id: break
        IP = str(ip_list[temp_sock])
        i = IP.index(",")
        IP = IP[2:i - 1]    #得到对象IP
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
        cur = conn.cursor()  # 使用cursor()方法获取操作游标
        cur.execute('select pubkey from user_list where id="%s"' % id_list[s])
        t_results = str(cur.fetchone())
        Pubkey = t_results[2:len(t_results) - 3]  # 获取对象pubkey
        s.send("250call_to."+IP+":"+Pubkey)
    else:
        if msg[0]=="0":s.send("505call_to."+t_id+".sorry he is not online")
        elif msg[0]=="1":talk_to_off(s, msg[6:],t_id)
def add_friend(s,msg):
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    cur.execute('select id from user_list')
    results = cur.fetchall()
    n_lists=[]
    for row in results:
        temp = str(row)
        n_lists.append(temp[2:len(temp) - 3])  # 所有已注册的nickname保存到n_lists
    t_id = msg[4:]
    if t_id in n_lists:  # 该户名存在
        if t_id not in friends_list[s]:
            f_list = friends_list[s] + t_id + ";"
            friends_list[s] = f_list  # 添加到该用户的好友列表
            cur.execute('select friends_list from user_list where id="%s"' % t_id)
            t_results = str(cur.fetchone())
            fri_list = t_results[2:len(t_results) - 3]
            fri_list = fri_list + id_list[s] + ";"  # 对方好友列表里也添加他
            try:
                cur.execute('update user_list set friends_list ="%s" where id="%s"' % (f_list, id_list[s]))
                cur.execute('update user_list set friends_list ="%s" where id="%s"' % (fri_list, t_id))
                conn.commit()
                s.send("250add.add friend successfully!")
                get_friends_states(s, f_list)  # 通知更新此用户的好友列表

                lianjieguo = ""
                for t_sock in user_names.keys():
                    if t_sock in loged_list:
                        lianjieguo = lianjieguo + id_list[t_sock] + ""
                if t_id in lianjieguo and u_states[t_id] == "on":  # 如果对方在线，也通知更新对方的好友列表
                    for temp_sock in user_names.keys():
                        if id_list[temp_sock] == t_id: break
                    get_friends_states(temp_sock, fri_list)
                    friends_list[temp_sock] = fri_list

            except:
                # Rollback in case there is any error
                conn.rollback()
                s.send("505add.something wrong with the SQL,Please try again!")
        else:
            s.send("505add.he is already your friends!")
    else:
        s.send("505add.sorry, this name does not exit!")
    conn.close()
def del_friend(s,msg):
    t_id = msg[4:]
    friends = friends_list[s]
    if t_id in friends:
        i = friends.find(t_id)
        new_friends = friends[0:i] + friends[i + len(t_id) + 1:]
        friends_list[s] = new_friends  # 新friends列表

        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
        cur = conn.cursor()  # 使用cursor()方法获取操作游标
        cur.execute('select friends_list from user_list where id="%s"' % t_id)
        t_results = str(cur.fetchone())
        fri_list = t_results[2:len(t_results) - 3]  # 对方的好友列表
        i = fri_list.find(id_list[s])
        new_fri = fri_list[0:i] + fri_list[i + len(id_list[s]) + 1:]  # 对方新fri列表
        try:
            cur.execute('update user_list set friends_list ="%s" where id="%s"' % (
            new_friends, id_list[s]))  # 该用户新friends列表更新到数据库
            cur.execute('update user_list set friends_list ="%s" where id="%s"' % (new_fri, t_id))  # 对方列表也更新
            conn.commit()
            conn.close()
            s.send("250del.del friend successfully!")
            get_friends_states(s, new_friends)  # 通知更新此用户的好友列表

            lianjieguo = ""
            for t_sock in user_names.keys():
                if t_sock in loged_list:
                    lianjieguo = lianjieguo + id_list[t_sock] + ""
            if t_id in lianjieguo and u_states[t_id] == "on":  # 如果对方在线，也通知更新对方的好友列表
                for temp_sock in user_names.keys():
                    if id_list[temp_sock] == t_id: break
                get_friends_states(temp_sock, new_fri)
                friends_list[temp_sock] = new_fri
        except:
            # Rollback in case there is any error
            conn.rollback()
            s.send("505del.something wrong with the SQL,Please try again!")
    else:
        s.send("505del.he is not your friend ")

def broadto_friends_info(s,ip_port):
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    cur.execute('select friends_list from user_list where id="%s"' % id_list[s])
    t_results = str(cur.fetchone())
    f_list = t_results[2:len(t_results) - 3]        #获取该用户好友列表
    conn.close()
    ip_port = str(ip_port)
    i = ip_port.index(",")
    u_info[id_list[s]] = id_list[s] +":"+user_names[s]+ ":"+u_states[id_list[s]]
    if u_states[id_list[s]]=="on":
        u_info[id_list[s]] = u_info[id_list[s]]+ ":"+ ip_port[2:i - 1] + ":" + ip_port[i + 2:len(ip_port) - 1] + ";"
    else:
        u_info[id_list[s]] = u_info[id_list[s]] + ";"
    for t_sock in user_names.keys():
        if t_sock in loged_list and t_sock != s :     #不发给自己
            if id_list[t_sock] in f_list and u_states[id_list[t_sock]]=="on":   #只发给该用户的在线好友
                t_sock.send("updatef."+u_info[id_list[s]])
def get_friends_states(s,myfriends):
    my_friends_states = ""
    lianjieguo = ""
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    for t_sock in user_names.keys():
        if t_sock in loged_list:
           lianjieguo = lianjieguo + id_list[t_sock] + ""
    while len(myfriends)>1:
        i = myfriends.index(";")
        f_id = myfriends[0:i]
        if f_id in lianjieguo and u_states[f_id] == "on":
            my_friends_states = my_friends_states + u_info[f_id]
        else:
            cur.execute('select nickname from id_nick where id="%s"' % f_id)
            t_results = str(cur.fetchone())
            nick = t_results[2:len(t_results) - 3]  # 获取其昵称
            my_friends_states = my_friends_states + f_id + ":" +nick+ ":" + "off" + ";"
        myfriends = myfriends[i+1:]
    conn.close()
    messag_list = "friends_states."+id_list[s]+":"+user_names[s]+";"+ my_friends_states
    s.send(messag_list)

def group_chat(s,msg):      #通知所有所有群成员你已在群
    flag = 1
    n_lists = []  # 保存已存在的ID
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    cur.execute('select ID from user_list')
    results = cur.fetchall()
    conn.close()
    for row in results:
        temp = str(row)
        n_lists.append(temp[2:len(temp) - 3])  # 所有已注册的id保存到n_lists
    t_m = msg[11:]
    while len(t_m) > 2:
        i = t_m.index(":")
        id = t_m[0:i]
        t_m = t_m[i + 1:]
        if t_m>2 and id not in n_lists:flag = 0
    if flag ==1 :
        messag = msg[11:] + id_list[s] + ":"  # 给该群的每一个人(包括他自己）发通知 id:id:id:in the group chat
        group_id[1] = messag = msg[11:] + id_list[s] + ":"
        m = msg = messag
        messag = "GGG."
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
        cur = conn.cursor()  # 使用cursor()方法获取操作游标
        while len(m) > 2:
            i = m.index(":")
            id = m[0:i]
            m = m[i + 1:]
            cur.execute('select nickname from id_nick where id ="%s"' % id)
            results = str(cur.fetchone())
            messag = messag + id + ":" + results[2:len(results) - 3] + ";"
        conn.close()
        while len(msg) > 2:
            i = msg.index(":")
            id = msg[0:i]
            msg = msg[i + 1:]
            if u_states[id] == "on":
                for t_sock in user_names.keys():
                    if id_list[t_sock] == id: break
                t_sock.send(messag)
            else:
                print id + " not online"
                conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
                cur = conn.cursor()  # 使用cursor()方法获取操作游标
                try:
                    t_msg = messag
                    cur.execute('update group_msg set tongzhi = "%s" where id="%s"' % (t_msg, id))
                    conn.commit()
                except:
                    # Rollback in case there is any error
                    conn.rollback()
                conn.close()
    else:
        s.send("505group_chat.at least one id not exist")

def group_offline(sock):
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    cur.execute('select tongzhi from group_msg where id="%s"' % id_list[sock])
    t_results = str(cur.fetchone())
    if len(t_results) < 10:   #没有群通知
        pass
    else:
        sock.send(t_results[2:len(t_results) - 3])
        try:
            cur.execute('update group_msg set tongzhi = "" where id="%s"' % id_list[sock])
            conn.commit()
        except:
            # Rollback in case there is any error
            conn.rollback()
    cur.execute('select wenjian from group_msg where id="%s"' % id_list[sock])
    t_results = str(cur.fetchone())
    if len(t_results) < 10:  # 没有群文件通知
        pass
    else:
        sock.send(t_results[2:len(t_results) - 3])
        try:
            cur.execute('update group_msg set wenjian = "" where id="%s"' % id_list[sock])
            conn.commit()
        except:
            # Rollback in case there is any error
            conn.rollback()
    cur.execute('select message from group_msg where id="%s"' % id_list[sock])
    t_results = str(cur.fetchone())
    if len(t_results) < 10:  # 没有群聊天消息通知
        pass
    else:
        sock.send(t_results[2:len(t_results) - 3])
        try:
            cur.execute('update group_msg set message = "" where id="%s"' % id_list[sock])
            conn.commit()
        except:
            # Rollback in case there is any error
            conn.rollback()
        print "sql wrong"
    conn.close()

def group_messag(s,msg):
    msg = msg[10:]
    if msg[0:11]=="pause_group":
        msg = msg[12:]
        group_gono[msg] = "pause"
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # 不发给他自己
                if u_states[id] == "on":  # 成员在线
                    if group_gono[id] == "on":  # 未屏蔽群消息
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GGM."+msg+":"+user_names[s]+" paused messags")
    elif msg[0:10]=="back_group":
        msg = msg[11:]
        group_gono[msg] = "on"
        s.send("OFFGMSG."+ group_msg[msg])  #把屏蔽期间的消息发给他
        group_msg[msg] = ""
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # 不发给他自己
                if u_states[id] == "on":  # 成员在线
                    if group_gono[id] == "on":  # 未屏蔽群消息
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GGM." + msg + ":" + user_names[s] + " back")
    elif msg[0:11]=="leave_group":
        msg=msg[12:]
        ids = group_id[1]
        i = ids.find(msg)
        group_id[1] = ids[0:i]+ ids[i+len(msg)+1:]
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # 不发给他自己
                if u_states[id] == "on":  # 成员在线
                    if group_gono[id] == "on":  # 未屏蔽群消息
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GGM." + msg + ":" + user_names[s] + " leave the group")
    elif msg[0:8]=="up_file0":
        send_pubkey(s)
        file_buffer[id_list[s]] = msg[9:]  #文件名
    elif msg[0:8]=="up_file1":
        if msg[9]=="k":
            msg = msg[11:]
            i = msg.index(":")
            id = msg[0:i]
            u_skey[id] = msg[i+1:]
        elif msg[9]=="v":
            msg = msg[11:]
            i = msg.index(":")
            id = msg[0:i]
            u_svector[id] = msg[i+1:]

    elif msg[0:8]=="up_file2":
        unknow_pad[file_buffer[id_list[s]]] = msg[9:]
    elif msg[0:8]=="up_file3":
        if msg[9:]!="EOF": up_file(s,msg[9:])  #成功接收客户端文件
        elif msg[9:] =="EOF":
            print "recv file done"
            s.send("250up_file:"+file_buffer[id_list[s]])
            ids = group_id[1]
            while len(ids) > 2:
                i = ids.index(":")
                id = ids[0:i]
                ids = ids[i + 1:]
                if id != id_list[s]:  # 不发给他自己
                    if u_states[id] == "on":  # 成员在线
                        if group_gono[id] == "on":  # 未屏蔽群消息
                            for t_sock in user_names.keys():
                                if id_list[t_sock] == id: break
                            t_sock.send("GFU." + id_list[s] + ":" + user_names[s] + " update file:"+file_buffer[id_list[s]])
                    else:  # 成员不在线
                        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
                        cur = conn.cursor()  # 使用cursor()方法获取操作游标
                        t_messag = "GFU." + id_list[s] + ":" + user_names[s] + " update file:"+file_buffer[id_list[s]]
                        try:
                            cur.execute('update group_msg set wenjian = "%s" where id="%s"' % (t_messag, id))
                            conn.commit()
                        except:
                            # Rollback in case there is any error
                            conn.rollback()
                        conn.close()

    elif msg[0:10]=="down_file0":
        down_file(s,msg[11:])     #msg = "down_file id [PS: msg[11:]==filename
        #发文件 s.send(file_buffer)
    else:
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # 不发给他自己
                if u_states[id] == "on":  # 成员在线
                    if group_gono[id]=="on":  #未屏蔽群消息
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GMSG."+ msg)
                    elif group_gono[id]=="pause":       #暂时屏蔽了群消息
                        i = msg.index(":")
                        name = msg[0:i]
                        j = msg.index("$")
                        time = msg[i+1:j]
                        group_msg[id] = group_msg[id]+ name + "("+time+")\n"+msg[j+1:]+"\n"
                else:    #未在线
                    print id + " not online"
                    i = msg.index(":")
                    name = msg[0:i]
                    j = msg.index("$")
                    time = msg[i + 1:j]
                    msg = name + "("+time+")\n"+msg[j+1:]+"\n"
                    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
                    cur = conn.cursor()  # 使用cursor()方法获取操作游标
                    cur.execute('select message from group_msg where id="%s"' % id)
                    t_results = str(cur.fetchone())
                    if len(t_results) < 10:
                        t_messag = "OFFGMSG."+msg
                    else:
                        t_messag = t_results[2:len(t_results)-3]+ msg
                    try:
                        cur.execute('update group_msg set message = "%s" where id="%s"' % (t_messag, id))
                        conn.commit()
                    except:
                        # Rollback in case there is any error
                        conn.rollback()
                    conn.close()

def send_pubkey(sock):
    ids = group_id[1]
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    while len(ids) > 2:
        i = ids.index(":")
        id = ids[0:i]
        ids = ids[i + 1:]
        if id != id_list[sock]:  # 不发给他自己
            cur.execute('select pubkey from user_list where id="%s"' % id)
            t_results = str(cur.fetchone())
            sock.send("up_file0:"+id+":"+t_results[2:len(t_results)-3])
    sock.send("up_file0:EOF")

def up_file(sock,msg):         #客户端up_file,服务器收文件
    fname=file_buffer[id_list[sock]]
    i=fname.index(".")
    fname = fname[0:i]
    fname = os.path.join('E:\\', (fname))  # 存在 D 根目录
    fname = fname +".txt"
    file = open(fname, 'a')
    if msg[0]=="p":
        msg = msg[4:]
        file.write(msg)
        file.close()
    elif msg[0]=="u":
        msg = msg[6:]
        file.write(msg)
        file.close()


def down_file(sock,fname):   #客户端down_file,服务器发文件
    i = fname.index(".")
    name = fname[0:i]
    name = os.path.join('E:\\', (name))
    name = name + ".txt"
    file = open(name, 'rb')
    filesize =0
    while True:
        filedata = file.read(1024)
        if not filedata:
            break
        else:
            filesize = filesize + len(filedata)
    file.close()
    file = open(name, 'rb')
    while True:
        if filesize >1024:
            filedata = file.read(1024)
            filesize = filesize -1024
            sock.send("down_file1:unpad:" + filedata)
        elif filesize<1024 and filesize>0:
            filedata = file.read(filesize)
            if unknow_pad[fname]=="pad":
                sock.send("down_file1:pad:" + filedata)
            elif unknow_pad[fname]=="unpad":
                sock.send("down_file1:unpad:" + filedata)
            break
    file.close()
    sock.send("down_file1:EOF")
    print "send file done"

def talk_to_off(sock,messag,id):
    i=messag.index(":")
    name = messag[0:i]
    j=messag.index("$")
    time =messag[i+1:j]
    messag = messag[j+1:]
    msg = name +"("+time+")\n"+messag+"\n"
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    cur.execute('select message from user_list where id="%s"' % id)
    t_results = str(cur.fetchone())
    if len(t_results) <10:
        messag = msg
    else:
        messag = t_results[2:len(t_results)-3] + msg
    try:
        cur.execute('update user_list set message = "%s" where id="%s"' % (messag,id))
        conn.commit()
    except:
        # Rollback in case there is any error
        conn.rollback()
        sock.send("505.something wrong with the SQL,Please try again!")
    conn.close()

def initialization():
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # 连接SQL并使用QQ这个数据库
    cur = conn.cursor()  # 使用cursor()方法获取操作游标
    cur.execute('select ID from user_list')
    results = cur.fetchall()
    conn.close()
    for row in results:
        temp = str(row)
        temp = temp[2:len(temp) - 3]  # 所有已注册的id保存到n_lists
        u_states[temp] = "off"
        group_gono[temp]= "on"
        group_msg[temp] = ""



if __name__ == "__main__":
    main()