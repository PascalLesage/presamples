.. _installing:

Installing
==========

Installing with pip
----------------------------------

The presamples package is hosted `on Pypi <https://pypi.org/project/presamples/>`_ and can be installed using pip:

.. code-block:: console

    pip install presamples

Installing with conda
------------------------------------

The presamples package is hosted on a conda channel and can be installed using conda:

.. code-block:: console

    conda install --channel pascallesage presamples

Install from github
-----------------------------------

The latest version of the presamples package is hosted on `github <https://github.com/PascalLesage/presamples/>`_ and can be installed
using pip:



.. code-block:: console


    https://github.com/PascalLesage/presamples/archive/master.zip
    git clone https://github.com/PascalLesage/presamples.git
    cd presamples
    python setup.py install

.. note::
    On some systems you may need to use ``sudo python setup.py install`` to
    install presamples system-wide.


Brightway2 dependencies and integration
----------------------------------------

Presamples was initially developed to work with the `Brightway2 LCA framework
<https://brightwaylca.dev//>`_ and hence inherits some requirements from that framework.
While it is possible to use with presamples without ever using Brightway, these
dependencies still get installed. They won't be a bother, though.

.. note::
   If you *do* want to use presamples with Brightway2, then great!
   You'll find many classes and methods that will take your LCA game
   to the next level. Make sure you have Brightway2 installed in your
   environment, see `here<https://docs.brightwaylca.dev/installation.html>`_ for
   more details.
