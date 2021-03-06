.. _tech_ref:

Technical reference
===================
* :ref:`presamplepackagechapter`

   - :func:`presamples.packaging.create_presamples_package`
   - :ref:`parameter_data`
   - :ref:`matrix_data`
   - :ref:`presamplepackagecontent`

      - :ref:`presamplepackagecontent_datapackage`
      - :ref:`presamplepackagecontent_parameters`
      - :ref:`presamplepackagecontent_matrices`

* :ref:`loader`

   - :class:`presamples.loader.PackagesDataLoader`
   - :meth:`presamples.loader.PackagesDataLoader.load_data`
   - :meth:`presamples.loader.PackagesDataLoader.index_arrays`
   - :meth:`presamples.loader.PackagesDataLoader.update_matrices`

.. _presamplepackagechapter:

Presample packages
------------------

Presamples packages are directories that **must** minimally contain a ``datapackage.json`` file, based on the
`datapackage standard <https://frictionlessdata.io/specs/data-package/>`_.
It may contain other files, depending on the types of resources contained in the presamples package.
The file contents are described here :ref:`presamplepackagecontent`.

.. _presamplepackagecreation:

.. autofunction:: presamples.packaging.create_presamples_package

.. _parameter_data:

Description of the ``parameter_data`` argument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``parameter_data`` argument in ``create_presamples_package`` is a list (or other iterable) of tuples containing
the following three objects:

- ``samples``: are a two-dimensional numpy array, where each row contains values for a specific named parameter,
  and columns represent possible values for these parameters. It is possible to have samples arrays with only one column
  (i.e. only one observation for the named parameters), and only one row (data on only one named parameter).
- ``names``: list of parameter names, as strings. The order of the names should be the same as the rows in ``samples``,
  i.e. the first name corresponds to data in the first row of ``samples``.
- ``label``: a string which will be used to name the resource. The presamples package does not presently use this label.


.. important::
   There must necessarily be as many named parameters in ``names`` as there are rows in ``samples``.

.. Note::
   It is possible to pass an arbitrary amount of (``samples``, ``names``, ``label``) tuples in ``parameter_data``.
   Each will be contained in a distinct resource of the presamples package. However,

   1. the names in each tuple *must* be unique, and
   2. the number of columns in each ``samples`` must be identical.

.. hint::
   While there are no restrictions on the string, using strings that are valid names in AST evaluators can prevent
   problems down the line.

.. _matrix_data:

Description of the ``matrix_data`` argument
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``matrix_data`` argument in ``create_presamples_package`` is a list (or other iterable) of tuples containing
the following three objects:

- ``samples``: are a two-dimensional Numpy array, where each row contains values for a specific matrix element that will
  be replaced and each column contains values for a given realization of the LCA model. It is possible to have samples
  arrays with only one column (i.e. only one observation for the matrix elements), and only one row (data on only one
  named parameter).
- ``indices``:  is an iterable with row and (usually) column indices. The *ith* element of indices refers to the *ith*
  row of the samples. The exact format of indices depends on the matrix to be constructed. These indices tell us where
  exactly to insert the samples into a specific matrix.
- ``matrix label``: is a string giving the name of the matrix to be modified in the LCA class. Strings that are
  currently supported are 'technosphere', biosphere' and 'cf'.

.. important::
   The number of rows in ``samples`` and ``indices`` must be identical.

.. Note::
   It is possible to pass an arbitrary amount of (``samples``, ``indices``, ``matrix label``) tuples in
   ``matrix_data``. Each will be contained in a distinct resource of the presamples package. However, the number of
   columns in each ``samples`` must be identical.

.. _presamplepackagecontent:

Presample package contents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _presamplepackagecontent_datapackage:

datapackage.json
::::::::::::::::::

Presample packages are directories that **must** minimally contain a ``datapackage.json`` file, based on the
`datapackage standard <https://frictionlessdata.io/specs/data-package/>`_.
It may contain other files, depending on the types of resources contained in the presamples package.

