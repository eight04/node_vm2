node_vm2
========

.. image:: https://api.codacy.com/project/badge/Grade/fb30c7193b6b43cf818457e3ff23e60c
   :target: https://www.codacy.com/app/eight04/node_vm2?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=eight04/node_vm2&amp;utm_campaign=Badge_Grade

.. image:: https://readthedocs.org/projects/node-vm2/badge/?version=latest
   :target: http://node-vm2.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
   
.. image:: https://travis-ci.org/eight04/node_vm2.svg?branch=master
   :target: https://travis-ci.org/eight04/node_vm2
   
.. image:: https://david-dm.org/eight04/node_vm2/status.svg?path=node_vm2/vm-server
   :target: https://david-dm.org/eight04/node_vm2?path=node_vm2/vm-server
   :alt: dependencies Status

A Python 3 to Node.js + vm2 binding, helps you execute JavaScript safely.

vm2
---

`vm2 <https://github.com/patriksimek/vm2>`__ is a node module to create **real** sandbox in node. The official node API `vm <https://nodejs.org/api/vm.html>`__, can only create isolate context and doesn't prevent harmful code to damage your computer.

How it works
------------

The module launchs a Node.js REPL server, which can be communicated with JSON. All JavaScript code are encoded in JSON and sent to the server. After the server executing the code in vm2, the result is sent back to Python.

Install
-------

You need Node.js.

https://nodejs.org/

Install node_vm2 from pypi wheel.

.. code-block::

   pip install node_vm2

Also make sure you have ``node`` executable in ``PATH``, or you can specify the executable with environment variable ``NODE_EXECUTABLE``.

Additionally, you will need ``npm`` to build node_vm2 from source.

Usage
-----

Most of the APIs are bound to `vm2 <https://github.com/patriksimek/vm2>`__.

Simple eval:

.. code-block:: python

   from node_vm2 import eval
   
   print(eval("['foo', 'bar'].join()"))
   
Use VM:

.. code-block:: python

   from node_vm2 import VM
   
   with VM() as vm:
      vm.run("""
         var sum = 0, i;
         for (i = 0; i < 10; i++) sum += i;
      """)
      print(vm.run("sum"))
      
Use NodeVM:

.. code-block:: python

   from node_vm2 import NodeVM
   
   js = """exports.greet = name => console.log(`Hello ${name}!`);"""
   
   with NodeVM.code(js) as module:
      module.call_member("greet", "John")
      
It is possible to do async task with Promise:

.. code-block:: python

   from datetime import datetime
   from node_vm2 import NodeVM

   js = """
   exports.test = () => {
      return new Promise(resolve => {
         setTimeout(() => {
            resolve("hello")
         }, 3000);
      });
   };
   """
   with NodeVM.code(js) as module:
      print(datetime.now())
      print(module.call_member("test"))
      print(datetime.now())
      
If you like to allow the VM to crash your server (e.g. ``process.exit()``), you should create the VM in a separate server so it won't affect other VMs:

.. code-block:: python

   from node_vm2 import VMServer, VM

   with VMServer() as server:
      with VM(server=server) as vm:
         # now the vm is created in a new server
         print(vm.run("1 + 2 + 3"))

API reference
-------------

http://node-vm2.readthedocs.io/

Changelog
---------

-  0.3.6 (Apr 22, 2019)

   -  Update vm2 to 3.8.0. Fix security issues.

-  0.3.5 (Feb 10, 2019)

   -  Update vm2 to 3.6.10. Fix security issues.

-  0.3.4 (Aug 10, 2018)

   -  Update vm2 to 3.6.3. Fix security issues.

-  0.3.3 (Jul 23, 2018)

   -  Fix: don't bundle dev dependencies.

-  0.3.2 (Jul 23, 2018)

   -  Fix: getting a freezed object would crash the server.
   -  Update vm2 to 3.6.2. Fix security issues.

-  0.3.1 (Apr 25, 2017)
   
   -  Add ``command`` arg to ``VMServer``.
   -  Fix: A dead default server is created if process spawning failed.

-  0.3.0 (Apr 23, 2017)

   -  **Change: use event queue to handle console redirects.**
   -  Reconize object thrown by VM which doesn't inherit built-in Error.

-  0.2.0 (Mar 25, 2017)

   -  **Drop NodeBridge.**
   -  Add VMServer.
   -  **Make all VMs share a default VMServer.**
   -  **Method rename: VM.connect -> VM.create, VM.close -> VM.destroy.**

-  0.1.0 (Mar 23, 2017)

   -  First release
   