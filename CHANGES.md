# 0.2.8 (2021-03-09)

Fix #72 to allow python 3.9 to parse json files

# 0.2.7 (2020-02-11)

Utility function to change the path of a presample resource

# 0.2.6 (2019-12-20)

Add possibility to collapse matrix data for repeated matrix indices when creating presample packages  

# 0.2.5 (2019-06-21)

Like 0.2.4, but rereleased due to readme issues

# 0.2.4 (2019-06-21)

Change `DataPackageLoader.parameters` to `ConsolidatedIndexedParameterMapping`

# 0.2.3 (2018-11-13)

Update for API changes in `bw2parameters`.

# 0.2.2 (2018-10-24)

Add function to allow resetting sequential indices. Makes Monte Carlo LCA happier.

# 0.2.1 (2018-06-11)

* Fix `ParametersMapping` for presample packages that have both matrix and paramter data
* Extend power of `ParameterizedBrightwayModel` by extending arguments of its `save_presamples` method to all arguments allowed in the underlying `create_presamples_package`

# 0.2 (2018-03-20)

Compatibility with [peewee 3](http://docs.peewee-orm.com/en/latest/peewee/changes.html) and bw2data 3.3.

# 0.1 (2018-03-20)

Initial release
