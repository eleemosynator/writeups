''' Extract simple scancode map from current Windows keyboard setup
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
# extract scancode map for given keyboard

import win32con
import win32api
import json

MAPVK_VK_TO_VSC = 0
MAPVK_VSC_TO_VK = 1
MAPVK_VK_TO_CHAR = 2
MAPVK_VSC_TO_VK_EX = 3

# Shorthand
def vk2vsc(vk):
    return win32api.MapVirtualKey(vk, MAPVK_VK_TO_VSC)

def vsc2vk(vsc):
    return win32api.MapVirtualKey(vsc, MAPVK_VSC_TO_VK)

# build scan and shifted-scan map mapping scaancode -> character
scans = {}
shifted_scans = {}
# We only care about printable characters
for k in xrange(0x20, 0x7f):
    vk = win32api.VkKeyScan(chr(k))     # Char->VK using current layout
    if vk & ~0x1ff:
        continue
    if vk & 0x100:
        # shifted
        shifted_scans[vk2vsc(vk & 0xff)] = chr(k)
    else:
        scans[vk2vsc(vk)] = chr(k)

# add symbolic keys
for vn in filter(lambda x: x.startswith('VK_'), dir(win32con)):
    vk = getattr(win32con, vn)
    scan = vk2vsc(vk)
    if not scan in scans:
        scans[scan] = '<' + vn[3:] + '>'

# shifts is a map of the three shift types to a list of left and right scancodes
shifts = {}
for name, vk_name in zip([ 'shift', 'ctrl', 'alt' ], [ 'SHIFT', 'CONTROL', 'MENU' ]):
    shifts[name] = [ vk2vsc(getattr(win32con, 'VK_' + side + vk_name)) for side in 'LR' ]

scancode_map = dict(scans=scans, shifted_scans=shifted_scans, shifts=shifts)
with open('scancode_map.json', 'wt') as fout:
    json.dump(scancode_map, fout)

