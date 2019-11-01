# -*- coding: UTF-8 -*-
"""
解析xml文件函数 pub,pri=certhandler() 返回值pub为公钥，pri为私钥
""" 

import xml.sax,os
global p_id
class certHandler( xml.sax.ContentHandler ):
  def __init__(self):
    self.CurrentData = ""
    self.id= ""
    self.privkey = ""
    self.pubkey = ""

    # 元素开始事件处理
  def startElement(self, tag, attributes):
    self.CurrentData = tag
    if tag == "cert":
      print("******************certificate*****************")
   # 元素结束事件处理
  def endElement(self, tag):
    if self.CurrentData == "id":
      print( "id:", self.id)

    elif self.CurrentData == "privkey":
      print( "privkey:", self.privkey)
      with open("myprivkey.pem", "w") as f:             #私钥在本地保存为myprivkey.pem
        myprivkey = self.privkey
        f.write(myprivkey)
    elif self.CurrentData == "pubkey":
      print( "pubkey:", self.pubkey)
      with open("mypubkey.pem", "w") as f:             #公钥在本地保存为mypubkey.pem
        mypubkey = self.pubkey
        f.write(mypubkey)
    self.CurrentData = ""
    return self.id,self.privkey,self.pubkey
      # 内容事件处理
  def characters(self, content):
    if self.CurrentData == "id":
      self.id = content
    elif self.CurrentData == "privkey":
      self.privkey = content
    elif self.CurrentData == "pubkey":
      self.pubkey = content
    return self.id,self.privkey,self.pubkey

def certhandler():
  p_id = "20165"
  # 创建一个 XMLReader
  parser = xml.sax.make_parser()
  # turn off namepsaces
  parser.setFeature(xml.sax.handler.feature_namespaces, 0)
  # 重写 ContextHandler
  Handler = certHandler()
  parser.setContentHandler( Handler )
  filename=p_id+".xml"
  parser.parse(filename)
  with open('mypubkey.pem') as publickfile:
    pub = publickfile.read()
  os.remove('mypubkey.pem')
  with open('myprivkey.pem') as privatefile:
    pri = privatefile.read()
  os.remove('myprivkey.pem')
  print pub
  #return pub,pri

certhandler()