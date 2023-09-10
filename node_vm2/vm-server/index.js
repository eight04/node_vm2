/* eslint no-console: 0 */

var readline = require("readline"),
    vm2 = require("vm2"),
    rl = readline.createInterface({
        input: process.stdin
    }),
    vmList = collection();
var fun_list= [], jc = 0
let id_jc = 0
let ret = {}

async function call_pyfun(obj,vmId, args) {
    let event = {
        type: "event",
        name: "pyfun",
        ids: obj,
        vmId:vmId,
        value: args,
        cid: id_jc
    };
    id_jc += 1
    event=obj_to_str(event)
    event.outputEncode=true
    console.log(JSON.stringify(event));
    let p=new Promise((resolve) => {
        // 定义一个尝试获取ret[event.cid]值的函数
        function attempt() {
            // 如果存在ret[event.cid]值
            if (event.cid in ret) {
                // 删除它，并用resolve函数传递给Promise
                let tmp = ret[event.cid];
                delete ret[event.cid];
                resolve(tmp);
            } else {
                // 否则，延迟10毫秒后再次尝试
                setTimeout(attempt, 10);
            }
        }
        // 开始第一次尝试
        attempt();
    });
    return await p

}

function obj_to_str(obj) {
    //判断类型
    if (typeof obj === 'object') {
        if (Array.isArray(obj)) {
            for (let i = 0; i < obj.length; i++) {
                obj[i] = obj_to_str(obj[i])
            }
        } else {
            for (let key in obj) {
                obj[key] = obj_to_str(obj[key]);
            }
        }
        return obj
    } else if (typeof obj === 'function') {
        if (obj.pyfun_id) {
            return obj.pyfun_id
        }
        if (!Object.values(fun_list).includes(obj)) {
            fun_list[jc] = obj
            obj = 'jsfun' + jc.toString()
            jc++
        } else {
            obj = 'jsfun' + fun_list.indexOf(obj).toString()
        }
        return obj
    } else if (typeof obj === 'string') {
        return 'str' + obj
    } else if (typeof obj === 'undefined') {
        return undefined
    } else if (typeof obj === 'number') {
        return obj
    } else if (typeof obj === 'boolean') {
        return obj
    } else {
        return 'obj' + obj.toString()
    }
}

function str_to_obj(obj) {
    //判断类型
    if (typeof obj === 'object') {
        if (Array.isArray(obj)) {
            for (let i = 0; i < obj.length; i++) {
                obj[i] = str_to_obj(obj[i])
            }
        } else {
            for (let key in obj) {
                obj[key] = str_to_obj(obj[key]);
            }
        }
        return obj
    } else if (typeof obj === 'string') {
        if (obj.indexOf('str') === 0) {
            return obj.slice(3)
        } else if (obj.indexOf('jsfun') === 0) {
            return fun_list[parseInt(obj.slice(5))]
        } else if (obj.indexOf('pyfun') === 0) {
            let fn = async function (...args) {
                return await call_pyfun(obj, -1,args)
            }
            fn.pyfun_id = obj
            // console.log(fn)
            return fn
        } else {
            return eval(obj.slice(3))
        }
    } else {
        return obj
    }
}

rl.on("line", line => {
    let input_tmp;
    var result, err, input;

    try {
        input_tmp = JSON.parse(line);
    } catch (err) {
        input_tmp = undefined;
    }

    if (!input_tmp) {
        return
    }

    if (input_tmp.inputEncode) {
        try {
            input = str_to_obj(input_tmp)
        } catch (e) {
            input = input_tmp
        }
    } else {
        input = input_tmp
    }
    if(input.action==='ret'){
        ret[input.cid] = input.value
        return;
    }

    try {
        result = processLine(input);
    } catch (_err) {
        err = _err;
    }
    if (err) {
        result = {status: "error", error: err.message || err};
    } else {
        result = result || {};
        result.status = "success";
    }
    result.id = input.id;
    result.type = "response";
    Promise.resolve(result.value)
        .then(value => {
            result.value=value
            result.vmId=input.vmId
            result.moduleId=input.moduleId
            result = obj_to_str(result);
            result.outputEncode=true
            console.log(JSON.stringify(result));
        })
        .catch(error => {
            result.status = "error";
            result.error = error.message || error;
            delete result.value;
            console.log(JSON.stringify(result));
        });
});

function processLine(input) {
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
    var _console = input.options.console || "inherit";
    if (_console !== "off") {
        input.options.console = "redirect";
    }
    var _vm = new vm2.NodeVM(input.options),
        modules = collection();
    var vm = {
        run({code, filename}) {
            const mod = filename != null ?
                _vm.run(code, filename) :
                _vm.run(code);
            return {
                value: modules.add(mod)
            };
        },
        get({moduleId}) {
            return {
                value: modules.get(moduleId)
            };
        },
        call({moduleId, args = []}) {
            return {
                value: modules.get(moduleId)(...args)
            };
        },
        getMember({moduleId, member}) {
            return {
                value: modules.get(moduleId)[member]
            };
        },
        callMember({moduleId, member, args = []}) {
            return {
                value: modules.get(moduleId)[member](...args)
            };
        },
        callJsFunc({moduleId,ids, args = []}) {
            return {
                value: fun_list[parseInt(ids)].call(modules.get(1),...args)
            };
        },
        setMember({moduleId, member, arg}) {
            modules.get(moduleId)[member] = arg
        },

        destroyModule({moduleId}) {
            modules.remove(moduleId);
        }
    };
    let id = vmList.add(vm);
    _vm.on("call_pyfun", (obj, vmId,args) => {
        return call_pyfun(obj,id,args)
    });
    if (_console !== "off") {
        _vm.on("console.log", (...args) => {
            var event = {
                vmId: id,
                type: "event",
                name: "console.log",
                value: args.join(" ")
            };
            console.log(JSON.stringify(event));
        });
        _vm.on("console.error", (...args) => {
            var event = {
                vmId: id,
                type: "event",
                name: "console.log",
                value: args.join(" ")
            };
            console.log(JSON.stringify(event));
        });
    }
    return {
        value: id
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
