.. _quickstart:

Quickstart
==========

This section provides a brief overview of the use of presamples for named parameters via a simple example.

* :ref:`objectives`
* :ref:`simple_example`
* :ref:`creating_presamples`
* :ref:`accessing_package`
* :ref:`loading_package`
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

To create a presamples package for the input data described above:

.. code-block:: python

    >>> import presamples

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

    >>> pp_id, pp_path = presamples.create_presamples_package(
    ...     parameter_data = [(ag_sample_arr, ag_names, "Agri baseline data")],
    ...     name="Baseline agri data - presample package"
    ... )

This function does several things:

1) It stores the samples to a numpy array and the parameter names as a json file to disk, at the location ``pp_path``
2) It generates a file ``datapackage.json`` that contains metadata on the presamples package.

.. code-block:: python

    >>> import os
    >>> os.listdir(pp_path)
    ['datapackage.json',
     'dbc8f4abb93540f9a1ab040b8923672f.0.names.json',
     'dbc8f4abb93540f9a1ab040b8923672f.0.samples.npy']

The datapackage has the following structure:

.. code-block:: python

    >>> import json
    >>> with open(pp_path/'datapackage.json', 'rb') as f:
    ...     datapackage = json.load(f)
    >>> print(json.dumps(datapackage, indent=4))
    {
        "name": "Baseline agri data - presample package",
        "id": "dbc8f4abb93540f9a1ab040b8923672f",
        "profile": "data-package",
        "seed": null,
        "resources": [
            {
                "samples": {
                    "filepath": "dbc8f4abb93540f9a1ab040b8923672f.0.samples.npy",
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
                    "filepath": "dbc8f4abb93540f9a1ab040b8923672f.0.names.json",
                    "md5": "c2202d5f8fd5fd9eb11e3cd528b6b14d",
                    "format": "json",
                    "mediatype": "application/json"
                },
                "profile": "data-resource",
                "label": "Agri baseline data",
                "index": 0
            }
        ],
        "ncols": 13
    }

See the :ref:`tech_ref` for more detail and for a list of other arguments.

.. _accessing_package:

Direct interface to presamples package
---------------------------------------------

To interact directly with a single presamples package :

.. code-block:: python

    >>> package = presamples.PresamplesPackage(pp_path)

The entire content of the ``datapackage.json`` file is returned by ``package.metadata``.

The package can also be used to directly return several properties contained in the datapackage, for example:

.. code-block:: python

    >>> package.name  # Name passed as optional argument in ``create_presamples_package``
    'Agri example - baseline data'

    >>> package.ncols # Number of columns, i.e. number of observations stored in the presamples array
    13

    >>> package.id
    '2a31aa637f564618bf5e606333ffb7fc'

Accessing the package's ``resources`` provides metadata on the stored data and filepaths to access it.
``packages.resources`` returns a list with as many resources as were passed in ``create_presamples_package``. In our
simple example, only one set of parameter data was passed, so ``packages.resources`` only contains one element.

.. code-block:: python

    >>> package.resources # List of resources, in simple example there is one
    [{'samples': {'filepath': 'dbc8f4abb93540f9a1ab040b8923672f.0.samples.npy',
       'md5': '58978441f250cadca1d5829110d23942',
       'shape': [3, 13],
       'dtype': 'float64',
       'format': 'npy',
       'mediatype': 'application/octet-stream'},
      'names': {'filepath': 'dbc8f4abb93540f9a1ab040b8923672f.0.names.json',
       'md5': 'c2202d5f8fd5fd9eb11e3cd528b6b14d',
       'format': 'json',
       'mediatype': 'application/json'},
      'profile': 'data-resource',
      'label': 'Agri baseline data',
      'index': 0}]

The PresamplesPackage also provides a ``ParametersMapping`` interface to access named parameter data:

.. code-block:: python

    >>> package.parameters
    <presamples.package_interface.ParametersMapping at 0x2136d4de5f8>

    >>> list(package.parameters.keys())
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

You can also get a specific array directly from the parameter name:

