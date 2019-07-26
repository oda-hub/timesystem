#!flask/bin/python
from flask import Flask, url_for, jsonify, send_file, request

import requests

import os
import sys
import copy
import pilton
import re
import logging

import socket

def dlog(*a, **aa):
    pass

consul=False

context=socket.gethostname()

app = Flask(__name__)

def converttime_rbp(rbp_var_suffix,informat,intime,outformat):
    ct=pilton.heatool("converttime")
    ct['informat']=informat
    ct['intime']=intime
    ct['outformat']=outformat

    env = copy.deepcopy(os.environ)
    env['REP_BASE_PROD'] = env['REP_BASE_PROD_'+rbp_var_suffix] 

    ct.run(env=env)

    return ct.output if hasattr(ct,'output') else None

@app.route('/api/v1.0/converttime/<string:informat>/<string:intime>/<string:outformat>', methods=['GET'])
def converttime(informat,intime,outformat):
    if outformat=="ANY":
        outformat=""


    problems = []
    output = None
    for rbp_var_suffix in "NRT", "CONS":
        try:
            output = converttime_rbp(rbp_var_suffix,informat,intime,outformat)
            r=dict(re.findall("Log_1  : Input Time\(.*?\): .*? Output Time\((.*?)\): (.*?)\n",output,re.S))

            print(r)

            if outformat=="":
                return jsonify(r)
            else:
                return r[outformat]

        except Exception as e:
            p = {'error from converttime':repr(e),'output':output }
            print("problem:", p)
    
            problems.append(p)

    r = jsonify(problems)

    r.status_code=500
    dlog(logging.ERROR,"error in converttime "+repr(e))
    return r


@app.route('/poke', methods=['GET'])
def poke():
    return ""

if __name__ == '__main__':

    if consul:
        import os
        from export_service import export_service,pick_port
        os.environ['EXPORT_SERVICE_PORT']="%i"%pick_port("")
        port=export_service("integral-timesystem","/poke",interval=0.1,timeout=0.2)

        host=os.environ['EXPORT_SERVICE_HOST'] if 'EXPORT_SERVICE_HOST' in os.environ else '127.0.0.1'
    else:
        host="0.0.0.0"
        port=5000
        
    ##
    app.run(debug=False,port=port,host=host)
