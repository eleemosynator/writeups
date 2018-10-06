''' fetch level2 payload

    Requires unpacked challenge files (another) and dependencies in the same
    directory.

    Copyright (C) 2018 eleemosynator

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
import another

PIN = 9667
filename = 'level2_payload.dll'

# wrap another.fetch_url() so that we can print the url before it's fetched

fetch_url_original = another.fetch_url
def fetch2(x):
    print 'url: ' + x
    return fetch_url_original(x)
another.fetch_url = fetch2


def main():
    key = another.get_url_key(PIN)
    data = another.decode_and_fetch_url(key)
    print 'fetched', len(data), 'bytes'
    decdata = another.get_encoded_data(data)
    with open(filename, 'wb') as f:
        f.write(decdata)
        f.close()
    print 'payload', len(decdata), 'bytes written to', filename

if __name__ == '__main__':
    main()