.. code-block:: python

    >>> package.parameters['land [ha]']
    memmap([17833000., 16161700., 15846800., 15946100., 16145100., 16519700.,
            15060300., 13156000., 13536700., 14981496., 15924684., 14023084.,
            14581100.])

Note that the values from **all** columns are returned, which makes the ``PresamplePackages`` a useful interface
for models that accept arrays as inputs:

.. code-block:: python

    >>> fert_per_kg(
            fert_kg_per_km2=package.parameters['fert consumption [kg/km2]'],
            land_ha=package.parameters['land [ha]'],
            cereal_t=package.parameters['cereal production [t]']
        )
    array([208.89781567, 187.55496749, 169.88106058, 202.93599925,
           158.05298607, 202.26874876, 193.85817388, 178.71973075,
           176.8157259 , 222.98038423, 225.78597129, 261.59013441,
           316.48831014])

.. _loading_package:

Loading packages for use one column at a time
---------------------------------------------

Presamples also allows accessing parameter data one observation at a time. This is useful to feed data from the presample
arrays in Monte Carlo Simulations.

This is done via the ``PackagesDataLoader``. A ``PackagesDataLoader`` is instantiated with a list of presamples package
paths. In our simple example, we just have one path:

.. code-block:: python

    >>> ag_loader = presamples.PackagesDataLoader([pp_path])

One of the important things the ``PackagesDataLoader`` does in create an ``Indexer`` for each presamples package. This indexer
simply returns an integer representing the column number of the presamples array from which data should be taken.
By default, the ``Indexer`` returns indices at random. An ``Indexer`` can also be seeded for reproducibility (see
:ref:`seeded_indexers`), and can also return values sequentially (see :ref:`sequential_indexers`).

The ``PackagesDataLoader`` has an interface to access named parameters, one observation at a time:

.. code-block:: python

    >>> ag_loader.parameters['land [ha]']
    17833000.0

It is also possible to return values for all parameters using the ``consolidated_arrays`` property:

.. code-block:: python

    >>> ag_loader.parameters.consolidated_array
    array([4.91972000e+07, 5.76301666e+01, 1.78330000e+07])

The order of the values is identical to the order of names:
.. code-block:: python

    >>> ag_loader.parameters.names
    ['cereal production [t]', 'fert consumption [kg/km2]', 'land [ha]']


The array is considered "consolidated" because it uses values from all packages passed to the ``PackagesDataLoader``. In
this simple example, only one was passed, so not much was consolidated, but the interest of consolidating is explained in
:ref:`override_parameter_values`.

To move to the next (random) observation:

.. code-block:: python

    >>> ag_loader.update_package_indices()
    >>> ag_loader.parameters.consolidated_array
    array([5.33611000e+07, 1.15822293e+02, 1.45811000e+07])

The index value of each package's ``Indexer`` can be returned using the ``consolidated_index``:

.. code-block:: python

    >>> for _ in range(4):
    ...     print(
    ...         "indices:",
    ...         ag_loader.parameters.consolidated_indices,
    ...         "values:",
    ...         ag_loader.parameters.consolidated_array
    ...     )
    ...     ag_loader.update_package_indices() # Move to the next (random) index
    indices: [12, 12, 12] values: [5.33611000e+07 1.15822293e+02 1.45811000e+07]
    indices: [8, 8, 8] values: [4.76672000e+07 6.22626679e+01 1.35367000e+07]
    indices: [5, 5, 5] values: [5.60304000e+07 6.86041448e+01 1.65197000e+07]
    indices: [0, 0, 0] values: [4.91972000e+07 5.76301666e+01 1.78330000e+07]

The indices are all the same because the ``PackagesDataLoader`` was populated with a single presamples package.

To use these in our model described in the simple_example_ section:

