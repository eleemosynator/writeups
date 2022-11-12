import os
import struct
import sys

SENTINEL = b'<nexe~~sentinel>'

# returns offset and size of resource bundle
def find_nexe_resource(data, fname):
	if data[-len(SENTINEL)-16:-16] != SENTINEL:
		raise RuntimeError(f'{fname}: missing sentinel tag')
	lengths = struct.unpack('<dd', data[-16:])
	js_len = int(lengths[1])
	ofs = -js_len - len(SENTINEL) - 16
	return ofs, js_len


def unnexe(fname):
	data = open(fname, 'rb').read()
	ofs, js_len = find_nexe_resource(data, fname)
	js = data[ofs:ofs + js_len]
	jsname = fname.replace('.exe', '.js')
	assert jsname != fname
	open(jsname, 'wb').write(js)
	print(f'extracted {js_len:,d} from {fname} to {jsname}')


def main():
	if len(sys.argv) < 2:
		print(f'Usage: {os.path.basename(sys.argv[0])} <nexe_filename>')
		sys.exit(1)
	for fname in sys.argv[1:]:
		unnexe(fname)

if __name__ == '__main__':
	main()
