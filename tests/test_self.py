import pytest
import time
from flask import url_for



def test_utc2ijd(client):
    t0=time.time()
    print("repeating request")
    r=client.get(url_for('converttime',informat="UTC",intime='2019-06-10T11:27:45',outformat="IJD"))

    print(r)

    assert r.status_code == 200
    print(r.json)

    assert (time.time() - t0)<1
    