.. code-block:: python

    >>> for run_nb in range(5): # Run the model 5 times
    ...     print("Run number:", run_nb)
    ...
    ...     # Update the index, i.e. move to the next random index
    ...     ag_loader.update_package_indices()
    # Calculate the model output using sampled parameter values
    ...     fertilizer_amount = fert_per_kg(
    ...         fert_kg_per_km2=ag_loader.parameters['fert consumption [kg/km2]'],
    ...         land_ha=ag_loader.parameters['fert consumption [kg/km2]'],
    ...         cereal_t=ag_loader.parameters['cereal production [t]']
    ...         )
    ...     # print the sampled column index and the model output for each run
    ...     print("\tindices:", ag_loader.parameters.consolidated_indices)
    ...     print("\tresult:", 	'{:.2e}'.format(fertilizer_amount))
    Run number: 0
        indices: [1, 1, 1]
        result: 6.84e-04
    Run number: 1
        indices: [4, 4, 4]
        result: 4.60e-04
    Run number: 2
        indices: [9, 9, 9]
        result: 1.15e-03
    Run number: 3
        indices: [5, 5, 5]
        result: 8.40e-04
    Run number: 4
        indices: [9, 9, 9]
        result: 1.15e-03

.. _storing_model_results:

Storing a model's output as a presample package
-----------------------------------------------

The calculated model output (in the example, kg fertilizer per kg cereal) may be an input to another model.
It would be possible to store the calculated output of our model as yet another presample package, and to use this
directly in the other model.

While this example is simple, it is rather obvious that this can be a great advantage for larger models that take take
a lot of computing resources.

.. code-block:: python

    >>> iterations = 100 # Number of iterations to store.
    >>> model_output = np.zeros(shape=(1, iterations))
    >>> for i in range(iterations):
    ...     ag_loader.update_package_indices()
    ...     model_output[0, i] = fert_per_kg(
    ...         fert_kg_per_km2=ag_loader.parameters['fert consumption [kg/km2]'],
    ...         land_ha=ag_loader.parameters['fert consumption [kg/km2]'],
    ...         cereal_t=ag_loader.parameters['cereal production [t]']
    ...     )
    >>> model_output
    array([[0.00133493, 0.00078676, 0.00081327, ..., 0.00078676, 0.00058567,
            0.00084508  ]])

    >>> ag_result_pp_id, ag_result_pp_fp = presamples.create_presamples_package(
    ...     parameter_data = [(model_output, ['fert_input_per_kg_cereal'], "Agri model output baseline")],
            name="baseline_model_output"
    ... )

This presample package can then be accessed or used as described above.

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

We can test that this worked by creating two ``PackagesDataLoader`` objects and making sure they return samples in the
same order:

.. code-block:: python

    # Create a first loader and print indices and values
    >>> ag_loader_seeded_1 = presamples.PackagesDataLoader([ag_fp_seeded])
    >>> ag_loader_seeded_2 = presamples.PackagesDataLoader([ag_fp_seeded])
    >>> ag_loader_seeded_1 is ag_loader_seeded_2
    False
    >>> ag_loader_seeded_1 == ag_loader_seeded_2
    False

The two loaders are distinct, and yet:

    >>> for _ in range(4):
    ...     ag_loader_seeded_1.update_package_indices()
    ...     print(
    ...         "indices:",
    ...         ag_loader_seeded_1.parameters.consolidated_indices,
    ...         "values:",
    ...         ag_loader_seeded_1.parameters.consolidated_array
    ...     )
    indices: [5, 5, 5] values: [5.60304000e+07 6.86041448e+01 1.65197000e+07]
    indices: [10, 10, 10] values: [6.64057010e+07 9.41524221e+01 1.59246840e+07]
    indices: [8, 8, 8] values: [4.76672000e+07 6.22626679e+01 1.35367000e+07]
    indices: [4, 4, 4] values: [4.80053000e+07 4.69949459e+01 1.61451000e+07]

    >>> for _ in range(4):
    ...     ag_loader_seeded_2.update_package_indices()
    ...     print(
    ...         "indices:",
    ...         ag_loader_seeded_2.parameters.consolidated_indices,
    ...         "values:",
    ...         ag_loader_seeded_2.parameters.consolidated_array
    ...     )
    indices: [5, 5, 5] values: [5.60304000e+07 6.86041448e+01 1.65197000e+07]
    indices: [10, 10, 10] values: [6.64057010e+07 9.41524221e+01 1.59246840e+07]
    indices: [8, 8, 8] values: [4.76672000e+07 6.22626679e+01 1.35367000e+07]
    indices: [4, 4, 4] values: [4.80053000e+07 4.69949459e+01 1.61451000e+07]

