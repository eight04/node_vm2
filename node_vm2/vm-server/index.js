var readline = require("readline"),
	vm2 = require("vm2"),
	rl = readline.createInterface({
		input: process.stdin,
		terminal: false
	});
	
rl.on("line", line => {
	var value, err;
	try {
		value = processLine(line);
	} catch (_err) {
		err = _err;
	}
	var out;
	if (err) {
		out = {status: "error", error: err.message};
	} else {
		out = {status: "success", value: value};
	}
	console.log(JSON.stringify(out));
});

function processLine(input) {
	input = JSON.parse(input);
	switch (input.action) {
		case "create":
			return createVM(input);
			
		case "close":
			return destroyVM();
			
		default:
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
			throw new Error("Unknown VM type: " + type);
	}
}

var vm;

function destroyVM() {
	vm = null;
	setImmediate(() => rl.close());
}

function createNormalVM(input) {
	var _vm = new vm2.VM(input.options);
	if (input.code) {
		_vm.run(input.code);
	}
	vm = {
		run({code}) {
			return _vm.run(code);
		},
		call({functionName, args}) {
			return _vm.run(functionName)(...args);
		}
	};
}

function createNodeVM(input) {
	var _vm = new vm2.NodeVM(input.options),
		modules = {},
		_id = 1;
	vm = {
		run({code, filename}) {
			modules[_id] = _vm.run(code, filename);
			return _id++;
		},
		get({id}) {
			return modules[id];
		},
		call({id, args}) {
			return modules[id](...args);
		},
		getMember({id, member}) {
			return modules[id][member];
		},
		callMember({id, member, args}) {
			return modules[id][member](...args);
		},
		destroy({id}) {
			delete modules[id];
		}
	};
}
