import pilton
import re

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

    if outformat=="":
        return r
    else:
        r[outformat]



