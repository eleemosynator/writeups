// Patch for anode
// Load modules from the command line and run a REPL
var loaded = [];

// argv[0] is the node binary, argv[1] is the main js file
for (var i = 2; i < process.argv.length; ++i) {
	const module_name = "./" + process.argv[i];
	console.log("Loading: " + module_name);
	loaded.push(require(module_name));
}
// Load the repl

const repl = require('repl');

const exe_path_elts = process.argv[0].split('\\');
const exe_name = exe_path_elts[exe_path_elts.length - 1].split('.')[0];

repl.start(exe_name + '>');

