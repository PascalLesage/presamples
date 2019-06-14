.. _quickstart:

Quickstart
==========

This section provides a brief overview of the use of presamples via a simple example:

* :ref:`objectives`
* :ref:`simple_example`
* :ref:`creating_presamples`
* :ref:`accessing_package`
* :ref:`using_package`
* :ref:`storing_model_results`
* :ref:`storing_resource`
* :ref:`seeded_indexers`
* :ref:`sequential_indexers`
* :ref:`override_parameter_values`
* :ref:`managing_using_campaigns`


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
----------------------------

Presamples was written to meet two specific needs:
- the need to store and provide access to arrays of data that are inputs to a model;
- the need to have a flexible data hierarchy so that some arrays can be replaced
by other arrays when running a model.

Presamples is used to write, load, manage and verify *presample arrays*, which are
simply arrays of values specific parameters can take. These are stored in
*presample packages*, which are based on the `datapackage standard <https://frictionlessdata.io/specs/data-package/>`_
by the `Open Knowledge Foundation <https://okfn.org/projects/>`_.

These presample arrays can be based on any source:

  - Measured data;
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


.. _simple_example:

Simple example: Fertilizer inputs to cereal production in Canada
----------------------------------------------------------------
For illustration, let's suppose you have a simple model that calculates the amount of fertilizer used to grow
1 kg of cereals in Canada. The model has three inputs:

  - Total amount of fertilizers used per km2 for a given year
  - The total land under cultivation for the same year
  - The total output of cereals for the same year

The model is simply:

.. code-block:: python

  >>> def fert_per_kg(fert_kg_per_km2, land_ha, cereal_t):
  ...     return fert_kg_per_km2 * (land_ha / 100) / (cereal_t / 1000)


The following data, stored as arrays, were collected for years 2003-2015 from the
`World Bank website <https://data.worldbank.org/>`_:

.. code-block:: python

    >>> import numpy as np

    # Cereal production, in metric tons
    >>> cereal_production_array = np.array(
    ...     [
    ...         49197200, 50778200, 50962400, 48577300, 48005300, 56030400,
    ...         49691900, 45793400, 47667200, 51799100, 66405701, 51535801, 53361100
    ...     ], dtype=np.int64
    ... )

    # Fertilizer consumption, in kg/km^2
    >>> fertilizer_consumption_array = np.array(
    ...     [57.63016664,   58.92761065,   54.63277483,   61.82127866,   46.99494591,
    ...      68.60414475,   63.96407104,   62.20875736,   62.26266793,   77.0963275 ,
    ...      94.15242211,   96.13617882,   115.82229301
    ...     ], dtype=np.float64
    ... )
    # Land used for cereal production, in hectares
    >>> land_for_cereals_array = np.array(
    ...     [
    ...         17833000, 16161700, 15846800, 15946100, 16145100, 16519700,
    ...         15060300, 13156000, 13536700, 14981496, 15924684, 14023084, 14581100
    ...     ], dtype=np.int64
    ... )

.. _creating_presamples:

Creating presample packages for data inputs
-------------------------------------------

Presamples packages for named parameters are created using ``create_presamples_package``.

The input data need to be formatted as a list of ``(samples, names, label)``, where:
  - ``samples`` are arrays containing *n* observations (columns) for *m* named parameters (rows)
  - ``names`` are a list of m parameter names
  - ``label`` is simply a tag to name the set of data being passed.

To format the agricultural data above:

.. code-block:: python

    # Stack arrays of data.
    # The number of columns equals the number of observations
    # The number of rows equals the number of parameters
    >>> ag_sample_arr = np.stack(
    ...     [
    ...         cereal_production_array,
    ...         fertilizer_consumption_array,
    ...         land_for_cereals_array
    ...     ], axis=0
    ... )

    # Create a list of your parameter names
    >>> ag_names = ['cereal production [t]', 'fert consumption [kg/km2]', 'land [ha]']


