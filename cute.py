from xcute import cute, LiveReload, run_task

class Env:
	def __init__(self, task, **env):
		self.task = task
		self.env = env

	def __call__(self, *args):
		import os
		backup = {}
		try:
			for key, value in self.env.items():
				backup[key] = os.environ.get(key, None)
				os.environ[key] = value
			return run_task(self.task, *args)
		finally:
			for key, value in backup.items():
				if value is None:
					del os.environ[key]
				else:
					os.environ[key] = value

class CD:
	"""Change directory, run the task, then change it back"""
	def __init__(self, task, path):
		self.task = task
		self.path = path

	def __call__(self, *args):
		import os
		backup = os.getcwd()
		try:
			os.chdir(self.path)
			return run_task(self.task, *args)
		finally:
			os.chdir(backup)
	
cute(
	pkg_name = "node_vm2",
	lint = [
		'install_npm',
		CD('npm test', 'node_vm2/vm-server'),
		'pylint {pkg_name}'
	],
	install_npm = CD('npm install', 'node_vm2/vm-server'),
	install_npm_prod = CD('npm install --production', 'node_vm2/vm-server'),
	test = ['lint', 'python test.py', 'readme_build'],
	bump_pre = 'test',
	bump_post = ['dist', 'release', 'publish', 'install'],
	dist_pre = [
		'x-clean build dist node_vm2/vm-server/node_modules',
		'install_npm_prod'
	],
	dist = 'python -m build',
	release = [
		'git add .',
		'git commit -m "Release v{version}"',
		'git tag -a v{version} -m "Release v{version}"'
	],
	publish = [
		'twine upload dist/*',
		'git push --follow-tags'
	],
	publish_err = 'start https://pypi.python.org/pypi/{pkg_name}/',
	install = 'pip install -e .',
	readme_build = [
		'rst2html5.py --no-raw --exit-status=1 --verbose '
			'README.rst | x-pipe build/readme/index.html'
	],
	readme_pre = "readme_build",
	readme = LiveReload("README.rst", "readme_build", "build/readme"),
	doc_build = "sphinx-build docs build/docs",
	doc_pre = "doc_build",
	doc = LiveReload(["{pkg_name}", "docs"], "doc_build", "build/docs")
)
