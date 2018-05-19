import os
import sys

if __name__ == '__main__':
    hdr = '03f30d0a00000000'.decode('hex')
    assert len(hdr) == 8
    for fn in sys.argv[1:]:
        with open(fn, 'rb') as f:
            data = f.read()
            f.close()
        if data[:4] == hdr[:4]:
            print 'Skipping ' + fn
            continue
        with open(fn, 'wb') as f:
            f.write(hdr + data)
            f.close()

