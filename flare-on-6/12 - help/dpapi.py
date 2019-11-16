''' Voltility script that decrypts blobs encrypted with DAPI CryptProtectMemory
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

# Volatility script
# Decrypt DPAPI-protected memory
import volatility.win32 as win32
import volatility.obj as obj

from Crypto.Cipher import AES
from Crypto.Cipher import DES3
import hashlib
import pdbtool
import symcache
import struct

# Enables debugging messages

DEBUG = False

# We only need code_parser for Windows 10 (cng.sys doesn't export RandomSalt)

HAVE_CODE_PARSER = False

try:
    import code_parser
    HAVE_CODE_PARSER = True
except:
    if DEBUG:
        print ' [-] Neither distorm3 nor capstone are available - disabling code parsing'

# CryptProtectMemory dwFlags values
CRYPTPROTECTMEMORY_SAME_PROCESS = 0
CRYPTPROTECTMEMORY_CROSS_PROCESS = 1
CRYPTPROTECTMEMORY_SAME_LOGON = 2

# Shorthand
SAME_PROCESS = 0
CROSS_PROCESS = 1
SAME_LOGON = 2

CNG_BASE = None

def get_cng_base(vm):
    global CNG_BASE
    if CNG_BASE is None:
        # Find cng.sys
        for mod in win32.modules.lsmod(vm):
            if mod.BaseDllName.v().lower() == 'cng.sys':
                CNG_BASE = mod.DllBase.v()
                break
    return CNG_BASE

def get_gsyms(vm, base, verbose=False):
    pdb_id = pdbtool.get_pdb_id(vm, base)
    if verbose:
        print ' [+] identified cng.sys debug symbols: %s.%s' % pdb_id
    gsyms = symcache.get_gsyms(pdb_id)
    if verbose:
        if gsyms is None:
            print ' [-] failed to load cng.sys symbol file'
        else:
            print ' [+] loaded %d symbols from symbol file' % len(gsyms)
    return gsyms

# keys lifted from cng.sys module
CNG_KEYS = None

# Key identifiers
# The CngEncryptMemoryInitialize generates two sets of random numbers
#  - the first set of 0x18 is fed into g_ShaHash which is used to generate both AES and 3DES 
#    keys. In addition, the 3DES global key is the same 0x18 bytes
#  - the second set of 0x10 is def into g_AESHash which is never used, however the same 0x10
#    bytes are used as the AES global key
#
# key generation for AES is:
#  aes_key = SHA1(g_ShaHash_contents || additional_key_data)
#  des3_key = SHa1(g_ShaHash_contents || 'aaa' || additional_key_data) || SHA1(g_ShaHash_contents || 'bbb' || additional_key_data)
CNG_KEY_MAP_WIN7 = {
    'GLOBAL_SHA1_CTX':  ('?g_ShaHash@@3UA_SHA_CTX@@A', 0x60),
    'AES_GLOBAL_SHA1_CTX': ('?g_AESHash@@3UA_SHA_CTX@@A', 0x60),
#    'AES_IV': ('?RandomSalt@@3PAEA', 16),
#    '3DES_IV': ('?RandomSalt@@3PAEA', 8),
    'AES_GLOBAL_KEY_SCHEDULE': ('?g_AESKey@@3UAESTable_128@@A', 0x164),
    '3DES_GLOBAL_KEY_SCHEDULE': ('?g_DES3Key@@3U_DES3TABLE@@A', 0x180) # Global 3DES key comes from AES SHA1 context
    }

# Symbols name for win10 versions of cng.sys
CNG_KEY_MAP_WIN10 = {
    'GLOBAL_SHA1_CTX':  ('?g_ShaHash@@3U_SYMCRYPT_SHA1_STATE@@A', 0x80),
    'AES_GLOBAL_SHA1_CTX': ('?g_AESHash@@3U_SYMCRYPT_SHA1_STATE@@A', 0x80),
# In Windoes 10 the IV (RandomSalt) does not have a debug symbol name
# we need to find it by disassembling CngEncryptMemoryInitialize
#    'AES_IV': ('?RandomSalt@@3PAEA', 16),
#    '3DES_IV': ('?RandomSalt@@3PAEA', 8),
    'AES_GLOBAL_KEY_SCHEDULE': ('?g_AESKey@@3U_SYMCRYPT_AES_EXPANDED_KEY@@A', 0x1F0),
    '3DES_GLOBAL_KEY_SCHEDULE': ('?g_DES3Key@@3U_SYMCRYPT_3DES_EXPANDED_KEY@@A', 0x1F0) # Global 3DES key comes from AES SHA1 context
    }

# details of the AES Key Schedule and SHA1 Context structures in Win7 and Win10
# for the SHA1 context structure we need to know the locations of the hash state,
# the inner buffer and the total size of data sent to the hash
# For the AES Key schedule we only need the location of the first sub-key
# which is identical to the full AES key
CNG_STRUCTURES = {
    7: {
        'SHA1': {
            'buffer':0,
            'size':0x58,
            'state':0x40
            },
        'AES': {
            'key':4         # dword dwNumRounds followed by schedule, first round key is the real key
            }
        },
    10: {
        'SHA1': {
            'buffer':0x20,
            'size':0x00,
            'state':0x60
            },
        'AES': {
            'key':0         # For Win10 there is no initial num rounds DWORD
            }
        }
    }


# Extract  the location of the IV by disassembling CngEncryptInitialize
#  and looking for rip-relative writes to memory
def get_cng_iv_addr_disasm(vm, cng_base, gsyms, verbose=False):
    if DEBUG:
        verbose = True
    fn_name = 'CngEncryptMemoryInitialize'
    if not fn_name in gsyms:
        if verbose:
            print ' [-] failed to find "%s" in cng.sys symbols - cannot extract IV'
        return None

    fn_addr = gsyms[fn_name]
    fn_body = vm.read(cng_base + fn_addr, 0x400)
    if fn_body is None:
        if verbose:
            print ' [-] failed to read "%s" body from RVA 0x%06x in cng.sys' % (fn_name, fn_addr)
        return None
    if verbose:
        print ' [+] %s at 0x%0x6 in cng.sys' % (fn_name, fn_addr)
    if not HAVE_CODE_PARSER:
        if verbose:
            print ' [-] Cannot extract IV location from cng.sys: Neither distorm3 nor capstone are installed'
        return None
    writes = code_parser.find_rip_relative_writes(fn_addr, fn_body)
    if len(writes) == 0:
        if verbose:
            print ' [-] Failed to find any rip-relative writes in "%s" in cng.sys' % fn_name
        return None
    # the IV is 16 byte total write to a rip-relative location
    iv_list = filter(lambda z: z[1] == 16, writes)
    if len(iv_list) != 1:
        if verbose:
            print ' [-] rip-relative write scanner returned %d 16-bytes writes, cannot locate IV' % len(iv_list)
        return None
    iv_rva = iv_list[0][0]
    if verbose:
        print ' [+] IV at rva 0x%06x: 0x%016x' % (iv_rva, cng_base + iv_rva)
    return cng_base + iv_rva

# get IV address either using 'RandomSalt' symbol or through disassembly
def get_cng_iv_addr(vm, cng_base, gsyms, verbose=False):
    if DEBUG:
        verbose = True
    random_salt_sym = '?RandomSalt@@3PAEA'
    if random_salt_sym in gsyms:
        if verbose:
            print ' [+] getting IV from RandomSalt symbol'
        return cng_base + gsyms[random_salt_sym]
    else:
        if verbose:
            print ' [+] getting IV from CngEncryptMemoryInitialize disassembly'
        return get_cng_iv_addr_disasm(vm, cng_base, gsyms, verbose)

# Chcek if all key map symbols are in the symbols registry
def gsyms_contains_key_map(gsyms, key_map):
    return all(map(lambda x: x[0] in gsyms, key_map.itervalues()))

# Read data blocks from loaded image using a symbol map
# symbol_map has the format: identifier => (symbol_name, data_size)
def read_data_with_symbol_map(vm, img_base, gsyms, symbol_map, verbose=False):
    data_map = {}
    for k, v in symbol_map.iteritems():
        if not v[0] in gsyms:
            if verbose:
                print ' [-] failed to find symbold %s in image' % v[0]
            return None
        offset = img_base + gsyms[v[0]]
        data = vm.read(offset, v[1])
        if data is None:
            if verbose:
                print ' [-] failed to read %d bytes from %s in image at 0x%016x' % (v[1], v[0], offset)
            return None
        data_map[k] = data
    return data_map

def get_cng_keys(vm, verbose=True):
    global CNG_KEYS, CNG_KEY_MAP_WIN7, CNG_KEY_MAP_WIN10
    if not CNG_KEYS is None:
        return CNG_KEYS
    cng_base = get_cng_base(vm)
    if cng_base is None:
        if verbose:
            print ' [-] Failed to get base address of cng.sys'
        return None
    if verbose:
        print ' [+] cng.sys located at 0x%016x' % cng_base
    gsyms = get_gsyms(vm, cng_base, verbose)
    if gsyms is None:
        return None
    if gsyms_contains_key_map(gsyms, CNG_KEY_MAP_WIN7):
        winver = 7
        symbol_map = CNG_KEY_MAP_WIN7
        if verbose:
            print ' [+] Windows 7 symbols matched'
    elif gsyms_contains_key_map(gsyms, CNG_KEY_MAP_WIN10):
        winver = 10
        symbol_map = CNG_KEY_MAP_WIN10
        if verbose:
            print ' [+] Windows 10 symbols matched'
    else:
        print ' [-] could not find either Win7 or Win10 key names in cng.sys symbols'
        return None

    keys = read_data_with_symbol_map(vm, cng_base, gsyms, symbol_map, verbose)
    if keys is None:
        return None
    if verbose:
        print ' [+] extracted keys from cng.sys'
    # In Windows 10 there is no explicit symbol name for the IV, so we have to
    # diassemble CngEncryptMemoryInitialize. We can generalie this approach
    # and just fall back to disassembly whenever the RandomSalt symbol is missing
    iv_addr = get_cng_iv_addr(vm, cng_base, gsyms, verbose)
    if iv_addr is None:
        return
    iv = vm.read(iv_addr, 16)
    if iv is None:
        if verbose:
            print ' [-] failed to read cng.sys IV from 0x%016x' % iv_addr
        return None
    keys['AES_IV'] = iv
    keys['3DES_IV'] = iv[:8]
    # Derive the SHA1 seed by parsing the SHA1 ctx
    sha1_seed = parse_sha1_ctx(keys['GLOBAL_SHA1_CTX'], winver)
    if sha1_seed is None:
        if verbose:
            print ' [-] failed to extract sha1 seed from the global sha1 context'
        return None
    keys['SHA1_SEED'] = sha1_seed       # This is also the global 3DES key
    keys['3DES_GLOBAL_KEY'] = sha1_seed
    keys['AES_GLOBAL_SHA1_SEED'] = parse_sha1_ctx(keys['AES_GLOBAL_SHA1_CTX'], winver)  # this should be the same as AES_GLOBAL_KEY
    keys['AES_GLOBAL_KEY'] = parse_aes_schedule(keys['AES_GLOBAL_KEY_SCHEDULE'], winver)  
    if verbose:
        print ' [+] extracted %d byte sha1 seed from cng' % len(sha1_seed)
    if False:
        for k, v in keys.iteritems():
            if 'SCHEDULE' in k or 'CTX' in k:
                continue
            print ' [+] %-22s %s' % (k + ':', v.encode('hex'))
    CNG_KEYS = keys
    if DEBUG:
        import pickle
        _, pdb_id = pdbtool.get_pdb_id(vm, cng_base)
        pickle.dump(keys, open('cng_keys_%s.pickle' % pdb_id, 'wb'))
    return CNG_KEYS

# Parse a cng SHA1_CTX structure to get the SHA1 seed
def parse_sha1_ctx(ctx, winver):
    if not (winver in CNG_STRUCTURES):
        raise Exception('Unsupported Windows version: %d' % winver)
    ofs = CNG_STRUCTURES[winver]['SHA1']
    ofs_state = ofs['state']
    ofs_buffer = ofs['buffer']
    ofs_size = ofs['size']
    # sha1 state is at offset 0x40 for win7 and is 20 bytes long
    sha1_state = ctx[ofs_state:ofs_state + 0x14]
    # Check sha1_ctx is still in initial state (i.e. no Sha1Transform yet)
    if sha1_state != struct.pack('<LLLLL', 0x67452301, 0x0EFCDAB89, 0x98BADCFE, 0x10325476, 0x0C3D2E1F0):
        return None
    seed_size = struct.unpack('<L', ctx[ofs_size:ofs_size+4])[0]
    return ctx[ofs_buffer:ofs_buffer+seed_size]

# Extract the key from the AES key schedule
# The raw AES key is xor'ed into the plaintext at the start of the first round, i.e. it is
# the very first (of 11 for AES128) subkeys
def parse_aes_schedule(ks, winver):
    if not (winver in CNG_STRUCTURES):
        raise Exception('Unsupported Windows version: %d' % winver)
    ofs_key = CNG_STRUCTURES[winver]['AES']['key']
    return ks[ofs_key:ofs_key+0x10]

# Handle process list caching
PSLIST_CACHE = None

def get_pslist(vm):
    return { proc.UniqueProcessId.v(): proc for proc in win32.tasks.pslist(vm) }

def lookup_pid(vm, pid):
    global PSLIST_CACHE
    if PSLIST_CACHE is None:
        PSLIST_CACHE = get_pslist(vm)
    if pid in PSLIST_CACHE:
        return PSLIST_CACHE[pid]
    else:
        return None


# Core UnprotectMemory() functoinality
def unprotect_memory_blob(vm, pid, data, dwFlags, verbose=True):
    if (len(data) & 0x0f) != 0:
        if (len(data) & 0x07) != 0:
            print ' [-] Data size [0x%03x] must be a multiple of 8' % len(data)
            return None
#        print ' [-] dpapi.unprotect_memory() only supports AES-encrypted blobs - size must be multiple of 16'
        cipher = DES3
        cipher_name = '3DES'
    else:
        cipher = AES
        cipher_name = 'AES'

    keys = None
    try:
        keys = get_cng_keys(vm, verbose)
    except Exception as e:
        print ' [-] Failed to extract keys from cng.sys: ' + e.message
    if keys is None:
        return None
    iv = keys[cipher_name + '_IV']
    if dwFlags == CROSS_PROCESS:
        # We don't need to dereference pid for this
        cipher_key = keys[cipher_name + '_GLOBAL_KEY']
    else:
        proc = lookup_pid(vm, pid)
        if proc is None:
            print ' [-] failed to lookup process %d' % pid
            return None
        if dwFlags == SAME_PROCESS:
            key_data = struct.pack('<LQ', proc.Cookie, proc.CreateTime.as_windows_timestamp())
        elif dwFlags == SAME_LOGON:
            token = proc.Token.dereference_as("_TOKEN")
#            print 'token at: ' + hex(token.obj_offset)
            if token.__class__ is obj.NoneObject:
                print ' [-] failed to dereference Token for pid %d' % pid
                return None
            key_data = struct.pack('<LL', token.AuthenticationId.LowPart.v(), token.AuthenticationId.HighPart.v())
            if verbose:
                print ' [+] authenticationId: 0x%08x%08x' % (token.AuthenticationId.HighPart.v(), token.AuthenticationId.LowPart.v())
        else:
            print ' [-] Invalid dwFlags value: %d' % dwFlags
            return None
#        print 'seed: ' + keys['AES_SHA1_SEED'].encode('hex')
#        print 'key_data: ' + key_data.encode('hex')
        # key generation is slightly different between AES and 3DES
        seed = keys['SHA1_SEED']
        if cipher_name == '3DES':
            cipher_key = (hashlib.sha1(seed + 'aaa' + key_data).digest() + hashlib.sha1(seed + 'bbb' + key_data).digest())[:0x18]
        else:
            cipher_key = hashlib.sha1(seed + key_data).digest()[:16]
    return cipher.new(cipher_key, mode=cipher.MODE_CBC, IV=iv).decrypt(data)

def unprotect_memory(vm, pid, offset, size, dwFlags=SAME_PROCESS, verbose=True):
    proc = lookup_pid(vm, pid)
    if proc is None:
        print ' [-] failed to lookup pid %d' % pid
        return None
    else:
        procname = proc.ImageFileName.v()
        procname = procname[:(procname + '\0').find('\0')]
        if verbose:
            print ' [+] pid %d %s -> 0x%016x' % (pid, procname, proc.v())
    data = proc.get_process_address_space().read(offset, size)
    if data is None:
        print ' [-] failed to read %d bytes from offset 0x%016x in %d %s' % (size, offset, pid, procname)
        return None
    return unprotect_memory_blob(vm, pid, data, dwFlags, verbose)


