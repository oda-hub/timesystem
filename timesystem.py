#!flask/bin/python
from flask import Flask, url_for, jsonify, send_file, request

import requests

import os
import sys
import glob
import time

from typing import TypeVar, Iterable, Tuple, Union, List

import copy
import re
import logging
import socket
import traceback

import pilton  # type: ignore

from astropy.table import Table  # type: ignore
from astropy.io import fits  # type: ignore
from astropy.time import Time  # type: ignore
from astropy.coordinates import SkyCoord  # type: ignore


def dlog(*a, **aa):
    pass


consul = False

context = socket.gethostname()

app = Flask(__name__)


class UserException(Exception):
    pass


@app.errorhandler(UserException)
def user_exception(e):
    return jsonify({'error': str(e)})


def converttime_rbp(rbp_var_suffix, informat, intime, outformat):
    ct = pilton.heatool("converttime")

    ct['informat'] = informat
    ct['intime'] = intime
    ct['outformat'] = outformat

    env = copy.deepcopy(os.environ)
    env['REP_BASE_PROD'] = env['REP_BASE_PROD_'+rbp_var_suffix]

    ct.run(env=env)

    return ct.output if hasattr(ct, 'output') else None


def detect_timeformat(t):
    try:
        t = float(t)
        if t > 20000:
            return 'MJD'
        else:
            return 'IJD'
    except:
        pass

    try:
        if Time(t).format == "isot":
            return "UTC"
    except Exception as e:
        raise UserException("unknown time format: %s" % repr(e))


@app.route('/api/v1.0/converttime/<string:informat>/<string:intime>/<string:outformat>', methods=['GET'])
def converttime(informat, intime, outformat):
    if outformat == "ANY":
        outformat = ""

    if informat == "ANY":
        informat = detect_timeformat(intime)

    problems = []
    output = None
    for rbp_var_suffix in "NRT", "CONS":
        try:
            output = converttime_rbp(
                rbp_var_suffix, informat, intime, outformat)
            print("convertime completed")

            r = dict(re.findall(
                "Log_1  : Input Time\(.*?\): .*? Output Time\((.*?)\): (.*?)\n", output, re.S))

            print("extracted", r)

            if outformat == "":
                return jsonify(r)
            else:
                if 'is close' in r[outformat]:
                    raise UserException("conversion impossible: "+repr(r))

                return r[outformat]

        except UserException as e:
            p = {'problem': str(e)}
            print("problem:", p)

            problems.append(p)

        except Exception as e:
            p = {'error from converttime': repr(
                e), 'output': output, 'traceback': traceback.format_exc()}
            print("problem:", p)

            problems.append(p)

    r = jsonify(problems)

    r.status_code = 400
    dlog(logging.ERROR, "error in converttime "+repr(problems))
    return r