The presample package can now be created:

.. code-block:: python

    >>> import presamples

    >>> pp_id, pp_path = presamples.create_presamples_package(
    ...     parameter_data = [(ag_sample_arr, ag_names, "Agri baseline data")]
    ... )

This function does several things:

1) It stores the samples to a numpy array and the parameter names as a json file to disk, at the location ``pp_path``
2) It generates a file ``datapackage.json`` that contains metadata on the presamples package.

The datapackage has the following structure:

.. code-block:: json

    {
      "name": "f53d306db86a41d79e68d2181ca32bea",
      "id": "f53d306db86a41d79e68d2181ca32bea",
      "profile": "data-package",
      "seed": null,
      "resources": [
        {
          "samples": {
            "filepath": "f53d306db86a41d79e68d2181ca32bea.0.samples.npy",
            "md5": "58978441f250cadca1d5829110d23942",
            "shape": [
              3,
              13
            ],
            "dtype": "float64",
            "format": "npy",
            "mediatype": "application/octet-stream"
          },
          "names": {
            "filepath": "f53d306db86a41d79e68d2181ca32bea.0.names.json",
            "md5": "c2202d5f8fd5fd9eb11e3cd528b6b14d",
            "format": "json",
            "mediatype": "application/json"
          },
          "profile": "data-resource",
          "label": "Canadian ag data from World Bank",
          "index": 0
        }
      ],
      "ncols": 13
    }

See the :ref:`tech_ref` for more detail and for a list of other arguments.

.. _accessing_package:

Accessing all data in a presamples package
---------------------------------------------

One way to interact with the presamples package is via the ``PresamplesPackage`` package interface:

.. code-block:: python

    >>> package = presamples.PresamplesPackage(pp_path)

The package can return multiple properties, such as:

  - information contained in datapackage.json (``package.metadata``)
  - a ParametersMapping object (``package.parameters``), which can be used to access parameter names (keys), presample arrays (values) or both (items):

.. code-block:: python

    >>> names = list(package.parameters.keys())
    ['cereal production [t]', 'fert consumption [kg/km2]', 'land [ha]']

    >>> list(package.parameters.values()) # Note that the arrays are memory mapped
     [memmap([49197200., 50778200., 50962400., 48577300., 48005300., 56030400.,
              49691900., 45793400., 47667200., 51799100., 66405701., 51535801.,
              53361100.]),
     memmap([ 57.63016664,  58.92761065,  54.63277483,  61.82127866,
              46.99494591,  68.60414475,  63.96407104,  62.20875736,
              62.26266793,  77.0963275 ,  94.15242211,  96.13617882,
              115.82229301]),
     memmap([17833000., 16161700., 15846800., 15946100., 16145100., 16519700.,
             15060300., 13156000., 13536700., 14981496., 15924684., 14023084.,
             14581100.])]

     >>> {k:v for k, v in package.parameters.items()}
     {'cereal production [t]': memmap([49197200., 50778200., 50962400., 48577300., 48005300., 56030400.,
             49691900., 45793400., 47667200., 51799100., 66405701., 51535801.,
             53361100.]),
     'fert consumption [kg/km2]': memmap([ 57.63016664,  58.92761065,  54.63277483,  61.82127866,
              46.99494591,  68.60414475,  63.96407104,  62.20875736,
              62.26266793,  77.0963275 ,  94.15242211,  96.13617882,
             115.82229301]),
     'land [ha]': memmap([17833000., 16161700., 15846800., 15946100., 16145100., 16519700.,
             15060300., 13156000., 13536700., 14981496., 15924684., 14023084.,
             14581100.])}

You can also access a specific array directly from the parameter name:

.. code-block:: python

    >>> package.parameters['land [ha]']
    memmap([17833000., 16161700., 15846800., 15946100., 16145100., 16519700.,
            15060300., 13156000., 13536700., 14981496., 15924684., 14023084.,
            14581100.])


.. _using_package:

