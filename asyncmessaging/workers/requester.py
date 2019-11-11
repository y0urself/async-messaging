# -*- coding: utf-8 -*-

from celery import Celery
#from gvm.protocols.gmp import Gmp as gmp

app = Celery('requester', backend='rpc://', broker='pyamqp://guest@localhost//')

@app.task
def xml_request(cmd : str):
    print(cmd)  

