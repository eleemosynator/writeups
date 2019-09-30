''' Decrypt stack strings for man.sys and friends
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
import sys
sys.path.append('../tools')
sys.path.append('../../tools')
import emu_helper
from Crypto.Cipher import ARC4
from unicorn.x86_const import *
import re

#VA_decrypt = idaapi.get_imagebase() + 0x1150

def is_unicode(s):
    return (len(s) & 1) == 0 and max(map(ord, s[1::2])) == 0

def is_printable(s):
    return all(map(lambda x: x >= 32 and x <= 126, map(ord, s)))

def make_printable(s):
    if is_unicode(s) and is_printable(s.decode('utf-16le')):
        return 'u"' + s.decode('utf-16le').encode('latin-1') + '"'
    elif is_printable(s):
        return 'a"' + s + '"'
    else:
        return 'b"' + s.encode('hex') + '"'

def get_ascii(s):
    if is_unicode(s):
        s = s.decode('utf-16le').encode('latin-1')
    if is_printable(s):
        return s
    else:
        return None

def is_symbol(s):
    s = get_ascii(s)
    if s is None:
        return False
    r_symbol = re.compile('^[\w\d_]+$')
    if r_symbol.match(s) is None:
        return False
    else:
        return True

def make_symbol(s):
    asc = get_ascii(s)
    if asc is None:
        return 'hex_' + s.encode('hex')
    else:
        s = asc
    if is_symbol(s):
        return s
    # force into symbol
    sym, _ = re.compile('[^\w\d_]').subn('_', s)
    return sym

# delete consecutive vars in stack
def delete_stack_vars(frame_id, v_start, v_len):
    to_del = []
    for offset, name, size in StructMembers(frame_id):
        if offset >= v_start and offset < v_start + v_len:
            to_del.append(offset)
    for offset in to_del:
        DelStrucMember(frame_id, offset)

# Mark the stack variables for the decrypted string
def mark_stack_vars(log, va_call, ptext, name_len, key_len):
    b_unicode = is_unicode(ptext)
    key_var = None
    name_var = None
    va = va_call
    for i in xrange(4):
        va = PrevHead(va)
        if GetMnem(va) != 'lea':
            continue
        if GetOpType(va, 0) != o_reg or GetOpType(va, 1) != o_displ:
            log("%06x: failed to parse key / stack address" % va)
            return
        reg = idaapi.get_reg_name(GetOperandValue(va, 0), 8)
        if reg == 'rcx':
            # key
            key_var = GetOperandValue(va, 1)
        elif reg == 'r8':
            name_var = GetOperandValue(va, 1)
        else:
            log("%06x: failed to parse register for key / stack address" % va)
            return
    frame_id = GetFrame(va_call)
    if not (key_var is None):
        SetMemberName(frame_id, key_var, 'key_%06x' % va_call)
        delete_stack_vars(frame_id, key_var + 1, key_len - 1)
        SetMemberType(frame_id, key_var, GetMemberFlag(frame_id, key_var), -1, key_len)
    if not (name_var is None):
        prefix = 'wsz_' if b_unicode else 'sz_'
        SetMemberName(frame_id, name_var, prefix + make_symbol(ptext))
        delete_stack_vars(frame_id, name_var + 1, name_len - 1)
        SetMemberType(frame_id, name_var, GetMemberFlag(frame_id, name_var), -1, name_len)


# va is address of the call to the decryption function
def decrypt_string(log, emu, va_call):
    # move back four instructions which must all be lea
    va = va_call
    for i in xrange(4):
        va = PrevHead(va)
        if GetMnem(va) not in 'leamov':
            log('unexpected menmonic at %04x: %s' % (va, GetMnem(va)))
            return
    # va now points to first instruction after stack setup
    maxdelta = 0
    k = 0
    while True:
        va = PrevHead(va)
        if GetMnem(va) != 'mov':
            break
        if GetOpType(va, 1) != o_imm:
            break
        if GetOpType(va, 0) != o_displ:
            break
        if 'rsp' not in GetDisasm(va):
            break
        insn = DecodeInstruction(va)
        # specflag1 == 1, specflag2 == 36 (index == base == 4: esp)
        # op.reg should also be 4, op.addr is the delta
        maxdelta = max(maxdelta, insn.Op1.addr)
        k += 1
    va = NextHead(va)
    # We don't really need to emulate, but hey
    maxdelta += 32
    log('xref at: %04x: %d stack bytes at delta %04x' % (va_call, k, maxdelta))
    if k == 0:
        log('ABORTING XREF AT %04x' % va_call)
        return
    emu.init_stack(maxdelta)
    rsp = emu.mu.reg_read(UC_X86_REG_RSP)
    emu.mu.mem_write(rsp, '\0' * maxdelta)
    emu.mu.emu_start(va, va_call)
    key_len = emu.mu.reg_read(UC_X86_REG_RDX) & 0xffffffff
    key = str(emu.mu.mem_read(emu.mu.reg_read(UC_X86_REG_RCX), key_len))
    ctext_len = emu.mu.reg_read(UC_X86_REG_R9) & 0xffffffff
    ctext = str(emu.mu.mem_read(emu.mu.reg_read(UC_X86_REG_R8), ctext_len))
    log('ctext: ' + ctext.encode('hex') + ', key: ' + key.encode('hex'))
    ptext = ARC4.new(key).decrypt(ctext)
    pcc = make_printable(ptext)
    log('decode: ' + pcc)
    MakeComm(va_call, pcc)
    mark_stack_vars(log, va_call, ptext, ctext_len, key_len)

def log_message(log, message):
    print message
    log.write(message + '\n')

def strip_extension(fn):
    n = fn.find('.')    # should do rfind
    if n > 0:
        return fn[:n]
    else:
        return fn

def decrypt_strings(VA_decrypt):
    log = open(strip_extension(GetInputFile()) + '_strings.log', 'at')
    emu = emu_helper.Emu()
    hdr = open(input_filename, 'rb').read(2)
    if hdr == 'MZ':
#        print 'Loading PE image'
        emu.init_pe(input_filename)
    else:
#        print 'Loading raw binary image'
        if idaapi.get_inf_structure().is_64bit():
            bits = 64
        else:
            bits = 32
        emu.init_binary_pe(GetInputFile(), idaapi.get_imagebase(), bits)
    for xr in XrefsTo(VA_decrypt):
        if GetMnem(xr.frm) != 'call':
            continue
        decrypt_string(lambda x:log_message(log, x), emu, xr.frm)
    log.close()

# yara hex strings

class YaraString(object):
    def __init__(self, name, yara_string):
        self.name = name
        self.yara_string = yara_string.translate(None, ' \t\r\n')   # delete blanks
        if len(self.yara_string) & 1:
            raise Exception("Invalid yara string (odd length): " + self.yara_string)
        self.length = len(self.yara_string) >> 1
        # parse the string
        self.parsed = []
        last = 0
        while True:
            n = self.yara_string.find('?', last)
            if n < 0:
                self.parsed.append((last >> 1, self.yara_string[last:].decode('hex')))
                break
            if self.yara_string[n + 1] != '?':
                raise Exception("Single nibble wildcards not supported")
            if n > last:
                self.parsed.append((last >> 1, self.yara_string[last:n].decode('hex')))
            last = n + 2

    def check_function(self, ea):
        l, r = Chunks(ea).next()
#        print '%06x: %06x -- %06x, %d, %d' % (ea, l, r, r - l, self.length)
        if r - l < self.length:
            return False
#        print 'check(%06x)' % ea
        for offset, data in self.parsed:
            if idaapi.get_many_bytes(l + offset, len(data)) != data:
#                print 'Failed: %06x [ %d ]' % (offset, len(data))
                return False
#        print 'found!'
        return True

    # Find Function by yara string
    # returns list of matches
    def find_functions(self):
        matches = []
        for func in Functions(Segments().next()):
            if self.check_function(func):
                matches.append(func)
        return matches

    def find_single_function(self):
        matches = self.find_functions()
        if len(matches) != 1:
            raise Exception("Failed to find " + self.name)
        return matches[0]

    def find_first_function(self):
        matches = self.find_functions()
        if len(matches) < 1:
            raise Exception("Failed to find " + self.name)
        return matches[0]

# set the names of functions called by another function in given order
def set_names(va, names):
    n = 0
    for rip in Heads(*Chunks(va).next()):
        if GetMnem(rip) != 'call':
            continue
        if n >= len(names):
            continue
        if names[n] != '':
            MakeNameEx(GetOperandValue(rip, 0), names[n], 0)
        n += 1

def set_rc4_crypt_names(va):
    MakeNameEx(va, "rc4_crypt", 0)
    set_names(va, [ 'rc4ctx_setkey', 'rc4ctx_crypt' ])
#    n = 0
#    for rip in Heads(*Chunks(va)):
#        if GetMnem(rip) != 'call':
#            continue
#        if n == 0:
#            name = 'rc4ctx_setkey'
#        else:
#            name = 'rc4ctx_crypt'
#        MakeNameEx(GetOperandValue(rip, 0), name, idaapi.SN_FORCE)
#        m += 1

# Yara pattern for the rc4_crypt() function
yara_rc4_crypt = YaraString('rc4_crypt', '44 89 4c 24 20 4c 89 44 24 18 89 54 24 10 48 89 4c 24 08 57 48 81 ec 30 01 00 00 c6 44 24 20 00 48 8d 7c 24 21 33 c0 b9 ff 00 00 00 f3 aa 48 8d bc 24 20 01 00 00 33 c0 b9 02 00 00 00 f3 aa 44 8b 84 24 48 01 00 00 48 8b 94 24 40 01 00 00 48 8d 4c 24 20 e8  ?? ?? ?? ?? 44 8b 8c 24 58 01 00 00 4c 8b 84 24 50 01 00 00 48 8b 94 24 50 01 00 00 48 8d 4c 24 20 e8  ?? ?? ?? ?? 48 81 c4 30 01 00 00 5f c3')

def find_and_decrypt():
    # Find rc4_crypt with yara-like rules
    VA_rc4_crypt = yara_rc4_crypt.find_first_function()
    set_rc4_crypt_names(VA_rc4_crypt)
    decrypt_strings(VA_rc4_crypt)


find_and_decrypt()

