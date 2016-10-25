#!flask/bin/python
from flask import Flask, url_for, jsonify, send_file, request
import pylru

import requests

import sys
import pilton
import re


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

    r=dict(re.findall("Log_1  : Input Time\(.*?\): .*? Output Time\((.*?)\): (.*?)\n",ct.output,re.S))

    print r

    if outformat=="":
        return jsonify(r)
    else:
        return r[outformat]

if __name__ == '__main__':
    port=7543

    try:
        from export_service import export_service
        port=export_service("integral-timesystem","/integral-timesystem/api/v1.0/IJD/3000/SCWID")
    except:
        raise
    
    ##
    app.run(debug=False,port=port)
