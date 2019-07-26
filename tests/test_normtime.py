import pytest
import time



def test_normtime():
    from timesystem import normalize_time

    print(normalize_time(1000))
    print(normalize_time(1000.))
    print(normalize_time("1000"))
    print(normalize_time("60000."))
    print(normalize_time("2015-01-01T11:11:11"))
    
    
