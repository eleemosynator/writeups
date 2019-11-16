''' Simple command line tool for fetch pdb files of a given executable into
    the symbol cache. Uses symcache, pdbcache, pdbtool, pdbparse and pefile
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
import pdbcache
import pdbtool
import symcache
import sys
import pefile

class PeReader(object):
    def __init__(self, fname):
        self.pe = pefile.PE(fname)
        self.img = self.pe.get_memory_mapped_image()

    def read(self, addr, size):
        return self.img[addr:addr+size]

for fn in sys.argv[1:]:
    print fn
    vm = PeReader(fn)
    pdb_tag = pdbtool.get_pdb_id(vm, 0)
    print fn, pdb_tag
    symcache.get_gsyms(pdb_tag)


