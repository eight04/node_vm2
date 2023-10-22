.. automodule:: node_vm2
   :show-inheritance:

   node_vm2
   ========

   A Python 3 to Node.js + vm2 binding, helps you execute JavaScript safely.
   
   Also checkout `node_vm2's readme <https://github.com/eight04/node_vm2>`_.

   .. warning::
      This project is no longer maintained. Please use `deno_vm <https://github.com/eight04/deno_vm>`__ instead.
   
   Functions
   ---------
   
   .. autofunction:: eval
   
   Classes
   -------
   
   .. autoclass:: BaseVM
      :members: __enter__, __exit__, create, destroy
   
   .. autoclass:: VM
      :members: run, call
   
   .. autoclass:: NodeVM
      
      .. autoattribute:: event_que
         :annotation: = queue.Queue()
         
      .. automethod:: run
      .. automethod:: code
   
   .. autoclass:: NodeVMModule
      :members: __enter__, __exit__, call, get, call_member, get_member, destroy
   
   .. autoclass:: VMServer
      :members: __enter__, __exit__, start, close
   
