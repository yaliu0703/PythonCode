# -*- coding: gbk -*-
import sys
reload(sys)
sys.setdefaultencoding('gbk')
'''
Created on 2016��6��30��
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
global HOST, PORT,RECV_BUFFER,connection_lists,loged_list,user_names,u_states,u_info,friends_list,ip_list,ID,group_id,group_gono,group_msg,file_buffer,key_iv,file_data
global u_skey,u_svector,unknow_pad,offline_msg
#HOST, PORT = gethostbyname(gethostname()), 5000
HOST, PORT = '10.201.9.147', 5000
ID = 20168
RECV_BUFFER = 103000
ip_list = {}              #����ÿ��socket��IP
connection_lists = [""]   #Ϊsocket�����б� fileno()��
loged_list = [""]         #�����¼�ɹ����ߵ�sock�б���ֹ�ظ���¼
id_list = {}              #ÿ���û����˺�,IDΨһ��ʶ,����
user_names = {}           #ÿ���û����ǳ�
u_info = {}               #ÿ���û�����Ϣ���ǳƣ�ip���˿ڣ�
u_states = {}             #ÿ���û�������״̬
friends_list = {}         #ÿ���û��ĺ����б�
group_id = {}             #Ⱥ���г�Աid
group_gono = {}           #�Ƿ�����Ⱥ��Ϣ
group_msg = {}            #�ݴ������˵�Ⱥ��Ϣ
file_buffer = {}          #����Ⱥ�ļ���Ϣ,���ϴ��ߵ�ID�������ļ��ļ���
u_skey = {}               #Ⱥ����ÿ��Ⱥ��Ա��Կ���ܵĻỰ��Կ
u_svector = {}            #Ⱥ����ÿ��Ⱥ��Ա��Կ���ܵ�����
unknow_pad = {}           #�ļ����һ���Ƿ����
offline_msg = {}         #�ݴ�������Ϣ
key_iv = {}
file_data ={}             #�ݴ���ܺ���ļ�����

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
               """���������Ѿ�����listening״̬�´˷�������һ������socket�������������š�
                                  �������ͨ�����ݸ�select.select(),�Ա�������ͬһ�������ж��server��socket�ļ�����"""
               # ADD new connections
               for sock in user_names.keys():
                   connection_lists.append(sock.fileno())  # ��socket�б����������
               print connection_lists
               try:
                   read, write, error = select.select(connection_lists, [], [],3)  # select for reading from all sockets
               except select.error, detail:
                   print detail
                   break
               print read
               for n in read:
                   if n == server.fileno():  # ����Ϣ���µ���������
                       print"new connection"
                       sock, addr = server.accept()
                       ip_list[sock] = addr
                       id_list[sock] = None
                       user_names[sock] = None
                   else:  # ����Ϣ�����������ӵĿͻ���
                       for sock in user_names.keys():
                           if sock.fileno() == n: break
                       name = user_names[sock]  # �û���nickname
                       try:
                           message = sock.recv(RECV_BUFFER)
                           print message
                           if message[0:8] == "register":
                               register(sock,message)
                           elif message[0:3] == "log":
                               login(sock, ip_list[sock], message)
                           elif message[0:4] == "call": #������Ϣ��ʽ call:id:0:˵�Ļ������߸�ʽcall:id:����
                               call_to(sock, message)
                           elif message[0:9] == "change_pw":
                               change_pw(sock,message)
                           elif message[0:11] == "change_name":
                               change_name(sock, ip_list[sock], message)
                           elif message[0:3] == "add":
                               add_friend(sock, message)
                           elif message[0:3] == "del":
                               del_friend(sock, message)
                           elif message[0:10]=="group_chat":  #��Ϣ��ʽ group_chat:id:id:id:
                               group_chat(sock,message)
                           elif message[0:9]=="group_msg":    #��Ϣ��ʽ group_msg:��װ�õ���Ϣ  PS:��װ�õ���Ϣָ�ͻ���Ҫ��ʾ����Ϣ��ʽ id:�ǳƣ�ʱ�䣺xxx
                               group_messag(sock,message)
                           elif message[0:4] == "quit":
                               u_states[id_list[sock]] = "off"
                               broadto_friends_info(sock, ip_list[sock])  # ֪ͨ���û��ĺ��ѣ���������
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
        publikey = pubn + "," + pube #��Կ�ַ���
        privn = str(privkey.n)
        prive = str(privkey.e)
        privd = str(privkey.d)
        privp = str(privkey.p)
        privq = str(privkey.q)
        privatekey = privn +","+prive+","+privd+","+privp+","+privq   #˽Կ�ַ���
        global ID
        genxml(str(ID), privatekey, publikey)

        try:
            # s.send(֤�飩
            conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
            cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
    t_id = msg[0:j]  # �õ�id
    pw = msg[j + 1:]  # �õ�password

    onlined = 0
    for t_sock in user_names.keys():
        if t_sock in loged_list and id_list[t_sock]==t_id:
           onlined=1
    if onlined==1:
        s.send("505log.you have loged already!")
    else:
        n_lists = []  # �����Ѵ��ڵ�ID
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
        cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
        cur.execute('select ID from user_list')
        results = cur.fetchall()
        for row in results:
            temp = str(row)
            n_lists.append(temp[2:len(temp) - 3])  # ������ע���id���浽n_lists
        cur.execute('select pw from user_list where id="%s"' % t_id)
        t_pw = cur.fetchone()  # ���ݿ��в�ѯ���ǳƵ�����
        temp_pw = str(t_pw)
        real_pw = temp_pw[2:len(temp_pw) - 3]
        print real_pw
        if t_id in n_lists and real_pw == str(hash(pw)):  # id������������ȷ
            s.send("250log.login successfully")
            id_list[s] = t_id
            u_states[id_list[s]] = "on"

            send_xml(s)

            cur.execute('select nickname from id_nick where id="%s"' % t_id)  # �õ����û��ǳ���Ϣ
            t_results = str(cur.fetchone())
            t_results = t_results[2:len(t_results) - 3]
            user_names[s] = t_results
            cur.execute('select friends_list from user_list where id="%s"' % t_id)  # �õ����û������б���Ϣ
            t_results = str(cur.fetchone())
            friends_list[s] = t_results[2:len(t_results) - 3]
            get_friends_states(s, friends_list[s])  # �õ����û��ĺ����������
            loged_list.append(s)
            broadto_friends_info(s, ip_port)  # ֪ͨ���û��ĺ��ѣ���������

            group_offline(s)
            cur.execute('select message from user_list where id="%s"' % t_id)
            t_results = str(cur.fetchone())
            if len(offline_msg[t_id]) <10:    #û��������Ϣ
                pass
            else:                      #��������Ϣ
                time.sleep(1)
                s.send("OFFLINE."+ offline_msg[t_id])
                offline_msg[t_id] = ""
                cur.execute('update user_list set message = "" where id="%s"' % (t_id))  #���message
                conn.commit()
            conn.close()

            if id_list[s] in group_id[1]:    #�û���Ⱥ����
                conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
                cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
                m = group_id[1]
                messag = ""
                while len(m) > 2:
                    i = m.index(":")
                    id = m[0:i]
                    m = m[i + 1:]
                    cur.execute('select nickname from id_nick where id ="%s"' % id)
                    results = str(cur.fetchone())
                    messag = messag + id + ":" + results[2:len(results) - 3] + ";"
                time.sleep(1)
                s.send("OFFGROUP_LIST."+messag)
                conn.close()


        else:
            s.send("505log.the id have not register yet or password wrong.try again!")

def send_xml(sock):
    filepath = id_list[sock]+".xml"
    print filepath
    if os.path.isfile(filepath):
        fileinfo_size = struct.calcsize('128sl')  # ����������
        # �����ļ�ͷ��Ϣ�������ļ������ļ���С
        fhead = struct.pack('128sl', os.path.basename(filepath), os.stat(filepath).st_size)
        sock.send(fhead)  # ����Ϣͷ
        fo = open(filepath, 'rb')
        while True:
            filedata = fo.read(1024)
            if not filedata:
                break
            sock.send(filedata)  # ����Ϣͷ
        fo.close()
        print 'send xml over...'

def change_pw(s,msg):
    if msg[9] =="0":s.send("250old_pw.please input your old password:")
    elif msg[9]=="1"or msg[9]=="2":
        if msg[9]=="1":
            w = msg[11:]
            conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
            cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
            cur.execute('select pw from user_list where id="%s"' % id_list[s])
            t_pw = cur.fetchone()  # ���ݿ��в�ѯ���ǳƵ�����
            temp_pw = str(t_pw)
            real_pw = temp_pw[2:len(temp_pw) - 3]
            if real_pw == str(hash(w)):
                s.send("250new_pw.input your new password:")
            else:
                s.send("505change_pw.wrong old password!")
            conn.close()
        elif msg[9]=="2":
            new_password = msg[11:]
            conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
            cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
        cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
    if t_id in lianjieguo and u_states[t_id] == "on":  # ����Է����ߣ�������IP��pubkey
        for temp_sock in user_names.keys():
            if id_list[temp_sock] == t_id: break
        IP = str(ip_list[temp_sock])
        i = IP.index(",")
        IP = IP[2:i - 1]    #�õ�����IP
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
        cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
        cur.execute('select pubkey from user_list where id="%s"' % id_list[s])
        t_results = str(cur.fetchone())
        Pubkey = t_results[2:len(t_results) - 3]  # ��ȡ����pubkey
        s.send("250call_to."+IP+":"+Pubkey)
    else:
        if msg[0]=="0":s.send("505call_to."+t_id+".sorry he is not online")
        elif msg[0]=="1":talk_to_off(s, msg[6:],t_id)
def add_friend(s,msg):
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    cur.execute('select id from user_list')
    results = cur.fetchall()
    n_lists=[]
    for row in results:
        temp = str(row)
        n_lists.append(temp[2:len(temp) - 3])  # ������ע���nickname���浽n_lists
    t_id = msg[4:]
    if t_id in n_lists:  # �û�������
        if t_id not in friends_list[s]:
            f_list = friends_list[s] + t_id + ";"
            friends_list[s] = f_list  # ��ӵ����û��ĺ����б�
            cur.execute('select friends_list from user_list where id="%s"' % t_id)
            t_results = str(cur.fetchone())
            fri_list = t_results[2:len(t_results) - 3]
            fri_list = fri_list + id_list[s] + ";"  # �Է������б���Ҳ�����
            try:
                cur.execute('update user_list set friends_list ="%s" where id="%s"' % (f_list, id_list[s]))
                cur.execute('update user_list set friends_list ="%s" where id="%s"' % (fri_list, t_id))
                conn.commit()
                s.send("250add.add friend successfully!")
                get_friends_states(s, f_list)  # ֪ͨ���´��û��ĺ����б�

                lianjieguo = ""
                for t_sock in user_names.keys():
                    if t_sock in loged_list:
                        lianjieguo = lianjieguo + id_list[t_sock] + ""
                if t_id in lianjieguo and u_states[t_id] == "on":  # ����Է����ߣ�Ҳ֪ͨ���¶Է��ĺ����б�
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
        friends_list[s] = new_friends  # ��friends�б�

        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
        cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
        cur.execute('select friends_list from user_list where id="%s"' % t_id)
        t_results = str(cur.fetchone())
        fri_list = t_results[2:len(t_results) - 3]  # �Է��ĺ����б�
        i = fri_list.find(id_list[s])
        new_fri = fri_list[0:i] + fri_list[i + len(id_list[s]) + 1:]  # �Է���fri�б�
        try:
            cur.execute('update user_list set friends_list ="%s" where id="%s"' % (
            new_friends, id_list[s]))  # ���û���friends�б���µ����ݿ�
            cur.execute('update user_list set friends_list ="%s" where id="%s"' % (new_fri, t_id))  # �Է��б�Ҳ����
            conn.commit()
            conn.close()
            s.send("250del.del friend successfully!")
            get_friends_states(s, new_friends)  # ֪ͨ���´��û��ĺ����б�

            lianjieguo = ""
            for t_sock in user_names.keys():
                if t_sock in loged_list:
                    lianjieguo = lianjieguo + id_list[t_sock] + ""
            if t_id in lianjieguo and u_states[t_id] == "on":  # ����Է����ߣ�Ҳ֪ͨ���¶Է��ĺ����б�
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
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    cur.execute('select friends_list from user_list where id="%s"' % id_list[s])
    t_results = str(cur.fetchone())
    f_list = t_results[2:len(t_results) - 3]        #��ȡ���û������б�
    conn.close()
    ip_port = str(ip_port)
    i = ip_port.index(",")
    u_info[id_list[s]] = id_list[s] +":"+user_names[s]+ ":"+u_states[id_list[s]]
    if u_states[id_list[s]]=="on":
        u_info[id_list[s]] = u_info[id_list[s]]+ ":"+ ip_port[2:i - 1] + ":" + ip_port[i + 2:len(ip_port) - 1] + ";"
    else:
        u_info[id_list[s]] = u_info[id_list[s]] + ";"
    for t_sock in user_names.keys():
        if t_sock in loged_list and t_sock != s :     #�������Լ�
            if id_list[t_sock] in f_list and u_states[id_list[t_sock]]=="on":   #ֻ�������û������ߺ���
                t_sock.send("updatef."+u_info[id_list[s]])
def get_friends_states(s,myfriends):
    my_friends_states = ""
    lianjieguo = ""
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
            nick = t_results[2:len(t_results) - 3]  # ��ȡ���ǳ�
            my_friends_states = my_friends_states + f_id + ":" +nick+ ":" + "off" + ";"
        myfriends = myfriends[i+1:]
    conn.close()
    messag_list = "friends_states."+id_list[s]+":"+user_names[s]+";"+ my_friends_states
    s.send(messag_list)

def group_chat(s,msg):      #֪ͨ��������Ⱥ��Ա������Ⱥ
    flag = 1
    n_lists = []  # �����Ѵ��ڵ�ID
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    cur.execute('select ID from user_list')
    results = cur.fetchall()
    conn.close()
    for row in results:
        temp = str(row)
        n_lists.append(temp[2:len(temp) - 3])  # ������ע���id���浽n_lists
    t_m = msg[11:]
    while len(t_m) > 2:
        i = t_m.index(":")
        id = t_m[0:i]
        t_m = t_m[i + 1:]
        if t_m>2 and id not in n_lists:flag = 0
    if flag ==1 :                                   #Ⱥ��Ա��id���Ϸ�
        messag = msg[11:] + id_list[s] + ":"  # ����Ⱥ��ÿһ����(�������Լ�����֪ͨ id:id:id:in the group chat
        group_id[1] =  msg[11:] + id_list[s] + ":"
        m = msg = messag
        messag = "GGG."
        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
        cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
                conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
                cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    cur.execute('select tongzhi from group_msg where id="%s"' % id_list[sock])
    t_results = str(cur.fetchone())
    if len(t_results) < 10:   #û��Ⱥ֪ͨ
        pass
    else:
        time.sleep(1)
        sock.send(t_results[2:len(t_results) - 3])
        try:
            cur.execute('update group_msg set tongzhi = "" where id="%s"' % id_list[sock])
            conn.commit()
        except:
            # Rollback in case there is any error
            conn.rollback()
    cur.execute('select wenjian from group_msg where id="%s"' % id_list[sock])
    t_results = str(cur.fetchone())
    if len(t_results) < 10:  # û��Ⱥ�ļ�֪ͨ
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
    if len(t_results) < 10:  # û��Ⱥ������Ϣ֪ͨ
        pass
    else:
        time.sleep(1)
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
    if msg[0:11]=="pause_group" and msg[12:] in group_id[1]:
        msg = msg[12:]
        group_gono[msg] = "pause"
        """"
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # ���������Լ�
                if u_states[id] == "on":  # ��Ա����
                    if group_gono[id] == "on":  # δ����Ⱥ��Ϣ
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GGM."+msg+":"+user_names[s]+" paused messags")"""
    elif msg[0:10]=="back_group" and msg[12:] in group_id[1]:
        msg = msg[11:]
        group_gono[msg] = "on"
        s.send("OFFGMSG."+ group_msg[msg])  #�������ڼ����Ϣ������
        group_msg[msg] = ""
        """
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # ���������Լ�
                if u_states[id] == "on":  # ��Ա����
                    if group_gono[id] == "on":  # δ����Ⱥ��Ϣ
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GGM." + msg + ":" + user_names[s] + " back")"""
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
            if id != id_list[s]:  # ���������Լ�
                if u_states[id] == "on":  # ��Ա����
                    if group_gono[id] == "on":  # δ����Ⱥ��Ϣ
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GGM." + msg + ":" + user_names[s] + " leave the group")
    elif msg[0:8]=="up_file0":
        send_pubkey(s)
        file_buffer[id_list[s]] = msg[9:]  #�ļ���
        file_data[msg[9:]] =""
    elif msg[0:8]=="up_file1":
        key_iv[file_buffer[id_list[s]]] = msg[9:]


    elif msg[0:8]=="up_file2":
        unknow_pad[file_buffer[id_list[s]]] = msg[9:]
    elif msg[0:8]=="up_file3":
        if msg[9:]!="EOF":
            up_file(s,msg[9:])  #�ɹ����տͻ����ļ�
            print "recv len:",len(msg[9:])
        elif msg[9:] =="EOF":
            print "recv file done"
            s.send("250up_file:"+file_buffer[id_list[s]])
            ids = group_id[1]
            while len(ids) > 2:
                i = ids.index(":")
                id = ids[0:i]
                ids = ids[i + 1:]
                if id != id_list[s]:  # ���������Լ�
                    if u_states[id] == "on":  # ��Ա����
                        if group_gono[id] == "on":  # δ����Ⱥ��Ϣ
                            for t_sock in user_names.keys():
                                if id_list[t_sock] == id: break
                            t_sock.send("GFU." + id_list[s] + ":" + user_names[s] + ":update file:"+file_buffer[id_list[s]])
                    else:  # ��Ա������
                        conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
                        cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
                        t_messag = "GFU." + id_list[s] + ":" + user_names[s] + " update file:"+file_buffer[id_list[s]]
                        try:
                            cur.execute('update group_msg set wenjian = "%s" where id="%s"' % (t_messag, id))
                            conn.commit()
                        except:
                            # Rollback in case there is any error
                            conn.rollback()
                        conn.close()

    elif msg[0:10]=="down_file0":   #��Ϣ��ʽ down_file0:filename
        if msg[10]=="#":
            down_file(s, msg[12:])  # msg = "down_file id [PS: msg[11:]==filename
        else:
            s.send("down_file0:" + key_iv[msg[11:]])
    else:
        ids = group_id[1]
        while len(ids) > 2:
            i = ids.index(":")
            id = ids[0:i]
            ids = ids[i + 1:]
            if id != id_list[s]:  # ���������Լ�
                if u_states[id] == "on":  # ��Ա����
                    if group_gono[id]=="on":  #δ����Ⱥ��Ϣ
                        for t_sock in user_names.keys():
                            if id_list[t_sock] == id: break
                        t_sock.send("GMSG."+ msg)
                        print t_sock.fileno()
                    elif group_gono[id]=="pause":       #��ʱ������Ⱥ��Ϣ
                        i = msg.index(":")
                        name = msg[0:i]
                        j = msg.index("$")
                        time1 = msg[i+1:j]
                        group_msg[id] = group_msg[id]+ name + "("+time1+")\n"+msg[j+1:]+"\n"
                else:    #δ����
                    print id + " not online"
                    i = msg.index(":")
                    name = msg[0:i]
                    j = msg.index("$")
                    time1 = msg[i + 1:j]
                    msg = name + "("+time1+")\n"+msg[j+1:]+"\n"
                    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
                    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
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
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    while len(ids) > 2:
        i = ids.index(":")
        id = ids[0:i]
        ids = ids[i + 1:]
        if id != id_list[sock]:  # ���������Լ�
            cur.execute('select pubkey from user_list where id="%s"' % id)
            t_results = str(cur.fetchone())
            sock.send("up_file0:"+id+":"+t_results[2:len(t_results)-3])
            time.sleep(1)
    time.sleep(1)
    sock.send("up_file0:EOF")

def up_file(sock,msg):         #�ͻ���up_file,���������ļ�
    fname=file_buffer[id_list[sock]]
    file_data[fname] = file_data[fname]+msg
    i=fname.index(".")
    fname = fname[0:i]
    fname = os.path.join('E:\\', (fname))  # ���� D ��Ŀ¼
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


def down_file(sock,fname):   #�ͻ���down_file,���������ļ�
    i = fname.index(".")
    """name = fname[0:i]
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
    file = open(name, 'rb')"""
    """while True:
        if filesize >10240:
            filedata = file.read(10240)
            filesize = filesize -10240
            sock.send("down_file1:unpad:" + filedata)
            time.sleep(1)
        elif filesize<10240 and filesize>0:
            filedata = file.read(filesize)
            if unknow_pad[fname]=="pad":
                sock.send("down_file1:pad:" + filedata)
            elif unknow_pad[fname]=="unpad":
                sock.send("down_file1:unpad:" + filedata)
            break"""
    sock.send("down_file1:"+file_data[fname])
    #file.close()
    time.sleep(2)
    sock.send("down_file1:EOF")
    print "send file done size:",len(file_data[fname])

def talk_to_off(sock,messag,id):
    i=messag.index(":")
    name = messag[0:i]
    j=messag.index("$")
    time1 =messag[i+1:j]
    messag = messag[j+1:]
    msg = name +"("+time1+")\n"+messag+"\n"
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    cur.execute('select message from user_list where id="%s"' % id)
    t_results = str(cur.fetchone())
    if len(offline_msg[id]) <10:
        offline_msg[id] = id_list[sock]+":"+user_names[sock]+":"+msg +"###"
    else:
        offline_msg[id] = offline_msg[id] + id_list[sock]+":"+user_names[sock]+":"+msg +"###"
    try:
        cur.execute('update user_list set message = "%s" where id="%s"' % (offline_msg[id],id))
        conn.commit()
    except:
        # Rollback in case there is any error
        conn.rollback()
        sock.send("505.something wrong with the SQL,Please try again!")
    conn.close()

def initialization():
    conn = MySQLdb.connect("localhost", "root", "123321lfy", "QQ")  # ����SQL��ʹ��QQ������ݿ�
    cur = conn.cursor()  # ʹ��cursor()������ȡ�����α�
    cur.execute('select ID from user_list')
    results = cur.fetchall()
    conn.close()
    for row in results:
        temp = str(row)
        temp = temp[2:len(temp) - 3]  # ������ע���id���浽n_lists
        u_states[temp] = "off"
        group_gono[temp]= "on"
        group_msg[temp] = ""
        offline_msg[temp] = ""
        group_id[1] = ""
    offline_msg[str(20167)] = group_msg[str(20167)]=""
    offline_msg[str(20168)] = group_msg[str(20168)] = ""
    offline_msg[str(20169)] = group_msg[str(20169)] = ""



if __name__ == "__main__":
    main()