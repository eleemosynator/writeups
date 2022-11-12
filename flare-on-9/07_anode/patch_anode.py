import os
import sys
import struct
from unnexe import find_nexe_resource

# replace js code in anode.exe

FNAME = 'anode.exe'

def main():
	data = bytearray(open(FNAME, 'rb').read())
	js_ofs, js_sz = find_nexe_resource(data, FNAME)
#	js_ofs = 56506374
#	js_sz  = 321847

	if len(sys.argv) < 2:
		print('{os.path.basename(sys.argv[0])} requires at least one argument')
		sys.exit(1)

	tag = sys.argv[1]
	if tag.endswith('.js'):
		tag = tag[:-3]

	newjs = open(f'{tag}.js', 'rb').read()
	if len(newjs) > js_sz:
		raise RuntimeError('replacement js is too long')

	# patch in replacement and pad
	data[js_ofs:js_ofs + js_sz] = (newjs + b'\r\n' * ((js_sz - len(newjs)+ 1) >> 1))[:js_sz]
	open(f'anode_{tag}.exe', 'wb').write(data)
	print(f'Patched {tag}.js into anode_{tag}.exe')

if __name__ == '__main__':
	main()
