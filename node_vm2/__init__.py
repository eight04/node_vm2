#! python3

"""
node_vm2
========

A Python 3 to Node.js + vm2 binding, helps you execute JavaScript safely.

There are 2 ways to specify ``node`` executable:

1. Add the directory of ``node`` to ``PATH`` env variable.
2. Set ``NODE_EXECUTABLE`` to the path of the executable.
"""

import abc
import json
import sys

from subprocess import Popen, PIPE
from os import path, environ

from .__pkginfo__ import __version__

NODE_EXECUTABLE = environ.get("NODE_EXECUTABLE", "node")
VM_SERVER = path.join(path.dirname(__file__), "vm-server")

class VMError(Exception):
	"""Errors thrown by VM."""
	pass
	
class NodeBridge:
	"""The bridge to node process, extended by VMs and shouldn't be initiated
	by users."""
	def __init__(self):
		self.closed = None
		self.process = None
		
	def __enter__(self):
		"""The bridge can be used as a context manager, which automatically
		:meth:`connect` the VM.
		
		.. code-block:: python
		
			vm = VM()
			vm.connect()
			vm.run(code)
			vm.close()
			
		vs.
		
		.. code-block:: python
		
			with VM() as vm:
				vm.run(code)
		"""
		return self.connect()
		
	def __exit__(self, exc_type, exc_value, traceback):
		"""See :meth:`close`."""
		self.close()
		
	def connect(self):
		"""Create subprocess and connect to Node.js."""
		if self.closed:
			raise VMError("The VM is closed")
			
		args = [NODE_EXECUTABLE, VM_SERVER]
		self.process = Popen(args, bufsize=0, stdin=PIPE, stdout=PIPE)
		self.onconnect()
		self.closed = False
		return self

	@abc.abstractmethod
	def onconnect(self):
		# overwrite by subclasses
		pass
	
	def close(self):
		"""Close the connection. Once connection is closed, you can't re-open
		it."""
		if self.closed:
			return self
		self.send({"action": "close"})
		self.process.communicate()
		self.process = None
		self.closed = True
		return self
	
	def send(self, object):
		"""Send object to Node.
		
		The object must be json-encodable.
		"""
		text = json.dumps(object) + "\n"
		self.process.stdin.write(text.encode("utf-8"))
		return self
	
	def read(self):
		"""Read the output from Node."""
		out = self.process.stdout.readline().decode("utf-8")
		data = json.loads(out)
		self.onread(data)
		# https://github.com/PyCQA/pylint/issues/922
		# pylint: disable=no-member
		return data.get("value")
		
	def onread(self, data):
		# status check
		if data["status"] != "success":
			raise VMError(data["error"])

class VM(NodeBridge):
	"""VM class, represent `vm2.VM <https://github.com/patriksimek/vm2#vm>`_.
	"""
	def __init__(self, code=None, **options):
		"""Create VM
		
		:param code: str. Optional. The JavaScript code to run after creating
			the VM. Useful to define some functions.
			
		:param options: The options for `vm2.VM`_.
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
		
		:param options: the options for `vm2.NodeVM`_.
		
		If ``console="redirect"``, those console output will return as strings,
		which can be access with :attr:`NodeVM.console_log` and
		:attr:`NodeVM.console_error`.
		"""
		super().__init__()
		self.options = options
		self.console = options.get("console", "inherit")
		self.console_log = None
		self.console_error = None
		
	def onconnect(self):
		# called by bridge
		self.send({
			"action": "create",
			"type": "NodeVM",
			"options": self.options
		}).read()
		
	def onread(self, data):
		# called by bridge.read
		if self.console == "inherit":
			text = data.get("console.log")
			if text is not None:
				sys.stdout.write(text)
				
			text = data.get("console.error")
			if text is not None:
				sys.stderr.write(text)
				
		elif self.console == "redirect":
			self.console_log = data.get("console.log")
			self.console_error = data.get("console.error")
			
		super().onread(data)
		
	def run(self, code, filename=None):
		"""Run the code and return a :class:`NodeVMModule`
		
		:param code: the code to run. The code should work like a commonjs
			module. See `vm2.NodeVM`_ for details.
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
	def code(cls, code, filename=None, **options):
		"""Create a module in VM.
		
		.. code-block:: python
		
			with NodeVM.code(code) as module:
				result = module.call_member("method")
				
		vs.
		
		.. code-block:: python
		
			with NodeVM() as vm:
				module = vm.run(code)
				result = module.call_member("method")
		"""
		vm = cls(**options)
		module = vm.connect().run(code, filename)
		module.CLOSE_ON_EXIT = True
		return module
		
class NodeVMModule:
	"""Since we can only pass primitive values between python and node, we use 
	this wrapper to access module created from NodeVM.
	
	This class shouldn't be initiated by users directly.
	
	You can access the VM object with attribute :attr:`NodeVMModule.vm`.
	"""
	def __init__(self, id, vm):
		self.id = id
		self.vm = vm
		self.CLOSE_ON_EXIT = False
		
	def call(self, *args):
		"""Call the module, in case that the module itself is a function."""
		return self.vm.send({
			"id": self.id,
			"action": "call",
			"args": args
		}).read()
		
	def get(self):
		"""Return the module, in case that the module itself is primitive
		value.
		"""
		return self.vm.send({
			"id": self.id,
			"action": "get"
		}).read()
		
	def call_member(self, member, *args):
		"""Call a function member."""
		return self.vm.send({
			"id": self.id,
			"action": "callMember",
			"member": member,
			"args": args
		}).read()
		
	def get_member(self, member):	
		"""Return the member."""
		return self.vm.send({
			"id": self.id,
			"action": "getMember",
			"member": member
		}).read()
		
	def destroy(self):
		"""Destroy the module."""
		out = self.vm.send({
			"id": self.id,
			"action": "destroy"
		}).read()
		if self.CLOSE_ON_EXIT:
			self.vm.close()
		return out
		
	def __enter__(self):
		"""This class can be used as a context manager. See :meth:`NodeVM.code`.
		"""
		return self
		
	def __exit__(self, exc_type, exc_value, tracback):
		"""The VM will be closed if:
		
		1. This method is called.
		2. The module is created by :meth:`NodeVM.code`.
		"""
		if self.CLOSE_ON_EXIT:
			self.vm.close()
			
def eval(code, **options):
	"""A shortcut to eval JavaScript.
	
	This function will create a :class:`VM`, run code, and return the result.
	"""
	with VM(**options) as vm:
		return vm.run(code)
