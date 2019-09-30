''' volatility addin - find and dump contents of i8042prt.sys keyboard buffer
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
# volatility addin - find and dump contents of i8042prt.sys keyboard buffer
import volatility.obj as obj
import volatility.poolscan as poolscan
import volatility.plugins.filescan as filescan
import struct
import parse_keyboard_buffer

# find i8042prt Driver structure
def find_i8042prt(addrspace):
    # Do a pool scan
    for drv in poolscan.MultiScanInterface(addr_space=addrspace,
                                           scanners=[filescan.PoolScanDriver],
                                           scan_virtual=True).scan():
        if 'i8042prt' in drv.DriverName.v():
            return drv
    return None

# A KeyboardClass device must be attached to the unnamed device that is the main i8042prt keyboard device
def find_keyboard_device(drv):
    for device in drv.devices():
        for att_device in device.attached_devices():
            # Alternatively can check the driver name of the attached device is kbd something
            device_header = obj.Object("_OBJECT_HEADER", offset = att_device.obj_offset -
                att_device.obj_vm.profile.get_obj_offset("_OBJECT_HEADER", "Body"),
                vm = att_device.obj_vm,
                native_vm = att_device.obj_native_vm
                )
            att_name = str(device_header.NameInfo.Name or '')
            if 'Keyboard' in att_name:
                return device
    return None

# Unpack array into words / dwords / qwords

def unpack_array(data, dsize=4, signed=False, endianess='<'):
    sizemap = { 1:'b', 2:'h', 4:'l', 8:'q' }
    if dsize not in sizemap:
        raise Exception('Invalid data size %d passed to unpack_array()' % dsize)
    dtype = sizemap[dsize]
    if not signed:
        dtype = dtype.upper()
    trimmed = len(data) - (len(data) % dsize)
    return list(struct.unpack(endianess + dtype * (trimmed / dsize), data))

# find i8042 kbd quuee
# search for a dara structture of the form
# DQ ptr_block_start
# DQ ptr_in_block
# DQ ptr_in_block
# DQ ptr_block_end
# in the DeviceExtension part of the keyboard device
# where ptr_block_end - ptr_block_start is divisible by 12 and equal
# to another dword field in DeviceExtension
def find_kbd_queue(addrspace):
    drv = find_i8042prt(addrspace)
    if drv is None:
        print ' [-] Failed to locate i8042prt driver'
        return None
    print ' [+] i8042prt driver object at 0x%016x: %s' % (drv.v(), drv.DriverName.v())
    dev = find_keyboard_device(drv)
    if dev is None:
        print ' [-] Failed to locate keyboard device'
        return None
    print ' [+] i8042prt keyboard device object at 0x%016x' % dev.v()
    ext = addrspace.read(dev.DeviceExtension.v(), dev.Size.v() - dev.struct_size)
    print ' [+] extension at 0x%016x size 0x%03x' % (dev.DeviceExtension.v(), len(ext))
    # find candidates for the buffer size
    pool_alignment = obj.VolMagic(addrspace).PoolAlignment.v()
    allsizes = set(filter(lambda x: x > 12 * 4 and (x % 12) == 0 and x <= 12000, unpack_array(ext, dsize=4)))
    for i in xrange(0, len(ext) - 3 * 8, 8):
        ptr, ptr_read, ptr_write, ptr_end = struct.unpack('<QQQQ', ext[i:i+4*8])
        if ptr == 0 or (ptr % pool_alignment) != 0:
            continue
        if ptr_read < ptr or ptr_read > ptr_end:
            continue
        if ptr_write < ptr or ptr_write > ptr_end:
            continue
        if (ptr_read - ptr) % 12 != 0:
            continue
        if (ptr_write - ptr) % 12 != 0:
            continue
        if (ptr_end - ptr) not in allsizes:
            continue
        # candidate
        print ' [+] candidate buffer ptr: 0x%016x from ext+0x%04x' % (ptr, i)
        # load the block header
        hdr = addrspace.read(ptr - pool_alignment, pool_alignment)
        if hdr is None:
            print ' [-] failed to read block header for 0x%016x' % ptr
            continue
        pool_hdr = obj.Object("_POOL_HEADER", offset=ptr-pool_alignment, vm=addrspace)
        if pool_hdr is None:
            print ' [-] failed to read block header for 0x%016x' % ptr
            continue
        if struct.pack('<L', pool_hdr.PoolTag.v()) != '8042':
            print ' [-] block at 0x%016x has incorrect tag: 0x%08x' % (ptr, pool_hdr.PoolTag.v())
            continue

        # this must be it! work out the delta in the buffer and retun it
        data = addrspace.read(ptr, ptr_end - ptr)
        if data is None:
            print ' [-] failed to read keyboard buffer at 0x%016x from ext+0x%04x' % (ptr, i)
            return None
        delta = ptr_write - ptr
        return data[delta:] + data[:delta]
    return None

def run(addrspace):
    buf = find_kbd_queue(addrspace)
    if not buf is None:
        parsed = parse_keyboard_buffer.parse_buffer(buf)
        print ' [+] %d characters parsed' % len(parsed)
        print ' [+] keystrokes: ' + ''.join(parsed)

