.. _quickstart:

Quickstart
==========

This section provides a brief overview of the use of presamples:
* :ref:`objectives`
* :ref:`creating_presamples`
* :ref:`accessing_package`
* :ref:`storing_resource`
* :ref:`quick_eg_1`
* :ref:`quick_eg_2`


.. note::
    While presamples are application-agnostic, the package was developed in
    the context of the `Brightway2 LCA framework <https://brightwaylca.org/>`_.
    If you are interested in using presamples for LCA and are new to presamples,
    you should move on to :ref:`use_with_bw2` after reading this section.

.. note::
    This section really only provides a brief overview. For a more in-depth presentation
    of the API, read the :ref:`tech_ref` section.
    Also, the examples in this section are minimalistic. For some more concrete examples,
    refer to the :ref:`examples` section.

.. _objectives:

The objectives of presamples
---------------------------

Presamples was written to meet two specific needs:
- the need to store and provide access to arrays of data that are inputs to a model;
- the need to have a flexible data hierarchy so that some arrays can be replaced
by other arrays when running a model.

Presamples is used to write, load, manage and verify *presample arrays*, which are
simply arrays of values specific parameters can take. These are stored in
*presample packages*, which are based on the `datapackage standard <https://frictionlessdata.io/specs/data-package/>`_
by the `Open Knowledge Foundation <https://okfn.org/projects/>`_.

These presample arrays can be based on any source:
  - Time series data from a statistical agency;
  - Array of random values generated from a given distribution;
  - The output from a MonteCarlo Simulation from a model;
  - A hat.

Presamples allows these arrays to be generated *ahead* of their use in a particular model. This is useful if:
  - Generating these values is computationally expensive and there is no need to recalculate them with each model run;
  - We want to reuse the *same* values every time a model is solved.

Also, when multiple presample packages are accessed for a single parameter, only the last
values are used. This allows a baseline model to be modulated with different input
data (scenarios) without actually making changes to the baseline data.


.. _creating_presamples:

Creating presample packages
---------------------------
**THIS SECTION IS UNDER CONSTRUCTION**
**It will contain a super-slim example of presample package creation**


.. code-block:: python

    import presamples
    import numpy as np

    first_data = np.random.rand(3, 100) # Creates a 3 x 100 array of floats [0, 1]
    first_names = ['p1', 'p2', 'p3']

    second_data = np.random.rand(1, 10) # Creates a 3 x 100 array of floats [0, 1]
    second_names = ['p4']

    ps_id, ps_path = presamples.create_presamples_package(
        parameter_data=[
            (first_data, first_names, 'first'),
            (second_data, second_names, 'second'),
        ]
    )




.. _accessing_package:

Accessing a presamples package
------------------------------
**THIS SECTION IS UNDER CONSTRUCTION**
**It will contain a super-slim example of accessing a package**

.. code-block:: python

    package = presamples.PresamplesPackage(ps_path)
    ...


.. _storing_resource:

Storing a presample resource
---------------------------
**THIS SECTION IS UNDER CONSTRUCTION**
**It will contain a super-slim example of saving the package to resources and some of the main resource properties**


.. code-block:: python

    pass


.. _managing_using_campaigns:

Managing resources using campaigns
----------------------------------
**THIS SECTION IS UNDER CONSTRUCTION**
**It will contain a super-slim example of creating a campaign, and using campaigns to load presample arrays**


.. _quick_eg_1:

Quick sample use 1: reuse of random samples
-------------------------------------------
**THIS SECTION IS UNDER CONSTRUCTION**


.. _quick_eg_2:

Quick sample use 2: storing scenario data
-----------------------------------------
**THIS SECTION IS UNDER CONSTRUCTION**