Accessing single samples in a presamples package
-------------------------------------------------

It is also possible to access a single observation for each variable rather than returning the entire array of observations.

This is done via the ``PackagesDataLoader``.

A ``PackagesDataLoader`` is instantiated with a list of presamples package paths. In our simple example, we just have one path:

.. code-block:: python

    >>> ag_loader = presamples.PackagesDataLoader([ag_fp])

One of the important things the ``PackagesDataLoader`` does is create an ``Indexer`` for each presamples package. This indexer
simply returns an integer representing the column number of the presamples array from which data will be taken.
By default, the ``Indexer`` returns indices at random (useful for e.g. Monte Carlo simulations). However, it can also return
values sequentially (see :ref:`sequential_indexers`) and can also be seeded (see :ref:`seeded_indexers`).

.. code-block:: python

    >>> for _ in range(4):
    ...     ag_loader.update_sample_indices()
    ...     print("index:", ag_loader.parameters[0].index, "values:", ag_loader.parameters[0].array)
    index: 6 values: [4.9691900e+07 6.3964071e+01 1.5060300e+07]
    index: 5 values: [5.60304000e+07 6.86041448e+01 1.65197000e+07]
    index: 9 values: [5.17991000e+07 7.70963275e+01 1.49814960e+07]
    index: 0 values: [4.91972000e+07 5.76301666e+01 1.78330000e+07]

To use these in our model described in the simple_example_ section:

.. code-block:: python

    >>> for run_nb in range(5): # Run the model 5 times
    ...     print("Run number:", run_nb)
    ...     # Calculate the model output using sampled parameter values
    ...     fertilizer_amount = fert_per_kg(
    ...         fert_kg_per_km2=ag_loader.parameters[0]['fert consumption [kg/km2]'],
    ...         land_ha=ag_loader.parameters[0]['fert consumption [kg/km2]'],
    ...         cereal_t=ag_loader.parameters[0]['cereal production [t]']
    ...         )
    ...     # print the sampled column index and the model output for each run
    ...     print("\tindex:", ag_loader.parameters[0].index)
    ...     print("\tresult:", 	'{:.2e}'.format(fertilizer_amount))
    ...     # Update the index, i.e. move to the next random index
    ...     ag_loader.update_sample_indices()
    Run number: 0
        index: 1
        result: 6.84e-04
    Run number: 1
        index: 2
        result: 5.86e-04
    Run number: 2
        index: 1
        result: 6.84e-04
    Run number: 3
        index: 10
        result: 1.33e-03
    Run number: 4
        index: 3
        result: 7.87e-04

.. _storing_model_results:

Storing a model's output as a presample package
-----------------------------------------------

The calculated model output (kg fertilizer per kg cereal) may be an input to another model. It would be possible to store
this output as another presample package which can then be used directly in that second model.

While this example is simple, it is rather obvious that this can be a great advantage for larger models that take take
a lot of computing resources.

.. code-block:: python

    >>> iterations = 100 # Number of iterations to store.
    >>> model_output = np.zeros(shape=(1, iterations))
    >>> for i in range(iterations):
    ...     model_output[0, i] = fert_per_kg(
    ...         fert_kg_per_km2=ag_loader.parameters[0]['fert consumption [kg/km2]'],
    ...         land_ha=ag_loader.parameters[0]['fert consumption [kg/km2]'],
    ...         cereal_t=ag_loader.parameters[0]['cereal production [t]']
    ...         )
    ...     ag_loader.update_sample_indices()
    >>> ag_result_pp_id, ag_result_pp_fp = presamples.create_presamples_package(
    ...     parameter_data = [(model_output, [''], "Agri model output baseline")]
    ... )

This presample package can then be accessed or used as described above.

.. _storing_resource:

Storing a presample resource
-----------------------------
Presamples allows an easy management of presample packages using ``PresampleResource``.

.. code-block:: python

    >>> pr = presamples.PresampleResource.create(path=pp_path, name="Ag model input data")

