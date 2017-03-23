#! python3

from unittest import TestCase, main
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
			vm = VM().connect()
			r = vm.run("'foo' + 'bar'")
			vm.close()
			self.assertEqual(r, "foobar")
			
		with self.subTest("with statement"):
			with VM() as vm:
				r = vm.run("'foo' + 'bar'")
				self.assertEqual(r, "foobar")
				
	def test_NodeVM(self):
		with self.subTest("create NodeVM"):
			vm = NodeVM().connect()
			m = vm.run("exports.foo = 'foo'")
			r = m.get_member("foo")
			self.assertEqual(r, "foo")
			vm.close()
			
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

main()
