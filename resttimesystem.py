#!flask/bin/python
from flask import Flask, url_for, jsonify, send_file, request
import pylru

import requests

import sys
import pilton
import re

from dlogging import logging
from dlogging import log as dlog

import socket

context=socket.gethostname()

app = Flask(__name__)

@app.route('/integral-timesystem/api/v1.0/<string:informat>/<string:intime>/<string:outformat>', methods=['GET'])
def converttime(informat,intime,outformat):
    if outformat=="ANY":
        outformat=""

    ct=pilton.heatool("converttime")
    ct['informat']=informat
    ct['intime']=intime
    ct['outformat']=outformat

    try:
        ct.run()
    except Exception as e:
        print "problem:",e
        r=jsonify({'error from converttime':repr(e),'output':ct.output})
        r.status_code=400
        dlog(logging.ERROR,"error in converttime "+repr(e))
        return r

    r=dict(re.findall("Log_1  : Input Time\(.*?\): .*? Output Time\((.*?)\): (.*?)\n",ct.output,re.S))

    print r

    if outformat=="":
        return jsonify(r)
    else:
        return r[outformat]

@app.route('/poke', methods=['GET'])
def poke():
    return ""

if __name__ == '__main__':
    port=7543

    import os
    os.environ['EXPORT_SERVICE_PORT']="%i"%port
    try:
        from export_service import export_service
        port=export_service("integral-timesystem","/poke",interval=0.1,timeout=0.2)
    except:
        raise
    
    ##
    app.run(debug=False,port=port)
