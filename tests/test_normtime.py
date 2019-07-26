import pytest
import time



def test_normtime():
    from timesystem import time2ijd

    print(time2ijd(1000))
    print(time2ijd(1000.))
    print(time2ijd("1000"))
    print(time2ijd("60000."))
    print(time2ijd("2015-01-01T11:11:11"))
    
    
