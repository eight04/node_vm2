node_vm2
========

A Python 3 to Node + vm2 binding, to safely execute JavaScript in Python.

Install
-------

You need Node.js first.
https://nodejs.org/

Install from pypi wheel.

.. codeblock::

   pip install node_vm2

Also make sure you have `node` executable in `PATH`, or you can specify the executable with environment variable `NODE_EXECUTABLE`.

Additionally, you will need `npm` to build node_vm2 from source.

Usage
-----

Most of the APIs are compatible with `vm2 <https://github.com/patriksimek/vm2>`.

.. codeblock:: python

   from node_vm2 import VM
   
   with VM() as vm:
      result = vm.run("""
         var sum = 0, i;
         for (i = 0; i < 10; i++) sum += i;
         sum;
      """)
      print(result)
      
API reference
-------------



Changelog
---------

-  Next

   -  First release
   