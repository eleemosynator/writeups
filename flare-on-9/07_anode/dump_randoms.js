// Export random numbers - we export the first 64 double because JavaScript V8
// has this wonderful habbit of generating random numbers in blocks of 64 and
// then serving them to the user in reverse order

const fs = require('fs');

var n = 64
var buff = Buffer.from(Array(n * 8));
for (var i = 0; i < n; ++i) {
	var dbl = Math.random();
	buff.writeDoubleLE(dbl, 8 * i);
}
const exe_path_elts = process.argv[0].split('\\');
const exe_name = exe_path_elts[exe_path_elts.length - 1].split('.')[0];
const filename = './randoms_' + exe_name + '.bin'
fs.writeFileSync(filename, buff);
console.log("dump_randoms: Wrote " + n.toString() + " randoms to " + filename);