class SCWIDX:
    def __init__(self):
        self.cache = {}

    def latest_version(self, rbp):
        fn_p = rbp+"/idx/scw/GNRL-SCWG-GRP-IDX_*"

        print("searching for", fn_p)

        fns = glob.glob(fn_p)

        if len(fns) == 0:
            raise UserException("no indices here "+fn_p)

        fn = sorted(fns)[-1]

        version = re.search("GNRL-SCWG-GRP-IDX_(.*?).fits.*",
                            os.path.basename(fn)).groups()[0]

        return version, fn

    def index(self, rbp, version=None):
        k = (rbp, version)
        if k in self.cache and self.cache[k]['expires_at'] > time.time():
            print("found cached", k)
            return self.cache[k]

        if version is None:
            version, fn = self.latest_version(rbp)

            if 'nrt' in rbp:
                expires_at = time.time() + 600
            else:
                expires_at = time.time() + 7200
        else:
            fn_p = rbp+"/idx/scw/GNRL-SCWG-GRP-IDX_"+version+"*"
            fns = glob.glob(fn_p)

            if len(fns) == 0:

                all_fns = glob.glob(rbp+"/idx/scw/GNRL-SCWG-GRP-IDX_*")
                versions = sorted([re.search(
                    "GNRL-SCWG-GRP-IDX_([0-9]+)\..*?", fn.split("/")[-1]).groups()[0] for fn in all_fns])

                if int(version) < int(versions[0]):
                    return self.index(rbp, versions[0])
                else:
                    versions_summary = "%s - %s" % (versions[0], versions[-1])

                    raise UserException("no index with requested version: %s; have: %s" % (
                        version, versions_summary))

            if len(fns) > 1:
                raise UserException(
                    "ambigious index with requested version: %s" % version)

            fn = fns[0]

            expires_at = time.time() + 24*3600*7

        print("picking", fn, version, expires_at)

        r = dict(
            table=Table.read(fits.open(fn)[1]),
            table_version=version,
            expires_at=expires_at,
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
        t = float(t)

        if t < 10000:  # IJD
            return t
        else:
            return t - 51544.0  # MJD
    except:
        return Time(t).mjd - 51544.0


def lastscw_rbp(rbp_var_suffix):
    rbp_var = "REP_BASE_PROD_"+rbp_var_suffix
    rbp = os.environ.get(rbp_var)

    print("rbp_var, rbp", rbp_var, rbp)
    idx = scwidx.index(rbp)
    return str(idx['table']['SWID'][-1])


def scwlist_rbp(rbp_var_suffix,
                index_version: str,
                t1: float,
                t2: float,
                ra: Union[float, None],
                dec: Union[float, None],
                radius: Union[float, None],
                min_good_isgri: Union[float, None],
                return_columns: Union[str, None],
                ):
    rbp_var = "REP_BASE_PROD_"+rbp_var_suffix
    rbp = os.environ.get(rbp_var)

    print("rbp_var, rbp", rbp_var, rbp)
    idx = scwidx.index(rbp, version=index_version)

    m = idx['table']['TSTART'] < t2
    m &= idx['table']['TSTOP'] > t1

    if ra is not None and dec is not None and radius is not None:
        c = SkyCoord(idx['table']['RA_SCX'], idx['table']
                     ['DEC_SCX'], unit="deg")
        m &= c.separation(SkyCoord(ra, dec, unit="deg")).degree < radius

    if min_good_isgri is not None:
        m &= idx['table']['TELAPSE'] > min_good_isgri
        m &= idx['table']['IBISMODE'] == 41

    if return_columns is None:
        return_columns = "SWID"

    r = {}
    for c in return_columns.split(","):
        if c in idx['table'].columns:
            r[c] = idx['table'][c][m].tolist()
        else:
            m = "undefined column name %s, have: %s" % (
                c, ", ".join(idx['table'].columns))
            print(c, m)
            raise UserException(m)

    return r


@app.route('/api/v1.0/scwlist/<string:readiness>/<string:t1>/<string:t2>', methods=['GET'])
def scwlist(readiness, t1, t2):
    problems = []

    ra = request.args.get("ra", default=None, type=float)
    dec = request.args.get("dec", default=None, type=float)
    radius = request.args.get("radius", default=None, type=float)
    min_good_isgri = request.args.get(
        "min_good_isgri", default=None, type=float)
    return_columns = request.args.get("return_columns", default=None, type=str)

    if readiness.lower() == "any":
        rbp_var_suffixes = ["NRT", "CONS"]
    elif readiness.lower() == "nrt":
        rbp_var_suffixes = ["NRT", ]
    elif readiness.lower() == "cons":
        rbp_var_suffixes = ["CONS", ]
    else:
        r = jsonify({'bad request': 'readiness undefined'})
        r.status_code = 400
        return r

    index_version = request.args.get('index_version', None)

    if len(rbp_var_suffixes) == 1:
        if index_version is None:
            rbp_var = "REP_BASE_PROD_"+rbp_var_suffixes[0]
            rbp = os.environ.get(rbp_var)

            index_version, fn = scwidx.latest_version(rbp)
        else:
            if not re.match("\d+", index_version):
                r = jsonify({'bad request': "non-conforming index version"})
                r.status_code = 400
                return r
    else:
        if index_version is not None:
            r = jsonify(
                {'bad request': "index version can only be set with \"cons\" or \"nrt\" source, not \"any\""})
            r.status_code = 400
            return r

    try:
        t1_ijd = time2ijd(t1)
        t2_ijd = time2ijd(t2)
    except ValueError as e:
        r = jsonify({'bad request': 'failed to interpret time: '+repr(e)})
        r.status_code = 400
        return r

    output = {}

    for rbp_var_suffix in rbp_var_suffixes:
        try:
            for k, v in scwlist_rbp(rbp_var_suffix, index_version, t1_ijd, t2_ijd, ra, dec, radius, min_good_isgri, return_columns=return_columns).items():
                if k not in output:
                    output[k] = []

                output[k] += v

        except UserException as e:
            p = {'problem in '+rbp_var_suffix: str(e)}
            print("problem:", p)

            problems.append(p)

        except Exception as e:
            p = {'error from scwlist_rbp': repr(
                e), 'output': output, 'traceback': traceback.format_exc()}  # sentry!!
            print("problem:", p)

            problems.append(p)

    if problems == []:
        if return_columns is None:
            output = sorted(set(output['SWID']))

        if 'debug' in request.args:
            return jsonify(dict(
                output=output,
                t1_ijd=t1_ijd,
                t2_ijd=t2_ijd,
                readiness=rbp_var_suffix,
                lastscw=lastscw_rbp(rbp_var_suffix),
                index_version=index_version,
            ))
        else:
            if request.args.get('return_index_version', 'no') == "yes":
                return jsonify(dict(scwlist=output, index_version=index_version))
            else:
                return jsonify(output)

    r = jsonify(problems)

    r.status_code = 400
    dlog(logging.ERROR, "error in converttime "+repr(problems))

    # return index version, last scw

    if 'debug' in request.args:
        return r
    else:
        return r


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    r = {}

    t = time.time()
    r['nrev_cons'] = len(glob.glob(os.path.join(
        os.environ.get("REP_BASE_PROD_CONS"), "scw/*")))
    r['tspent_cons'] = time.time() - t

    t = time.time()
    r['nrev_idx_cons'] = len(glob.glob(os.path.join(
        os.environ.get("REP_BASE_PROD_CONS"), "idx/scw/*")))
    r['tspent_idx_cons'] = time.time() - t

    t = time.time()
    r['nrev_nrt'] = len(glob.glob(os.path.join(
        os.environ.get("REP_BASE_PROD_NRT"), "scw/*")))
    r['tspent_nrt'] = time.time() - t
    
    t = time.time()
    r['nrev_idx_nrt'] = len(glob.glob(os.path.join(
        os.environ.get("REP_BASE_PROD_NRT"), "idx/scw/*")))
    r['tspent_idx_nrt'] = time.time() - t

    if r['nrev_idx_cons'] > 0 and r['nrev_idx_nrt'] > 0 and r['nrev_cons'] > 10 and r['nrev_nrt'] > 10:
        return jsonify({'status': 'OK', **r}), 200
    else:
        return jsonify({'status': 'NOK', **r}), 400


@app.route('/test', methods=['GET'])
def test():
    import subprocess
    c = subprocess.check_output(
        ["python", "-m", "pytest", "-sv", "/timesystem/tests"])
    return c


@app.route('/', methods=['GET'])
@app.route('/poke', methods=['GET'])
def poke():
    return "all is ok"


if __name__ == '__main__':
    host = "0.0.0.0"
    port = 5000

    app.run(debug=False, port=port, host=host)
