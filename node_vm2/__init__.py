#! python3

import json
from subprocess import Popen, PIPE, TimeoutExpired
from os import path, environ

from .__pkginfo__ import __version__

NODE_EXECUTABLE = environ.get("NODE_EXECUTABLE", "node")
VM_SERVER = path.join(path.dirname(__file__), "vm-server")

class VMError(Exception):
	pass
	
def decode_output(s):
	try:
		s = json.loads(s)
	except json.JSONDecodeError:
		raise TypeError("Failed to decode output: " + out)

class NodeBridge:
	def __init__(self, code=None, filename=None, **options):
		self.closed = None
		self.process = None
		
	def __enter__(self):
		return self.connect()
		
	def __exit__(self, exc_type, exc_value, traceback):
		self.close()
		
	def connect(self):
		if self.closed:
			raise VMError("The VM is closed")
			
		args = [NODE_EXECUTABLE, VM_SERVER]
		self.process = Popen(args, bufsize=0, stdin=PIPE, stdout=PIPE, encoding="utf-8")
		self.onconnect()
		self.closed = False
		return self
	
	def close(self):
		self.send({"action": "close"})
		self.process.communicate()
		self.process = None
		self.closed = True
		return self
	
	def send(self, o):
		self.process.stdin.write(json.dumps(o) + "\n")
		return self
	
	def read(self):
		out = self.process.stdout.readline()
		data = json.loads(out)
		if data["status"] != "success":
			raise VMError(data["error"])
		return data.get("value")

class VM(NodeBridge):
	def __init__(self, code=None, **options):
		super().__init__()
		self.code = code
		self.options = options
		
	def onconnect(self):
		self.send({
			"action": "create",
			"type": "VM",
			"code": self.code,
			"options": self.options
		}).read()

	def run(self, code):
		return self.send({"action": "run", "code": code}).read()
		
	def call(self, fn, *args):
		return self.send({
			"action": "call",
			"functionName": fn,
			"args": args
		}).read()
		
class NodeVM(NodeBridge):
	def __init__(self, **options):
		super().__init__()
		self.options = options
		
	def onconnect(self):
		self.result = self.send({
			"action": "create",
			"type": "NodeVM",
			"options": self.options
		}).read()
		
	def run(self, code, filename=None):
		id = self.send({
			"action": "run",
			"code": code,
			"filename": filename
		}).read()
		return NodeVMModule(id, self)
		
	@classmethod
	def code(cls, code, filename=None, options=None):
		vm = cls(**options)
		module = vm.run(code, filename)
		module.CLOSE_ON_EXIT = True
		return module
		
class NodeVMModule:
	def __init__(self, id, bridge):
		self.id = id
		self.bridge = bridge
		self.CLOSE_ON_EXIT = False
		
	def call(self, *args):
		return self.bridge.send({
			"id": self.id,
			"action": "call",
			"args": args
		}).read()
		
	def get(self):
		return self.bridge.send({
			"id": self.id,
			"action": "get"
		}).read()
		
	def call_member(self, member, *args):
		return self.bridge.send({
			"id": self.id,
			"action": "callMember",
			"member": member,
			"args": args
		}).read()
		
	def get_member(self, member):
		return self.bridge.send({
			"id": self.id,
			"action": "getMember",
			"member": member
		}).read()
		
	def destroy(self):
		out = self.bridge.send({
			"id": self.id,
			"action": "destroy"
		}).read()
		if self.CLOSE_ON_EXIT:
			self.bridge.close()
		return out
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, tracback):
		if self.CLOSE_ON_EXIT:
			self.bridge.close()
