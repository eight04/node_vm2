#! python3

from io import StringIO
from unittest import TestCase, main
from unittest.mock import patch
from node_vm2 import eval, VM, NodeVM, VMError

class Main(TestCase):
	def test_eval(self):
		with self.subTest("one line eval"):
			r = eval("'foo' + 'bar'")
			self.assertEqual(r, "foobar")
			
		with self.subTest("multiline"):
			r = eval("""
				var foo = x => x + 'bar';
				foo('foo');
			""")
			self.assertEqual(r, "foobar")
			
	def test_VM(self):
		with self.subTest("create VM"):
			vm = VM().create()
			r = vm.run("'foo' + 'bar'")
			vm.destroy()
			self.assertEqual(r, "foobar")
			
		with self.subTest("with statement"):
			with VM() as vm:
				r = vm.run("'foo' + 'bar'")
				self.assertEqual(r, "foobar")
				
	def test_NodeVM(self):
		with self.subTest("create NodeVM"):
			vm = NodeVM().create()
			m = vm.run("exports.foo = 'foo'")
			r = m.get_member("foo")
			self.assertEqual(r, "foo")
			vm.destroy()
			
		with self.subTest("with statement"):
			with NodeVM() as vm:
				m = vm.run("exports.foo = 'foo'")
				r = m.get_member("foo")
				self.assertEqual(r, "foo")
				
		with self.subTest("NodeVM.code()"):
			with NodeVM.code("exports.foo = 'foo'") as m:
				r = m.get_member("foo")
				self.assertEqual(r, "foo")
				
	def test_VMError(self):
		with self.assertRaisesRegex(VMError, "foo"):
			eval("throw new Error('foo')")

		# doesn't inherit Error
		with self.assertRaisesRegex(VMError, "foo"):
			eval("throw 'foo'");
			
	def test_console(self):
		code = "exports.test = s => console.log(s)"
		with NodeVM.code(code) as module:
			with patch("sys.stdout", new=StringIO()) as out:
				module.call_member("test", "Hello")
				self.assertEqual(out.getvalue(), "Hello\n")
				
		# redirect and event
		with NodeVM.code(code, console="redirect") as module:
			module.call_member("test", "Hello")
			event = module.vm.event_que.get_nowait()
			self.assertEqual(event["value"], "Hello")
			
main()
