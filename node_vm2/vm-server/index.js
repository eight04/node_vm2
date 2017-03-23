var readline = require("readline"),
	vm2 = require("vm2"),
	rl = readline.createInterface({
		input: process.stdin
	}),
	vm;
	
rl.on("line", line => {
	var result, err;
	try {
		result = processLine(line);
	} catch (_err) {
		err = _err;
	}
	if (err) {
		result = {status: "error", error: err.message};
	} else {
		result = result || {};
		result.status = "success";
	}
	console.log(JSON.stringify(result));
});

function processLine(input) {
	input = JSON.parse(input);
	switch (input.action) {
		case "create":
			return createVM(input);
			
		case "close":
			setImmediate(() => rl.close());
			return destroyVM();
			
		default:
			if (!vm) {
				throw new Error("VM is not actived");
			}
			if (!vm.hasOwnProperty(input.action)) {
				throw new Error("Unknown action: " + input.action);
			}
			return vm[input.action](input);
	}
}

function createVM(input) {
	switch (input.type) {
		case "VM":
			return createNormalVM(input);
			
		case "NodeVM":
			return createNodeVM(input);
			
		default:
			throw new Error("Unknown VM type: " + input.type);
	}
}

function destroyVM() {
	vm = null;
}

function createNormalVM(input) {
	var _vm = new vm2.VM(input.options);
	vm = {
		run({code}) {
			return {
				value: _vm.run(code)
			};
		},
		call({functionName, args}) {
			return {
				value: _vm.run(functionName)(...args)
			};
		}
	};
	if (input.code) {
		_vm.run(input.code);
	}
}

function createNodeVM(input) {
	if (!input.options) {
		input.options = {};
	}
	var console;
	if (input.options.console != "off") {
		console = nodeVmConsole(input.options.console);
		input.options.console = "redirect";
	}
	var _vm = new vm2.NodeVM(input.options),
		modules = {},
		_id = 1;
	if (console) {
		console.register(_vm);
	}
	vm = {
		run({code, filename}) {
			modules[_id] = _vm.run(code, filename);
			return _id++;
		},
		get({id}) {
			return modules[id];
		},
		call({id, args = []}) {
			return modules[id](...args);
		},
		getMember({id, member}) {
			return modules[id][member];
		},
		callMember({id, member, args = []}) {
			return modules[id][member](...args);
		},
		destroy({id}) {
			delete modules[id];
		}
	};
	for (const [key, fn] of Object.entries(vm)) {
		vm[key] = input => {
			var result = {
				value: fn(input)
			};
			if (console) {
				return console.assign(result);
			}
			return result;
		};
	}
}

function nodeVmConsole(type = "inherit") {
	var data = {
		log: "",
		error: ""
	};
	return {
		assign(o) {
			o["console.log"] = data.log;
			o["console.error"] = data.error;
			data.log = "";
			data.error = "";
			return o;
		},
		register(vm) {
			vm.on("console.log", (...args) => {
				data.log += args.join(" ") + "\n";
			});
			vm.on("console.error", (...args) => {
				data.error += args.join(" ") + "\n";
			});
		},
		type
	};
}
