''' Brute-guess the password to the KeePass database
    Copyright (C) 2019 eleemosynator

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import libkeepass
import itertools
import time

def try_open_db(db, key):
    try:
        return libkeepass.open(db, password=key)
    except IOError as e:
        if 'Master key invalid' in e.message:
            return None
        else:
            raise IOError(e.message)

DB = 'traffic/file-01639.bin'
KEY_TEMPLATE = 'th1s_is_th3_3nd'
KEY_SUFFIX = '!!!'

total_tries = 0

# recursively try all combinations of k shifted letters
# starting at position m
def recurse_keys(key, k, m):
    global total_tries
    if k == 0 or m >= len(key):
        # No more things to try
        dbkey = str(key) + KEY_SUFFIX
        print dbkey
        total_tries += 1
        db = try_open_db(DB, dbkey)
        if db is not None:
            print 'WIN!!!'
#            print db.pretty_print()
            print '%d total tries' % total_tries
            return True
        else:
            return False
    else:
        # iterate over locations of next shifted char
        for l in xrange(m, len(key)):
            # We're not shifting '_' or '3'
            if chr(key[l]) in '_3':
                continue
            if chr(key[l]) == '1':
                key[l] = ord('!')
                if recurse_keys(key, k - 1, l + 1):
                    return True
                key[l] = ord('1')
            else:
                key[l] = ord(chr(key[l]).upper())
                if recurse_keys(key, k - 1, l + 1):
                    return True
                key[l] = ord(chr(key[l]).lower())
    return False

def brute_key():
    for k in xrange(len(KEY_TEMPLATE) - 5):
        if recurse_keys(bytearray(KEY_TEMPLATE), k, 0):
            break

if __name__ == '__main__':
    t0 = time.clock()
    brute_key()
    print 'bruted in %.2fs' % (time.clock() - t0)
