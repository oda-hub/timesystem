import pytest
import time



def test_normtime():
    from timesystem import time2ijd

    print(time2ijd(1000))
    print(time2ijd(1000.))
    print(time2ijd("1000"))
    print(time2ijd("60000."))
    print(time2ijd("2015-01-01T11:11:11"))
    
    
def test_timeformat():
    from timesystem import detect_timeformat

    print(detect_timeformat(1000))
    print(detect_timeformat(1000.))
    print(detect_timeformat("1000"))
    print(detect_timeformat("60000."))
    print(detect_timeformat("2015-01-01T11:11:11"))
    
    
