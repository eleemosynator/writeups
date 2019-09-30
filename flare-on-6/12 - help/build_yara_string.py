''' IDA script for building Yara rules out of functions
    Copyright (C) 2016-2019 eleemosynator

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

import idaapi
import os

class YaraBuffer(object):
    def __init__(self):
        self.data = []

    def ship(self, ea_start, ea_end):
        try:
            self.data.append(' '.join(['%02x' % Byte(ea) for ea in range(ea_start, ea_end) ]))
        except Exception as e:
            print 'failed: %06x -- %06x' % (ea_start, ea_end)
            raise e

    def shipq(self, n):
        self.data.append(' ??' * n)

    def get_string(self):
        return ' '.join(self.data)

# Extract current function as generalized yara rule

def build_yara_string():
    ea = GetFunctionAttr(ScreenEA(), FUNCATTR_START)
    if ea == BADADDR:
        print 'Failed to determine function start'
        return
    y = YaraBuffer()
    is_64bit = idaapi.get_inf_structure().is_64bit()
    nq = 0
    for rip in Heads(*Chunks(ea).next()):
        rip_next = NextHead(rip)
        if rip_next - rip <= 4:     # Anything smaller than DWord has no relation
            y.ship(rip, rip_next)
            continue
        # both 32-bit and 64-bit mode have 32bit near jumps
        # (far jumps & far calls are tacitly ignored here)
        if GetMnem(rip) == 'call' and GetOpType(rip, 0) != o_reg:
            y.ship(rip, rip_next - 4)
            y.shipq(4)
            continue
        # 32bit and 64-bit cases are somewhat different
        insn = DecodeInstruction(rip)
        if is_64bit:
            if insn.Op2.type == o_void:
                # Single operand
                if insn.Op1.type == o_mem:
                    y.ship(rip, rip_next - 4)
                    y.shipq(4)
                else:
                    y.ship(rip, rip_next)
            else:
                # Two opearands
                if insn.Op1.type == o_mem:
                    # rip relative Op1
                    y.ship(rip, rip + insn.Op1.offb)
                    y.shipq(rip_next - rip - insn.Op1.offb)
                else:
                    if (insn.Op2.type == o_imm and insn.Op2.dtyp == idaapi.dt_qword
                                               and rip_next - rip - insn.Op2.offb == 8
                                               and insn.Op2.value >= MinEA()
                                               and insn.Op2.value < MaxEA()):
                        y.ship(rip, rip_next - 8)
                        y.shipq(8)
                    else:
                        y.ship(rip, rip_next)
        else:
            # 32bit heuristic treatment
            t = Dword(rip_next - 4)
            if GetMnem(rip) == 'call' or (t >= MinEA() and t < MaxEA()):
                y.ship(rip, rip_next - 4)
                y.shipq(4)
                nq += 4
            else:
                y.ship(rip, rip_next)
    return y.get_string()

