from .presamples_base import PackageBase
from collections.abc import Mapping
import numpy as np
import json
import os


class NameConflicts(Exception):
    """Can't flatten dictionary due to conflicting parameter names"""
    pass


class ParameterPresamples(PackageBase, Mapping):
    """Read-only interface to presamples for named parameters."""
    def __init__(self, *args, labels=None, **kwargs):
        super().__init__(*args, **kwargs)
        included = lambda x: labels is None or x in labels
        self.data = {r['label']: self._load(r) for r in self.resources if included(r['label'])}

    @property
    def resources(self):
        for o in self.metadata['resources']:
            if 'label' in o:
                yield o

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return len(self.data)

    def __contains__(self, k):
        return k in self.data

    def __iter__(self):
        return iter(self.data)

    def _load(self, obj):
        maybe_float = lambda x: float(x) if x.shape in ((), (1,)) else x

        names = json.load(open(os.path.join(self.path, obj['names']['filepath'])))
        samples = np.load(os.path.join(self.path, obj['samples']['filepath']))
        return {x: maybe_float(y.ravel()) for x, y in zip(names, samples)}

    @property
    def name_conflicts(self):
        return sum(len(o) for o in self.values()) != len({x for v in self.values() for x in v})

    def flattened(self):
        if self.name_conflicts:
            raise NameConflicts

        return {y: z for x in self.values() for y, z in x.items()}
