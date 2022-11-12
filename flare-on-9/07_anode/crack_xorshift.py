# Invert v8 xorshift state from Math.random() samples
# v8 only uses s0 to generate double, which makes this a walk in the park
import os
import struct
import sys
sys.path.append('../tools')
from dandc import f2_linear_solve

# Invert the xor shr / xor shl operation: x ^= x >> n
def inv_xorshr(x, n, nbits=64):
	assert n > 0
	mask = (1 << n) - 1
	# the top n bits are clear text and can be used to decode the next n bits etc
	for m in range(0, nbits - n, n):
		x ^= (x & (mask << (nbits - n - m))) >> n
	return x

def inv_xorshl(x, n, nbits=64):
	assert n > 0
	mask = (1 << n) - 1
	# the bottom n bits are clear text and can be used to decode the next n bits etc
	for m in range(0, nbits - n, n):
		x ^= (x & (mask << m)) << n
	return x & ((1 << nbits) - 1)

# Murmur3Hash
def murmur3(x):
    x ^= x >> 33
    x *= 0xFF51AFD7ED558CCD
    x &= ((1 << 64) - 1)
    x ^= x >> 33
    x *= 0xC4CEB9FE1A85EC53
    x &= ((1 << 64) - 1)
    x ^= x >> 33
    return x

# Inverse of Murmur3Hash
def rumrum3(x):
    x ^= x >> 33
	x *= 0x9cb4b2f8129337db		# Modular inverse of magic constant above
    x &= ((1 << 64) - 1)
    x ^= x >> 33
    x *= 0x4f74430c22a54005
    x &= ((1 << 64) - 1)
    x ^= x >> 33
    return x


def xorshift_s0(state):
	return state & ((1 << 64) - 1)

def xorshift_s1(state):
	return (state >> 64) & ((1 << 64) - 1)

def xorshift(state):
	mask = (1 << 64) - 1
	# swap s0, s1
	s1 = state & mask
	s0 = (state >> 64) & mask
	s1 ^= (s1 << 23) & mask
	s1 ^= s1 >> 17
	s1 ^= s0
	s1 ^= s0 >> 26
	return (s1 << 64) | s0

def inv_xorshift(state):
	mask = (1 << 64) - 1
	s0 = state & mask
	s1 = (state >> 64) & mask
	s1 ^= s0 >> 26
	s1 ^= s0
	s1 = inv_xorshr(s1, 17)
	s1 = inv_xorshl(s1, 23)	
	return (s0 << 64) | s1

def xorshiftk(state, k=6):
	for i in range(k):
		state = xorshift(state)
	return state

def inv_xorshiftk(state, k=6):
	for i in range(k):
		state = inv_xorshift(state)
	return state

# extract doubles from xorshift stream
def xorshift_rng(state):
	while True:
		state = xorshift(state)
		yield struct.unpack('<d', ((xorshift_s0(state) >> 12) | 0x3FF0000000000000).to_bytes(8, 'little'))[0] - 1.0

# Weirdly, v8 generates caches of 64 random numbers by running xorshift128, but then
# feeds them to the user backwards, i.e. first Math.random() call gets output 64
# ... 64th call gets output 1 and then 65th call gets output 128 - beautiful
# (with zero indexing that is 0..63 -> 63 .. 0, 64..127 -> 127..64 etc)
# thought I was seeing double there for a sec

# extract the A matrix from a linear function y = f(x)
# nrows is the number of bits in y and ncols is the number of bits in x
def extract_A(f, ncols, nrows=None):
	if nrows is None:
		nrows = ncols
	if nrows < ncols:
		raise RuntimeError("extract_A(): Cannot model underdetermined system")
	A = [ 0 ] * nrows
	for i in range(ncols):
		y = f(1 << i)
		for j in range(i + 1):
			A[j] |= (y & (1 << j)) << (i - j)
		for j in range(i + 1, nrows):
			A[j] |= (y & (1 << j)) >> (j - i)
#		if nrows > ncols:
#			print(f'{i:d} {y:032x}/{y.bit_length()}')
#	if nrows > ncols:
#		print(ncols, len(A))
	return A

# sample binary representation of double from xorshift
# return m concatenated sampled doubles
class XorshiftBinned:
	def __init__(self, shift = 12, samples = 64, k = 16):
		self.shift = shift
		self.samples = samples
		self.k = k

	@property
	def bitsize(self):
		return (64 - self.shift) * self.samples

	def f(self, state):
		y = 0
		mask = (1 << (64 - self.shift)) - 1
		nbits = 0
		for i in range(self.samples):
			#nbits in range(0, 128 * 32, 64 - shift):
			#state = xorshiftk(state, k = 32)
			state = xorshiftk(state, self.k)
			y |= ((xorshift_s0(state) >> self.shift) & mask) << nbits
			nbits += 64 - self.shift
		return y
		
# Check if a given xorshift state is from JavaScript
# SetSeed type 1 or type 2 (returns 0, None or  1, seed or 2, seed)
def check_javascript_seed(state):
	mask = (1 << 64) - 1
	s0 = xorshift_s0(state)
	s1 = xorshift_s1(state)
	q = rumrum3(s0)
	if murmur3(~q & mask) == s1:
		return 1, q
	if murmur3(~s0 & mask) == s1:
		return 2, q
	return 0, None

def find_key_from_randoms(filename):
	data = open(filename, 'rb').read()
	assert len(data) == 8 * 64
	# Invert the stripe of 64 doubles
	doubles = struct.unpack('<' + 'd' * 64, data)[::-1]
	# Convert back to binary extract from xorshift state
	bins = list(map(lambda x: int.from_bytes(struct.pack('<d', x + 1.0), 'little') & ((1 << 52) - 1), doubles))
	# Now set up problem
	v = XorshiftBinned(samples = 4, k = 1)
	A = extract_A(v.f, 128, v.bitsize)
	# calculate y vector
	y = 0
	for k in range(4):
		y |= bins[k] << (k * 52)
	# Solve
	state = f2_linear_solve(A, y, 128)
	return state

def show_key_from_randoms(filename):
	state = find_key_from_randoms(filename)
	ofs, stype, seed = scan_javascript_seed(state, 8192)
	print(f'{filename:<32s}0x{state:032x} {ofs if ofs is not None else ""} {stype if ofs is not None else ""} {f"0x{seed:016x}" if stype is not None else ""}')

def make_generator(f, state0):
	def gen():
		state = state0
		while True:
			state = f(state)
			yield state
	return gen

# Inner function
def scan_javascript_seed_inner(gen, k):
	ofs = 0
	for state in gen():
		ofs += 1
		stype, seed = check_javascript_seed(state)
		if stype > 0:
			return ofs, stype, seed
		if ofs >= k:
			break
	return None, None, None

# Scan for a javascript seeding event with K states of given state
# returns offset, seed_type and seed
def scan_javascript_seed(state, k):
	stype, seed = check_javascript_seed(state)
	if stype > 0:
		return 0, stype, seed
	ofs, stype, seed = scan_javascript_seed_inner(make_generator(xorshift, state), k)
	if ofs is not None:
		return ofs, stype, seed
	ofs, stype, seed = scan_javascript_seed_inner(make_generator(inv_xorshift, state), k)
	if ofs is not None:
		return -ofs, stype, seed
	return None, None, None

if __name__ == '__main__':
	for fn in sys.argv[1:]:
		show_key_from_randoms(fn)

