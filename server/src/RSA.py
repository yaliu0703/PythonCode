# -*- coding: utf-8 -*-
import rsa
message = "hello"
# 先生成一对密钥,
(pubkey, privkey) = rsa.newkeys(1024)

pubn = str(pubkey.n)
pube = str(pubkey.e)
pubk = rsa.PublicKey(long(pubn), int(pube)) #从字符串转回公钥钥

privn = str(privkey.n)
prive = str(privkey.e)
privd = str(privkey.d)
privp = str(privkey.p)
privq = str(privkey.q)
privk = rsa.PrivateKey(long(privn), int(prive), long(privd), long(privp), long(privq)) #从字符串转回私钥
print "myprik:"
print privk

crypto = rsa.encrypt(message, pubk)
message = rsa.decrypt(crypto, privk)
if privkey==privk:print "ok"
print message

"""
pub = pubkey.save_pkcs1()
pubfile = open('public.pem','w+')
pubfile.write(pub)
pubfile.close()

pri = privkey.save_pkcs1()
prifile = open('private.pem','w+')
prifile.write(pri)
prifile.close()

# load公钥和密钥
message = 'hello'
with open('public.pem') as publickfile:
    p = publickfile.read()
    pubkey = rsa.PublicKey.load_pkcs1(p)

with open('private.pem') as privatefile:
    p = privatefile.read()
    privkey = rsa.PrivateKey.load_pkcs1(p)"""
