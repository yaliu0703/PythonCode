# -*- coding: UTF-8 -*-
"""
生成xml文件 函数genxml(p_id)，保存id,certificate,privkey,pubkey
"""
from xml.dom.minidom import Document

import rsa,re

"""
(pubkey,privkey)=rsa.newkeys(1024);
pubkey=''.join(re.findall(r'(\w*[0-9]+)\w*',str(pubkey)))
privkey=''.join(re.findall(r'(\w*[0-9]+)\w*',str(privkey)))
p_id='1010' #id值改变
"""
def genxml(p_id,privkey,pubkey):

	#创建DOM文档对象

	doc = Document()  

	cert = doc.createElement('cert')
	doc.appendChild(cert)

	#创建元素id
	pid = doc.createElement('id') 
	id_text = doc.createTextNode(p_id)
	pid.appendChild(id_text)
	cert.appendChild(pid)

	#创建元素privkey
	private = doc.createElement('privkey')
	private_text=doc.createTextNode(privkey)
	private.appendChild(private_text)
	cert.appendChild(private)

	#创建元素privkey
	public = doc.createElement('pubkey')
	public_text=doc.createTextNode(pubkey)
	public.appendChild(public_text)
	cert.appendChild(public)

	filename = p_id + '.xml'
	f = open(filename, 'w')
	f.write(doc.toprettyxml(indent = ''))
	f.close()