#!flask/bin/python
from flask import Flask, url_for, jsonify, send_file, request

import requests

import os
import sys
import glob
import time

import copy
import re
import logging
import socket
import traceback

import pilton

from astropy.table import Table
from astropy.io import fits
from astropy.time import Time


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
            print("convertime completed")

            r=dict(re.findall("Log_1  : Input Time\(.*?\): .*? Output Time\((.*?)\): (.*?)\n",output,re.S))

            print("extracted", r)

            if outformat=="":
                return jsonify(r)
            else:
                if 'is close' in r[outformat]:
                    raise Exception("conversion impossible: "+repr(r))

                return r[outformat]

        except Exception as e:
            p = {'error from converttime':repr(e),'output':output, 'traceback':traceback.format_exc()}
            print("problem:", p)
    
            problems.append(p)

    r = jsonify(problems)

    r.status_code=500
    dlog(logging.ERROR,"error in converttime "+repr(problems))
    return r


class SCWIDX:
    def __init__(self):
        self.cache = {}

    def index(self, rbp, version=None):
        k = (rbp, version)
        if k in self.cache and self.cache[k]['expires_at'] > time.time():
            print("found cached",k)
            return self.cache[k]

        if version is None:
            fn_p = rbp+"/idx/scw/GNRL-SCWG-GRP-IDX_*"
            fn = sorted(glob.glob(fn_p))[-1]

            version = re.search("GNRL-SCWG-GRP-IDX_(.*?).fits.*", os.path.basename(fn)).groups()[0]

            expires_at = time.time() + 3600
        else:
            fn = rbp+"/idx/scw/GNRL-SCWG-GRP-IDX_"+version

            expires_at = time.time() + 24*3600*7

        print("picking", fn, version, expires_at)

        r = dict(
                    table = Table.read(fits.open(fn)[1]), 
                    table_version = version, 
                    expires_at = expires_at,
                )

        self.cache[k] = r

        return r
    
    def nrt(self, version=None):
        return self.index(os.environ.get('REP_BASE_PROD_NRT'))
    
    def cons(self, version=None):
        return self.index(os.environ.get('REP_BASE_PROD_CONS'))


scwidx = SCWIDX()

def time2ijd(t):
    try:
        t=float(t)

        if t < 10000: # IJD
            return t
        else:
            return t - 51544.0 # MJD
    except:
        return Time(t).mjd - 51544.0

def lastscw_rbp(rbp_var_suffix):
    rbp_var = "REP_BASE_PROD_"+rbp_var_suffix
    rbp = os.environ.get(rbp_var)

    print("rbp_var, rbp", rbp_var, rbp)
    idx = scwidx.index(rbp)
    return idx['SWID'][-1]


def scwlist_rbp(rbp_var_suffix, t1: float, t2: float):
    rbp_var = "REP_BASE_PROD_"+rbp_var_suffix
    rbp = os.environ.get(rbp_var)

    print("rbp_var, rbp", rbp_var, rbp)
    idx = scwidx.index(rbp)

    m = idx['table']['TSTART'] < t2
    m &= idx['table']['TSTOP'] > t1

    return list(idx['table']['SWID'][m])

@app.route('/api/v1.0/scwlist/<string:readiness>/<string:t1>/<string:t2>', methods=['GET'])
def scwlist(readiness,t1,t2):
    problems = []
    output = None

    if readiness.lower() == "any":
        rbp_var_suffixes = ["NRT", "CONS"]
    elif readiness.lower() == "nrt":
        rbp_var_suffixes = ["NRT", ]
    elif readiness.lower() == "cons":
        rbp_var_suffixes = ["CONS", ]
    else:
        r = jsonify({'bad request:','readiness undefined'})
        r.status_code=400
        return r

    t1_ijd = time2ijd(t1)
    t2_ijd = time2ijd(t2)

    for rbp_var_suffix in rbp_var_suffixes:
        try:
            output = scwlist_rbp(rbp_var_suffix, t1_ijd, t2_ijd)


            if 'debug' in request.args:
                return jsonify(dict(
                                    output=output,
                                    t1_ijd=t1_ijd,
                                    t2_ijd=t2_ijd,
                                    readiness=rbp_var_suffix,
                                    lastscw=lastscw_rbp(rbp_var_suffix),
                                ))
            else:
                return jsonify(output)

        except Exception as e:
            p = {'error from scwlist_rbp':repr(e),'output':output, 'traceback':traceback.format_exc() } # sentry!!
            print("problem:", p)
    
            problems.append(p)

    r = jsonify(problems)

    r.status_code=500
    dlog(logging.ERROR,"error in converttime "+repr(problems))

    # return index version, last scw

    if 'debug' in request.args:
        return r
    else:
        return r


@app.route('/test', methods=['GET'])
def test():
    pass

@app.route('/', methods=['GET'])
@app.route('/poke', methods=['GET'])
def poke():
    return "all is ok"

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
