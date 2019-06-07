.. _installing:

Installing
==========

Installing with pip
-------------------

The simplest way to install presamples is to pip install the latest version hosted on PyPI:

.. code-block:: console

    pip install presamples


Installing with git
-------------------

The project is hosted at https://github.com/PascalLesage/presamples/ and can be installed
using git:

.. code-block:: console

    git clone https://github.com/PascalLesage/presamples.git
    cd presamples
    python setup.py install

.. note::
    On some systems you may need to use ``sudo python setup.py install`` to
    install presamples system-wide.


Brightway2 dependencies and integration
---------------------

Presamples was initially developed to work with the `Brightway2 LCA framework
<https://brightwaylca.org//>`_ and hence has some requirements from that framework.
While it is possible to use with presamples without ever using Brightway, these
dependencies still get installed. They won't be a bother, though.

.. note::
   If you *do* want to use presamples with Brightway2, then great!
   You'll find many classes and methods that will take your LCA game
   to the next level. Make sure you have Brightway2 installed in your
   environment, see `here<https://docs.brightwaylca.org/installation.html>`_ for
   more details.
