import pilton
import re

try:
    import fermi,integral
except:
    pass


def converttime(informat,intime,outformat):
    if outformat=="ANY":
        outformat=""

    if informat=="SCWID":
        datamirror.ensure_data(scw=intime)

    ct=pilton.heatool("converttime")
    ct['informat']=informat
    ct['intime']=intime
    ct['outformat']=outformat

    try:
        ct.run()
    except Exception as e:
        print "problem:",e
        r=jsonify({'error from converttime':repr(e),'output':ct.output if hasattr(ct,'output') else None})

        if outformat=="SCWID":
            try:
                c=isdclient.getscw(intime)
            except Exception as ei:
                r=jsonify({'error from converttime':repr(e),'output':ct.output,'error from ISDC':repr(ei),'ISDC response':c})

        r.status_code=500
        dlog(logging.ERROR,"error in converttime "+repr(e))
        return r

    r=dict(re.findall("Log_1  : Input Time\(.*?\): .*? Output Time\((.*?)\): (.*?)\n",ct.output,re.S))

    print r

    if outformat=="":
        return jsonify(r)
    else:
        return r[outformat]




def x2ijd(x,rbp=None):
    if isinstance(x,float) or  isinstance(x,int):
        print "float must be IJD: IJD found!"

        if float(x)>10000.:
            print "too big for IJD - must be fermis"
            return fermi.fermis2ijd(float(x))
        return x

    if not isinstance(x,str):
        print "should be float or string"
        return

    if re.match("^\d*.\d*$",x) or re.match("^\d*$",x):
        print "IJD found!",x
        return float(x)

    if re.match("\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.?\d*",x):
        print "UTC found!"
        return integral.utc2ijd(x,rbp=rbp)

    print "can not interpret time:",x

    return None

def x2fermis(x):
    return fermi.ijd2fermis(x2ijd(x))
