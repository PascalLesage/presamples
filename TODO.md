# Docs

* Introduction and use cases
* How to generate presamples
* Data format for different kinds of presamples
* How to specify presamples for a new matrix (dtype, row_formatter, metadata)
* How to use presamples

# Presample generation

* From parameterized inventories
* From generic outside model

# Campaigns

* API and user stories for generating presamples and presample resources (packages?)
* Campaign.replace_presample_package,
* Campaign.add_presample_packages
* Campaign.add_local_presamples: Validate files, figure out if getting name and description from metadata is sensible
* PresamplePackage.metadata

# Tests

* Finish matrix presamples consolidation tests (in matrix_presamples)
* Test parameterized inventory generation and use
* Complete campaign tests

# Models

* Model to generate presamples for a whole database (check processed array md5?)
* Model to generate presamples for an LCIA method (check processed array md5?)
* Tests on finding exchanges

# Packaging

* Adjust CF presamples package to include method that generated them, if available
* Adjust LCA class to filter presamples based LCIA method (need to think about best way)
* Adjust docstring for split_inventory_presamples

# Matrix presamples

* __str__ method

# Bw2calc

* Tests for multi-column presamples (single-column already done)
