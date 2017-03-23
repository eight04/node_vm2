var readline = require("readline"),
	vm2 = require("vm2"),
	rl = readline.createInterface({
		input: process.stdin
	}),
	vmList = collection();
	
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
		case "ping":
			return;
			
		case "close":
			setImmediate(() => rl.close());
			return;
			
		case "create":
			return createVM(input);
			
		case "destroy":
			return destroyVM(input);
			
		default:
			var vm = vmList.get(input.vmId);
			if (!vm[input.action]) {
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

function destroyVM(input) {
	vmList.remove(input.vmId);
}

function createNormalVM(input) {
	var _vm = new vm2.VM(input.options);
	if (input.code) {
		_vm.run(input.code);
	}
	var vm = {
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
	return {
		value: vmList.add(vm)
	};
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
		modules = collection();
	if (console) {
		console.register(_vm);
	}
	var vm = {
		run({code, filename}) {
			return modules.add(_vm.run(code, filename));
		},
		get({moduleId}) {
			return modules.get(moduleId);
		},
		call({moduleId, args = []}) {
			return modules.get(moduleId)(...args);
		},
		getMember({moduleId, member}) {
			return modules.get(moduleId)[member];
		},
		callMember({moduleId, member, args = []}) {
			return modules.get(moduleId)[member](...args);
		},
		destroyModule({moduleId}) {
			modules.remove(moduleId);
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
	return {
		value: vmList.add(vm)
	};
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

function collection() {
	var inc = 1,
		hold = Object.create(null);
	return {
		add(item) {
			hold[inc] = item;
			return inc++;
		},
		remove(id) {
			if (!(id in hold)) {
				throw new Error("Index doesn't exist: " + id);
			}
			delete hold[id];
		},
		get(id) {
			if (!(id in hold)) {
				throw new Error("Index doesn't exist: " + id);
			}
			return hold[id];
		},
		has(id) {
			return id in hold;
		}
	};
}