.. _sequential_indexers:

Creating presample packages with sequential indexers
-----------------------------------------------------

It can often be useful to sample values sequentially. To do so, pass ``seed=sequential`` when creating the presamples package.

.. code-block:: python

    >>> pp_id_seq, pp_path_seq = presamples.create_presamples_package(
    ...     parameter_data = [(ag_sample_arr, ag_names, "Agri baseline data")],
    ...     seed='sequential'
    ... )
    >>> ag_loader_seq = presamples.PackagesDataLoader([ag_fp_seq])
    >>> for _ in range(4):
    ...     print(
    ...         "indices:",
    ...         ag_loader_seq.parameters.consolidated_indices,
    ...         "values:",
    ...         ag_loader_seq.parameters.consolidated_array
    ...     )
    ...     ag_loader_seq.update_package_indices()
    indices: [0, 0, 0] values: [4.91972000e+07 5.76301666e+01 1.78330000e+07]
    indices: [1, 1, 1] values: [5.07782000e+07 5.89276106e+01 1.61617000e+07]
    indices: [2, 2, 2] values: [5.09624000e+07 5.46327748e+01 1.58468000e+07]
    indices: [3, 3, 3] values: [4.85773000e+07 6.18212787e+01 1.59461000e+07]


.. _override_parameter_values:

Using presamples to override input values
-----------------------------------------

Multiple presamples packages can be passed to a single ``DataPackageLoader``. When a named parameted is present in more
than one presamples package, only the value in the last package to have the named parameter is used.  This allows for
easily updating input data.

In our example, say we want to fix the fertilizer use parameter to an amount representing a specific scenario:

.. code-block:: python

    >>> new_fertilizer_amount = np.array([60]).reshape(1,1) # The array MUST have one row, as we only have one parameter
    >>> fert_scenario_id, fert_scenario_path = presamples.create_presamples_package(
    ...     parameter_data=[new_fertilizer_amount, ['fert consumption [kg/km2]'], 'ag scenario 1']),
    ...     name="Scenario 1 agri data - presample package"
    ... )

We can now create a loader where both the baseline and the scenario packages are passed:

.. code-block:: python

    >>> ag_loader_scenario = presamples.PackagesDataLoader([pp_path, fert_scenario_loader])

We can see that the original values for fertilizer use have been replaced by those in the new package.

.. code-block:: python

    >>> for _ in range(4):
    ...     print(
    ...         "indices:",
    ...         ag_loader_scenario.parameters.consolidated_indices,
    ...         "values:",
    ...         ag_loader_scenario.parameters.consolidated_array
    ...     )
    ...     ag_loader_scenario.update_package_indices()
    indices: [6, 0, 6] values: [4.96919e+07 6.00000e+01 1.50603e+07]
    indices: [11, 0, 11] values: [5.1535801e+07 6.0000000e+01 1.4023084e+07]
    indices: [1, 0, 1] values: [5.07782e+07 6.00000e+01 1.61617e+07]
    indices: [11, 0, 11] values: [5.1535801e+07 6.0000000e+01 1.4023084e+07]

Notice that the index for the second parameter ('fert consumption [kg/km2]') is always 0: this is because the package
for this named parameter only has one column.

You can pass as many packages as required, and each package can have any number of named parameters and observations
(columns).

.. important::
  When passing multiple presamples package paths to a single ``DataPackageLoader``, named parameters get their values and
  indices from the last presamples package that contains data on this named parameter.


.. _storing_resource:

Storing a presample resource
-----------------------------
In order to facilitate their retrieval for reuse, references to presamples packages can be stored in a database
``campaigns.db``. Interaction with this database is based on the `Peewee ORM <http://docs.peewee-orm.com/en/latest/>`_.

The first table of this database is the ``PresampleResource`` table, used to store references to presamples packages.

To store a reference to a presample package in the database:

.. code-block:: python

    >>> pr_baseline = presamples.PresampleResource.create(
    ...     name="Baseline agri data",
    ...     path=pp_path
    ... )

The resource has a few useful properties, such as ``name`` and ``path``.

One can then retrieve a presample resource based on the name:

