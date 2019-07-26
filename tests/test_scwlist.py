import pytest
import time
from flask import url_for



def test_scwlist(client):
    t0=time.time()
    r=client.get(url_for('scwlist', readiness="unset", t1='2019-06-10T11:27:45',t2='2019-06-10T11:27:45'))
    print(r)
    assert r.status_code == 400
    
def test_scwlist(client):
    t0=time.time()
    r=client.get(url_for('scwlist', readiness="any", t1='2019-06-10T11:27:45',t2='2019-06-10T11:27:45'))
    print(r)
    assert r.status_code == 200
    print(r.json)
    

    t0=time.time()
    print("repeating request")
    r=client.get(url_for('scwlist', readiness="any", t1='2019-06-10T11:27:45',t2='2019-06-10T11:27:45'))
    print(r)
    assert r.status_code == 200
    print(r.json)

    assert (time.time() - t0)<1
    