The resource has a few useful properties, such as ``name`` and ``path``.

One can then retrieve a presample resource based on the name:

.. code-block:: python

    >>> pr_retrieved = presamples.PresampleResource.get(presamples.PresampleResource.name=="Ag model input data")

and then use the associated presample package:

.. code-block:: python

    >>> new_loader = presamples.PackagesDataLoader([pr_retrieved.path])


.. _seeded_indexers:

Creating presample packages with seeded indexers
----------------------------------------------------

Indexers are by default random. To force the indices to be returned in the same order everytime a presamples package is
used, it is possible to specify a ``seed`` when creating the presamples package. This will ensure repeatability across
uses of the presample package.

Reusing the original data, we simply pass a seed when using ``create_presamples_package``:

.. code-block:: python

    >>> pp_id_seeded, pp_path_seeded = presamples.create_presamples_package(
    ...     parameter_data = [(ag_sample_arr, ag_names, "Agri baseline data")],
    ...     seed=42
    ... )

    # Create a first loader and print indices and values
    >>> ag_loader_seeded_pp = presamples.PackagesDataLoader([ag_fp_seeded])
    >>> for _ in range(4):
    ...     print("index:", ag_loader_seeded.parameters[0].index, "values:", ag_loader_seeded.parameters[0].array)
    ...     ag_loader_seeded.update_sample_indices()
    index: 5 values: [5.60304000e+07 6.86041448e+01 1.65197000e+07]
    index: 10 values: [6.64057010e+07 9.41524221e+01 1.59246840e+07]
    index: 8 values: [4.76672000e+07 6.22626679e+01 1.35367000e+07]
    index: 4 values: [4.80053000e+07 4.69949459e+01 1.61451000e+07]

    # Create a second loader and print indices and values
    >>> ag_loader_seeded_pp_2 = presamples.PackagesDataLoader([ag_fp_seeded])
    >>> for _ in range(4):
    ...     print("index:", ag_loader_seeded_2.parameters[0].index, "values:", ag_loader_seeded_2.parameters[0].array)
    ...     ag_loader_seeded_2.update_sample_indices()
    index: 5 values: [5.60304000e+07 6.86041448e+01 1.65197000e+07]
    index: 10 values: [6.64057010e+07 9.41524221e+01 1.59246840e+07]
    index: 8 values: [4.76672000e+07 6.22626679e+01 1.35367000e+07]
    index: 4 values: [4.80053000e+07 4.69949459e+01 1.61451000e+07]

.. _sequential_indexers:

Creating presample packages with sequential indexers
----------------------------------------------------

It can often be useful to sample values sequentially. To do so, pass ``seed=sequential`` when creating the presamples package.

.. code-block:: python

    >>> pp_id_seq, pp_path_seq = presamples.create_presamples_package(
    ...     parameter_data = [(ag_sample_arr, ag_names, "Agri baseline data")],
    ...     seed='sequential'
    ... )
    >>> ag_loader_seq = presamples.PackagesDataLoader([ag_fp_seq])
    >>> for _ in range(4):
    ...     print("index:", ag_loader_seq.parameters[0].index, "values:", ag_loader_seq.parameters[0].array)
    ...     ag_loader_seq.update_sample_indices()
    index: 0 values: [4.91972000e+07 5.76301666e+01 1.78330000e+07]
    index: 1 values: [5.07782000e+07 5.89276106e+01 1.61617000e+07]
    index: 2 values: [5.09624000e+07 5.46327748e+01 1.58468000e+07]
    index: 3 values: [4.85773000e+07 6.18212787e+01 1.59461000e+07]



.. _override_parameter_values:

Using presamples to override input values
-----------------------------------------

ON HOLD, See `<https://github.com/PascalLesage/presamples/issues/56>`_

.. _managing_using_campaigns:

Using ``Campaigns`` to manage sets of presample packages
--------------------------------------------------------

ON HOLD until override issue is fixed.