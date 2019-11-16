''' Cache pdbparse-generated global symbol maps from pdb files
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

# Cache global symbol map given pdb id, requires pdbparse
import pdbcache
import pdbparse

from pdbparse.pe import Sections
from pdbparse.omap import Omap

class DummyOmap(object):
    def remap(self, addr):
        return addr

def parse_pdb_file(fname, verbose=False):
    pdb = pdbparse.parse(fname)
    try:
        sects = pdb.STREAM_SECT_HDR_ORIG.sections
        omap = pdb.STREAM_OMAP_FROM_SRC
        if verbose:
            print ' [+] Using old section header with Omap'
    except AttributeError as e:
        sects = pdb.STREAM_SECT_HDR.sections
        omap = DummyOmap()
        if verbose:
            print ' [+] Using new section header and dummy Omap'

    if verbose:
        print ' [+] Read %d sections' % len(sects)

    gsyms = {}
    for sym in pdb.STREAM_GSYM.globals:
        try:
            off = sym.offset
            base = sects[sym.segment - 1].VirtualAddress
#            sec_name = sects[sym.segment - 1].Name.split('\0')[0]
            gsyms[sym.name.encode('latin-1')] = omap.remap(off + base)
        except IndexError as e:
            if verbose:
                print ' [-] Skipping %s: missing section %d' % (sym.name, sym.segment - 1)
        except AttributeError as e:
            pass
    return gsyms

CACHE = {}

def get_gsyms(pdb_id):
    global CACHE
    if pdb_id in CACHE:
        return CACHE[pdb_id]
    pdb_file = pdbcache.get_pdb_file(pdb_id)
    if pdb_file is None:
        return None
    gsyms = parse_pdb_file(pdb_file)
    if gsyms != None:
        CACHE[pdb_id] = gsyms
    return gsyms

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print 'Usage: symcache.py <pdb filename>'
        sys.exit(1)

    gsyms = parse_pdb_file(sys.argv[1], True)

