''' Label the imports for the image of man.sys
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
VA_ILT = 0xE028
VA_IAT = 0x6000

def count_qwords(ea):
    k = 0
    while True:
        if Qword(ea) == 0:
            break
        k += 1
        ea += 8
    return k

def read_string(va):
    out = []
    while Byte(va) != 0:
        out.append(chr(Byte(va)))
        va += 1
    return ''.join(out)

def tag_imports():
    ilt = VA_ILT
    iat = VA_IAT
    while Qword(ilt) != 0:
        imp = read_string(Qword(ilt) + 2)
        MakeName(iat, imp)
        iat += 8
        ilt += 8



# print map(count_qwords, [ VA_ILT, VA_IAT ])
tag_imports()

