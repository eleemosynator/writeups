/* 
 *  dpapi_test.cpp :- Test the three types of CryptProtectMemory encryption
 *                    Run and cause a crash-dump with NotMyFault to test
 *  Copyright (C) 2019 eleemosynator
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 *
 */

// Compile with: cl /Ox /EHs dpapi_test.cpp crypt32.lib

#include <windows.h>
#include <cstdlib>
#include <iostream>
#include <string>

char message[] = "16bytemagictagXXThis is a 32 bytes message blockThis is a 32 bytes message blockThis is a 32 bytes message block"
                 "8 bytes!8 bytes!8 bytes!";

int main(int argc, char *argv[])
{
	for (int i = 0; i < 3; ++i) {
		CryptProtectMemory(message + 16 + i * 32, 32, i);
		CryptProtectMemory(message + 16 + 3 * 32 + i * 8, 8, i);
	}

	std::string ans;
	std::cin >> ans;
}
