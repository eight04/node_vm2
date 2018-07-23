#! python3

import os
from os import path

from contextlib import contextmanager
from subprocess import run

from setuptools import setup
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop

@contextmanager
def chdir(dest):
	cwd = os.getcwd()
	os.chdir(dest)
	try:
		yield
	finally:
		os.chdir(cwd)

def npm_install(install_lib):
	with chdir(path.join(install_lib, "node_vm2/vm-server")):
		run("npm install", check=True, shell=True)

class install(_install):
	def run(self):
		super().run()
		self.execute(npm_install, [self.install_lib])
		
class develop(_develop):
	def run(self):
		super().run()
		self.execute(npm_install, [os.getcwd()])

if os.environ.get("READTHEDOCS"):
	setup()
else:
	setup(
		cmdclass = {
			"install": install,
			"develop": develop
		}
	)