.. code-block:: python

    >>> pr_baseline_retrieved = presamples.PresampleResource.get(
    ...     presamples.PresampleResource.name=="Baseline agri data"
    ... )
    >>> pr_baseline == pr_baseline_retrieved
    True

and then use the associated presample package:

.. code-block:: python

    >>> other_loader = presamples.PackagesDataLoader([pr_baseline.path])


.. _managing_using_campaigns:

Using ``Campaigns`` to manage sets of presample packages
--------------------------------------------------------

The ``Campaign`` database also has a table called ``Campaign``, used to store information about ordered collections
of ``PresampleResources``.

To create a new campaign:

.. code-block:: python

    >>> ag_campaign_baseline = presamples.Campaign.create(name="Agricultural baseline campaign")
    >>> ag_campaign_baseline.save()
    1

The 1 indicates that one row was changed in the ``Campaign`` table.

We can add our samples of baseline values using the ``PresampleResource`` that was created earlier:

.. code-block:: python

    >>> ag_campaign_baseline.add_presample_resource(pr_baseline)

    >>> ag_campaign_baseline #Get some information on the campaign
    <Campaign: Campaign Agricultural baseline campaign with no parent and 1 packages>

    >>> [p.name for p in ag_campaign_baseline.packages] # List packages used in campaign
    ['Baseline agri data']

A ``Campaign`` can be passed directly to a ``PackagesDataLoader``:

.. code-block:: python

    >>> loader = presamples.PackagesDataLoader(ag_campaign_baseline)
    >>> loader.parameters.consolidated_array
    array([6.64057010e+07, 9.41524221e+01, 1.59246840e+07])

More interestingly, a ``Campaign`` can point to multiple ``PresampleResources`` in the desired order. Let's add the
scenario data we had above to a ``PresampleResource``:

.. code-block:: python

    >>> pr_scenario = presamples.PresampleResource.create(
    ...     path=fert_scenario_path,
    ...     name="Scenario 1 agri data"
    ... )

Next we create a *child* Campaign based on the baseline campaign we created above. This child campaign
will automatically point to all the resources of the parent Campaign. Note that you can have an arbitrary
number of descendents.

.. code-block:: python

    >>> ag_campaign_scenario1 = ag_campaign_baseline.add_child("Agricultural scenario 1 campaign") # Create a child campaign
    >>> ag_campaign_scenario1.save()
    1
    >>> ag_campaign_scenario1.add_presample_resource(pr_scenario) # Add the scenario presample resource

The ``ag_scenario`` ``Campaign`` has the baseline data as parent (it will use all its presample packages) and another
package.

.. code-block:: python

    >>> ag_campaign_scenario1
    <Campaign: Campaign Agricultural scenario 1 campaign with parent Agricultural baseline campaign and 2 packages>

    >>> [p.name for p in ag_campaign_scenario1.ancestors]
    ['Agricultural baseline campaign']

    >>> [p.name for p in ag_campaign_scenario1.packages]
    ['Baseline agri data', 'Scenario 1 agri data']

Using the campaign in a ``PackagesDataLoader`` will call the presample packages in the expected order, i.e. from the
package with baseline data (added first) to the scenario data (added after):

.. code-block:: python

    >>> loader_scenario = presamples.PackagesDataLoader(ag_campaign_scenario1) # Load
    >>> for _ in range(4): # Check values for 4 iterations
    ...     loader_scenario.update_package_indices()
    ...     print(
    ...         "Indices:",
    ...         loader_scenario.parameters.consolidated_indices,
    ...         "Values: ",
    ...         loader_scenario.parameters.consolidated_array
    ...     )
    Indices: [9, 0, 9] Values:  [5.1799100e+07 6.0000000e+01 1.4981496e+07]
    Indices: [6, 0, 6] Values:  [4.96919e+07 6.00000e+01 1.50603e+07]
    Indices: [2, 0, 2] Values:  [5.09624e+07 6.00000e+01 1.58468e+07]
    Indices: [2, 0, 2] Values:  [5.09624e+07 6.00000e+01 1.58468e+07]

The scenario data overwrote the fertiliser use data on each iteration.