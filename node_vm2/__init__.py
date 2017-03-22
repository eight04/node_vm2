#! python3

"""
node_vm2

A Python 3 to Node.js + vm2 binding, helps you execute JavaScript safely.

This module looks following places for node executable:

1. ``node`` in the path
2. ``NODE_EXECUTABLE`` env variable, the path to ``node``.
"""

import abc
import json
from subprocess import Popen, PIPE
from os import path, environ

from .__pkginfo__ import __version__

NODE_EXECUTABLE = environ.get("NODE_EXECUTABLE", "node")
VM_SERVER = path.join(path.dirname(__file__), "vm-server")

class VMError(Exception):
	"""Error throwed by VM"""
	pass
	
class NodeBridge:
	"""The bridge to node process. Extended by VMs."""
	def __init__(self):
		self.closed = None
		self.process = None
		
	def __enter__(self):
		"""The bridge can be used as a context manager, which automatically
		connect to the VM when entering.
		
		..code-block:: python
		
			vm = VM()
			vm.connect()
			vm.run(code)
			vm.close()
			
		vs.
		
		..code-block:: python
		
			with VM() as vm:
				vm.run(code)
		"""
		return self.connect()
		
	def __exit__(self, exc_type, exc_value, traceback):
		"""Call :method:`close` when exit."""
		self.close()
		
	def connect(self):
		"""Create subprocess and connect to Node.js"""
		if self.closed:
			raise VMError("The VM is closed")
			
		args = [NODE_EXECUTABLE, VM_SERVER]
		self.process = Popen(args, bufsize=0, stdin=PIPE, stdout=PIPE)
		self.onconnect()
		self.closed = False
		return self

	@abc.abstractmethod
	def onconnect(self):
		"""Overwrite"""
		pass
	
	def close(self):
		"""Close the connection. Once connection is closed, you can't re-open
		it again."""
		if self.closed:
			return self
		self.send({"action": "close"})
		self.process.communicate()
		self.process = None
		self.closed = True
		return self
	
	def send(self, o):
		"""Send object to Node.
		
		The object must be json-encodable.
		"""
		text = json.dumps(o) + "\n"
		self.process.stdin.write(text.encode("utf-8"))
		return self
	
	def read(self):
		"""Read the output from Node."""
		out = self.process.stdout.readline().decode("utf-8")
		data = json.loads(out)
		if data["status"] != "success":
			raise VMError(data["error"])
		# https://github.com/PyCQA/pylint/issues/922
		# pylint: disable=no-member
		return data.get("value")

class VM(NodeBridge):
	"""VM class, represent `vm2.VM <https://github.com/patriksimek/vm2#vm>`_"""
	def __init__(self, code=None, **options):
		"""Create VM
		
		:param code: str, optional. js code to initilize the VM.
		:param options: The options sending to `vm2.VM`_.
		"""
		super().__init__()
		self.code = code
		self.options = options
		
	def onconnect(self):
		# called by NodeBridge.connect
		self.send({
			"action": "create",
			"type": "VM",
			"code": self.code,
			"options": self.options
		}).read()

	def run(self, code):
		"""Execute JavaScript and return the result."""
		return self.send({"action": "run", "code": code}).read()
		
	def call(self, function_name, *args):
		"""Call the function and return the result.
		
		:param function_name: The function to call.
		:param args: Function arguments.
		"""
		return self.send({
			"action": "call",
			"functionName": function_name,
			"args": args
		}).read()
		
class NodeVM(NodeBridge):
	"""NodeVM class, represent `vm2.NodeVM 
	<https://github.com/patriksimek/vm2#nodevm>`_.
	"""
	def __init__(self, **options):
		"""Create NodeVM.
		
		:param options: the options sent to `vm2.NodeVM`_.
		"""
		super().__init__()
		self.options = options
		
	def onconnect(self):
		# called by bridge
		self.send({
			"action": "create",
			"type": "NodeVM",
			"options": self.options
		}).read()
		
	def run(self, code, filename=None):
		"""Run the code and return a :class:`NodeVMModule`
		
		:param code: the code to run. The code should work like a commonjs
			module. See `vm2.NodeVM`__ for details.
		:param filename: optional. Currently this argument has no effects.
		:return: :class:`NodeVMModule`.
		"""
		id = self.send({
			"action": "run",
			"code": code,
			"filename": filename
		}).read()
		return NodeVMModule(id, self)
		
	@classmethod
	def code(cls, code, filename=None, options=None):
		"""Create a module in VM.
		
		..code-block::python
		
			with NodeVM.code(code) as module:
				result = module.call_member("method")
				
		vs.
		
		..code-block::python
		
			with NodeVM() as vm:
				module = vm.run(code)
				result = module.call_member("method")
		"""
		vm = cls(**options)
		module = vm.run(code, filename)
		module.CLOSE_ON_EXIT = True
		return module
		
class NodeVMModule:
	"""Since we can only pass primitive values between python and node, we use 
	this wrapper to access module created from NodeVM.
	
	This class shouldn't initiate by user directly.
	"""
	def __init__(self, id, bridge):
		self.id = id
		self.bridge = bridge
		self.CLOSE_ON_EXIT = False
		
	def call(self, *args):
		"""Call the module, in case that the module itself is a function."""
		return self.bridge.send({
			"id": self.id,
			"action": "call",
			"args": args
		}).read()
		
	def get(self):
		"""Get the module, in case that the module itself is primitive value"""
		return self.bridge.send({
			"id": self.id,
			"action": "get"
		}).read()
		
	def call_member(self, member, *args):
		"""Call the member of the module"""
		return self.bridge.send({
			"id": self.id,
			"action": "callMember",
			"member": member,
			"args": args
		}).read()
		
	def get_member(self, member):	
		"""Get the member of the module"""
		return self.bridge.send({
			"id": self.id,
			"action": "getMember",
			"member": member
		}).read()
		
	def destroy(self):
		"""Destroy the module"""
		out = self.bridge.send({
			"id": self.id,
			"action": "destroy"
		}).read()
		if self.CLOSE_ON_EXIT:
			self.bridge.close()
		return out
		
	def __enter__(self):
		"""This class can be used as context manager. See :meth:`NodeVM.code`.
		"""
		return self
		
	def __exit__(self, exc_type, exc_value, tracback):
		"""The NodeVM will be closed when exiting the module."""
		if self.CLOSE_ON_EXIT:
			self.bridge.close()
			
def eval(code, **options):
	"""A shortcut to eval JavaScript.
	
	This function will create a :class:`VM`, run code, and return the result.
	"""
	with VM(**options) as vm:
		return vm.run(code)
