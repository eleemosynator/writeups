''' Scan Kernel Pool allocations for specific pattern
    (badly named, need to rename)
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
# Scan Kernel Pool allocations for specific pattern
import volatility.obj as obj
import volatility.poolscan as poolscan

def bugread(vm, offset, size, z=False):
    extra = offset & 0xfff
    offset &= ~0xfff
    size += extra
    method = vm.zread if z else vm.read
    data = method(offset, size)
    if data is None:
        return None
    return data[extra:]

def run(addrspace, tag, pattern, paged=True, non_paged=True):
    pool_block_size = obj.VolMagic(addrspace).PoolAlignment.v()
    scanner = poolscan.SinglePoolScanner()
#    scanner.checks = [  ]
    scanner.checks = [ ('CheckPoolType', dict(paged = paged, non_paged = non_paged)) ]
    if not tag is None and len(tag) > 0:
        scanner.checks.append(('PoolTagCheck', dict(tag = tag)))
    for offset in scanner.scan(addrspace):
        pool_header = obj.Object("_POOL_HEADER", offset = offset, vm = addrspace)
        block_size = pool_header.BlockSize.v() * pool_block_size
        data_size = block_size - pool_header.struct_size
        data = bugread(addrspace, offset + pool_header.struct_size, data_size, z=True)
#        print 'offset: %016x, type: %d, data: %d, read: %d' % (offset, pool_header.PoolType.v(), data_size, len(data))
        pos = data.find(pattern)
        if pos >= 0:
            print '0x%016x %s type: %d, size: %d @ 0x%02x + 0x%03x' % (offset, tag, pool_header.PoolType.v(), block_size, pool_header.struct_size, pos)