The format for the datapackage.json file is:

.. code-block::

    {
      "name": str,
      "id": uuid or str,
      "profile": "data-package",
      "seed": Null, int, array_like or "sequential"
      "resources": [],
      "ncols": int
    }

There can be an arbitrary number of resources. Each resource is represented in the datapackage by a dictionary.

.. _presamplepackagecontent_parameters:

Named parameters
:::::::::::::::::

Resources for named parameters have the following format:

.. code-block::

    {
        "samples": {
            "filepath": "{id}.{data package index}.samples.npy",
            "md5": md5 hash,,
            "shape": [
                number of rows,
                number of columns
            ],
            "dtype": "float64",
            "format": "npy",
            "mediatype": "application/octet-stream"
        },
        "names": {
            "filepath": "{id}.{data package index}.names.json",
            "md5": md5 hash,
            "format": "json",
            "mediatype": "application/json"
        },
        "profile": "data-resource",
        "label": parameter label,
        "index": data package index
    }

Where:
- the id is based on the ``\id_`` argument passed to ``create_presamples_package``
- the data package index indicates the position (index) of the resource in the list of resources

.. _presamplepackagecontent_matrices:

Matrices
:::::::::

.. code-block::

    {
        "type": matrix type (technosphere, biosphere, cfs),
        "samples": {
            "filepath": "{id}.{data package index}.samples.npy",
            "md5": md5 hash,
            "shape": [
                number of rows,
                number of columns
            ],
        "dtype": "float32",
        "format": "npy",
        "mediatype": "application/octet-stream"
        },
        "index": data package index,
        "indices": {
            "filepath": "{id}.{data package index}.indices.npy",
            "md5": md5 hash,
            "format": "npy",
            "mediatype": "application/octet-stream"
        },
        "profile": "data-resource",
        "row from label": str, e.g. "input",
        "row to label": str, e.g. "row",
        "row dict": str, e.g. "_biosphere_dict",
        "col from label": str, e.g. "output",
        "col to label": str, e.g. "col",
        "col dict": str, e.g. "_activity_dict",
        "matrix": str, e.g. "biosphere_matrix"
    }

The last elements ("row from label", "row to label", etc.) are used by the :meth:`presamples.loader.PackagesDataLoader.index_arrays`
method to map the resource elements to the LCA matrices.

.. _loader:

Loading multiple presample packages
-------------------------------------

Loading multiple presample packages for use in models requiring one value at a time is done using the
``PackagesDataLoader`` class.

.. autoclass:: presamples.loader.PackagesDataLoader

When creating a ``PackagesDataLoader`` instance, parameter and matrix data automatically loaded by invoking the method
``load_data`` to each path in ``dirpaths``:

.. automethod:: presamples.loader.PackagesDataLoader.load_data

Loaded data can then be parsed for accessing *consolidated* parameters or for injecting data in LCA matrices.

.. _loader_param:

Using named parameters in ``PackagesDataLoader``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
With ``load_data``, all presample packages are loaded. However, to ensure that only the **last** presample package with
data on a specific named parameter is used, parameters are *consolidated*. The consolidated parameters are available
via the ``parameters`` property. ``parameters`` points to a ``ConsolidatedIndexedParameterMapping`` object.

.. autoclass:: presamples.loader.ConsolidatedIndexedParameterMapping
   :members:



.. _loader_lca:

Using ``PackagesDataLoader`` with LCA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Brightway ``LCA`` (and ``MonteCarloLCA``) objects can seamlessly integrate presample packages.

.. code-block:: python

   >>> from brightway2 import LCA
   >>> lca = LCA(demand={product:1}, presamples=[pp_path1, pp_path2, pp_path3])

This instantiates a ``PackagesDataLoader`` as described above.

It then indexes arrays:

.. automethod:: presamples.loader.PackagesDataLoader.index_arrays

Finally, data from the correct columns in the presamples arrays are inserted in the LCA matrices:

.. automethod:: presamples.loader.PackagesDataLoader.update_matrices

