''' Simple cache manager for pdb files downloaded from symbol server
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
# Manage cached pdb files, download any missing
import os
import sys

# PDB cache location is configured through PDB_CACHE environment var
PDB_CACHE_CONFIG_NAME = 'PDB_CACHE'

# WinDbg cache location
WINDBG_CACHE_DIR = 'c:/ProgramData/dbg/sym'

PDB_CACHE_DIR = None

def check_assign_pdb_cache(dirname):
    global PDB_CACHE_DIR
    if dirname is None or dirname == '':
        return False
#    print 'check: ' + dirname
    if not os.path.isdir(dirname):
        try:
            os.mkdir(dirname)
        except Exception as e:
            print ' [-] WARNING: Cannot create pdb cache dir ' + dirname + ' : ' + e.strerror
            return False
    # check we can write
    try:
        test_fname = os.path.join(dirname, 'write_test.out')
        with open(test_fname, 'wt') as fout:
            fout.write('EOF\n\x1a')
            fout.close()
        os.unlink(test_fname)
    except Exception as e:
        print ' [-] WARNING: Cannot write to pdb cache ' + dirname + ' : ' + e.strerror
        return False
#    print 'assigned: ' + dirname
    PDB_CACHE_DIR = dirname
    return True

def get_pdb_cache_dir():
    global PDB_CACHE_DIR
    if PDB_CACHE_DIR is None:
        if PDB_CACHE_CONFIG_NAME in os.environ:
            if check_assign_pdb_cache(os.environ[PDB_CACHE_CONFIG]):
                return PDB_CACHE_DIR
        if check_assign_pdb_cache(WINDBG_CACHE_DIR):
            return PDB_CACHE_DIR
        if check_assign_pdb_cache('./.pdbcache'):
            return PDB_CACHE_DIR
    return PDB_CACHE_DIR

# Initialize PDB_CACHE_DIR
get_pdb_cache_dir()
print ' [+] pdb cache at ', PDB_CACHE_DIR

# Downloading logic shamelessly stolen from symchk.py in pdbparse package

SYM_URL = 'http://msdl.microsoft.com/download/symbols'
USER_AGENT = "Microsoft-Symbol-Server/6.11.0001.404"

import requests
import shutil

def download_pdb_file(fname_dst, url):
    with requests.get(url, headers={'User-Agent': USER_AGENT}, stream=True, allow_redirects=True) as fin:
        with open(fname_dst, 'wb') as fout:
            shutil.copyfileobj(fin.raw, fout)

def ensure_dir_exists(dirname):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

# All pdb files are accessed using pdb_id: (pdb_name, guid_string)
# Returns full path and filename of downloaded file or None

def get_pdb_file(pdb_id):
    global PDB_CACHE_DIR
    fname = '/{0}/{1}/{0}'.format(*pdb_id)
    if os.path.isfile(WINDBG_CACHE_DIR + fname):
        return WINDBG_CACHE_DIR + fname
    if os.path.isfile(PDB_CACHE_DIR + fname):
        return PDB_CACHE_DIR + fname
    # Download
    ensure_dir_exists(PDB_CACHE_DIR + '/{0}'.format(*pdb_id))
    ensure_dir_exists(PDB_CACHE_DIR + '/{0}/{1}'.format(*pdb_id))
    download_pdb_file(PDB_CACHE_DIR + fname, SYM_URL + fname)
    return PDB_CACHE_DIR + fname

def main():
    if len(sys.argv) != 3:
        print 'Usage: pdbcache <pdb_name> <guid_id>'
        sys.exit(1)
    get_pdb_file(sys.argv[1:])

if __name__ == '__main__':
    main()

