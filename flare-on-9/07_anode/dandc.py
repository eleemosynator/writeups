# Divide-and-Conquer attack on the cipher in anode
# Requires built "anode_showouput.exe" that displays the output of the cipher as a list of numbers
# Solve challenge 07 by exploiting it's simple dependence structure and lienar properties, starting from bottom bit upwards
# as operators ^, +, - only feed information upwards, the bottom-most unknown bit is always linear

import sys
sys.path.append('../tools')
import subprocess
from timing import clock

target = bytes([106, 196, 106, 178, 174, 102, 31, 91, 66, 255, 86, 196, 74, 139, 219, 166, 106, 4, 211, 68, 227, 72, 156, 38, 239, 153, 223, 225, 73, 171, 51, 4, 234, 50, 207, 82, 18, 111, 180, 212, 81, 189, 73, 76])

def run_flag(flag):
	with subprocess.Popen(['anode_showoutput.exe'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) as proc:
		out, err = proc.communicate(flag + b'\n')
		proc.wait()
	pre = b'Enter flag:'
	if not out.startswith(pre):
		raise RuntimeError('Unexpected response: ' + repr(out))
	out = list(map(int, out[len(pre):-1].decode('utf-8').split(',')))
	return bytes(out)

# Linear Algebra in F_2
# Solve the system of equations A x = y where:
#  A is a matrix with r rows and c columns, c >= r
#  x is unknown bitvector
#  y is the rhs bitvector
# A is encoded as a list of ints with A_{ij} being the jth bit of the ith row
# where i, j are zero-indexed
# x and y are also encoded as integers
def f2_linear_solve(A, y, ncols=None, validate=False):
	if ncols is None:
		ncols = len(A)
	if ncols > len(A):
		raise RuntimeError(f'f2_linear_solve(): Underdetermined system {len(A)}x{ncols}')
	# copy A to avoid ruining things
	A = A[:]
	topbit = 1 << ncols
	mask = topbit - 1
	if validate:
		for i, v in enumerate(A):
			if (v & mask) != v:
				raise RuntimeError(f'f2_linear_solve(): row {i} of A exceedes column count: {v.bit_length()} vs {ncols}')
		if (y & ((1 << len(A)) - 1)) != y:
			raise RuntimeError(f'f2_linear_solve(): rhs y of system exceeds row count: {y.bit_length()} vs {len(A)}')
	# Encode RHS into high bits of A to make operations simpler
	for i in range(ncols):
		A[i] |= (y & (1 << i)) << (ncols - i)
	for i in range(ncols, len(A)):
		A[i] |= (y & (1 << i)) >> (i - ncols)
	# Now solve
	for c in range(ncols):	# Columns we are solving for
		bit = 1 << c
		if not (A[c] & bit):
			# This row does not have this bit set, find another
			for j in range(c + 1, len(A)):
				if A[j] & bit:
					# swap, and done
					A[c], A[j] = A[j], A[c]
					break
		v = A[c]
		if not (v & bit):
			raise RuntimeError(f'f2_linear_solve(): Underdetermined system - bit {c} cannot be resolved')
		# Now eliminate this bit from all other rows
		for i in range(len(A)):
			if i == c:
				continue
			if A[i] & bit:
				A[i] ^= v
	# Done, ensure that the system is not impossible (i.e. all rows and RHS of A after ncols are idenitically zero)
	if len(A) > ncols and max(A[ncols:]) != 0:
		raise RuntimeError(f'f2_linear_solve(): Impossible linear system - non-zero residue after elimination')
	# Finally, extract the x vector
	x = 0
	for i in range(ncols):
		x |= (A[i] & topbit) >> (ncols - i)
	return x


def main():
	t0 = clock()
	# Iterative solving of the bits
	# base value
	flag = bytearray(b'\x40' * len(target))
	base = run_flag(flag)
	for bit in range(7):		# We don't need to solve for bit 7
		t1 = clock()
		bitmask = 1 << bit
		lomask = bitmask - 1
		vector = bytearray(flag)
		# The array element A_{jk} is bit k of A[j]
		A = [ 0 ] * len(flag)
		for i in range(len(flag)):
			# Flip the current bit of input byte i
			vector[i] ^= bitmask
			out = run_flag(vector)
			sys.stdout.write('.')
			sys.stdout.flush()
			# Reset the current bit of input byte i
			vector[i] = flag[i]
			# extract
			for j in range(len(flag)):
				A[j] |= (((out[j] ^ base[j]) >> bit) & 1) << i
		# Now calculate the RHS of the A x = y equation for this bit
		y = 0
		for i in range(len(base)):
			y |= (((target[i] ^ base[i]) >> bit) & 1) << i
		x = f2_linear_solve(A, y)
		if x is None:
			print('Failed to solve matrix')
			sys.exit(1)
			
		# Now update the flag
		for i in range(len(flag)):
			flag[i] ^= ((x >> i) & 1) << bit
		newbase = run_flag(flag)
		assert all([ (a & (bitmask | lomask)) == (b & (bitmask | lomask)) for a, b in zip(newbase, target) ])
		base = newbase
		sys.stdout.write('\n')
		print(f'{clock() - t1:6.2f}s {bit:d} {flag.decode("utf-8")}')
	print(f'{clock() - t0:6.2f}s Total time\n')
	print('Flag: ', bytes([ x & 0x7f for x in flag ]).decode('utf-8'))

if __name__ == '__main__':
	main()

# n0t_ju5t_A_j4vaSCriP7_ch4l1eng3@flare-on.com
