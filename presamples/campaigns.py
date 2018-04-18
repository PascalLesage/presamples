from pathlib import Path
import datetime
import json
import os
import shutil

try:
    from bw2data import config, projects
    from bw2data.sqlite import SubstitutableDatabase
    def presamples_dir():
        """Needs to be function for tests"""
        return Path(projects.request_directory("presamples"))

except ImportError:
    from .fallbacks import SubstitutableDatabase
    projects = None
    presamples_dir = os.getcwd

from peewee import (DateTimeField, ForeignKeyField, IntegerField, Model,
                    TextField, fn, DoesNotExist)
from .errors import MissingPresample
from .package_interface import PresamplesPackage


class ModelBase(Model):
    _order_field = "name"

    def __lt__(self, other):
        # Make it possible to order our objects
        if type(self) != type(other):
            raise TypeError
        else:
            return self._order_value() < other._order_value()


class Campaign(ModelBase):
    name = TextField(index=True, unique=True)
    description = TextField(null=True)
    parent = ForeignKeyField('self', null=True)
    modified = DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super().save(*args, **kwargs)

    @property
    def packages(self):
        return (
            PresampleResource
            .select()
            .join(CampaignOrdering)
            .where(CampaignOrdering.campaign == self)
            .order_by(CampaignOrdering.order.asc())
        )

    def __str__(self):
        if self.parent is not None:
            return "Campaign {n} with parent {p} and {r} packages".format(
            n=self.name, p=self.parent.name, r=self.packages.count())
        else:
            return "Campaign {n} with no parent and {r} packages".format(
            n=self.name, r=self.packages.count())

    def __iter__(self):
        """Iterate over campaign packages in order.

        Returns the path of each package for PackagesDataLoader."""
        for package in self.packages:
            yield package.as_loadable()

    def __contains__(self, obj):
        try:
            CampaignOrdering.get(
                campaign=self,
                package=self._get_resource(obj)
            )
            return True
        except DoesNotExist:
            return False

    def __len__(self):
        return self.packages.count()

    def _order_value(self):
        return getattr(self, getattr(self, "_order_field"))

    def _shift_presamples_at_index(self, index):
        """Shift the order of all presamples >= ``index`` up by one."""
        CampaignOrdering.update(order = CampaignOrdering.order + 1).where(
            CampaignOrdering.campaign == self,
            CampaignOrdering.order > index - 1
        ).execute()

    def _max_order(self):
        """Return maximum ordering index already used, or ``None``."""
        return CampaignOrdering.select(fn.Max(CampaignOrdering.order)).where(
            CampaignOrdering.campaign == self
        ).scalar()

    def _get_resource(self, obj):
        """Get a ``PresampleResource`` by class instance or name"""
        if isinstance(obj, PresampleResource):
            return obj
        else:
            return PresampleResource.get(name=obj)

    def replace_presample_package(self, new, old, propagate=False):
        """Replace presample package in campaign.

        ``new`` can be either a n instance of ``PresampleResource`` or the name of a presample resource; the same conditions apply for ``old``. ``old`` must already be added to the campaign.

        ``propagate`` determines whether to also replace presample packages in all child campaigns. Will ignore child campaigns where ``old`` is no longer used.

        Doesn't return anything."""
        new = self._get_resource(new)
        old = self._get_resource(old)
        if old not in self:
            raise MissingPresample

        link = CampaignOrdering.get(campaign=self, package=old)
        link.package = new
        link.save()

        if propagate:
            for child in self.descendants:
                try:
                    child.replace_presample_package(new, old, False)
                except MissingPresample:
                    pass

    def add_presample_resource(self, obj, index=None):
        """Add an existing ``PresampleResource``.

        ``obj`` is an instance of ``PresampleResource``, or the name of a ``PresampleResource``.

        ``index`` is an optional index in the order of presamples.
        Existing presamples will be shifted if necessary.

        Doesn't return anything."""
        package = self._get_resource(obj)
        if package in self:
            raise ValueError("This presample resource is already in this campaign")

        handle_none = lambda x: -1 if x is None else x

        if index is not None:
            self._shift_presamples_at_index(index)
        else:
            index = handle_none(self._max_order()) + 1

        CampaignOrdering.create(
            campaign=self,
            package=package,
            order=index
        )

    def drop_presample_resource(self, obj):
        """Remove a presample resource from a campaign.

        ``obj`` is an instance of ``PresampleResource``, or the name of a ``PresampleResource``.

        Doesn't return anything."""
        package = self._get_resource(obj)
        if package not in self:
            raise ValueError("This presample resource is not in this campaign")

        CampaignOrdering.get(
            campaign=self,
            package=package,
        ).delete_instance()

    def add_local_presamples(self, dirpath, index=None, copy=True):
        """Add presamples directory at ``dirpath``.

        ``index`` is an optional index in the order of presamples.
        Existing presamples will be shifted if necessary.

        If true, ``copy`` will cause the directory to be copied to the
        project directory.

        Doesn't return anything."""
        pp = PresamplesPackage(dirpath)
        id_, name = pp.id, pp.name

        handle_none = lambda x: -1 if x is None else x

        if index is not None:
            self._shift_presamples_at_index(index)
        else:
            index = handle_none(self._max_order()) + 1

        if copy:
            path = presamples_dir() / id_
            if os.path.isdir(path):
                raise ValueError("This package already exists in the project directory")
            shutil.copytree(dirpath, path, symlinks=True)
            dirpath = path

        package = PresampleResource.create(
            name=name,
            kind='local',
            path=os.path.abspath(dirpath)
        )
        CampaignOrdering.create(
            campaign=self,
            package=package,
            order=index
        )

    def add_child(self, name, description=None):
        """Add new child campaign, including all presamples.

        The child campaign should not exist already; ``name`` is the name of the new campaign to be created.

        Returns created ``Campaign`` object."""
        if Campaign.select().where(Campaign.name == name).count():
            raise ValueError("This campaign already exists")
        with db.atomic() as transaction:
            campaign = Campaign.create(
                name=name,
                description=description,
                parent=self
            )
            queryset = (
                CampaignOrdering
                .select()
                .join(Campaign)
                .where(CampaignOrdering.campaign == self)
                .order_by(CampaignOrdering.order.asc())
            )
            for obj in queryset:
                CampaignOrdering.create(
                    campaign=campaign,
                    package=obj.package,
                    order=obj.order
                )
        return campaign

    @property
    def children(self):
        return Campaign.select().where(Campaign.parent == self).order_by(Campaign.name)

    @property
    def descendants(self):
        """Return iterator of descendants, ordered by depth and then name. Convert to a list to get length."""
        # Recursive queries not supported in peewee
        # Note that quoting is SQLite specific (Postgres uses %s)
        for obj_id in Campaign.raw('''
            WITH RECURSIVE descendants (name, level, id) AS (
                VALUES(?, 0, ?)
                UNION ALL
                SELECT campaign.name, descendants.level + 1, campaign.id
                  FROM campaign
                  JOIN descendants ON campaign.parent_id = descendants.id
                 ORDER BY 2, 1
              )
            SELECT id FROM descendants WHERE id != ?;
        ''', self.name, self.id, self.id).tuples():
            yield Campaign.get(id=obj_id)

    @property
    def ancestors(self):
        """Return iterator of ancestors, ordered by distance from this campaign."""
        # Recursive queries not supported in peewee
        # Note that quoting is SQLite specific (Postgres uses %s)
        if not self.parent_id:
            raise StopIteration
        for obj_id in Campaign.raw('''
            WITH RECURSIVE ancestors (level, id) AS (
                VALUES(0, ?)
                UNION ALL
                SELECT ancestors.level + 1, campaign.parent_id
                  FROM campaign
                  JOIN ancestors ON campaign.id = ancestors.id
                  WHERE campaign.parent_id IS NOT NULL
              )
            SELECT id FROM ancestors;
        ''', self.parent_id).tuples():
            yield Campaign.get(id=obj_id)


class PresampleResource(ModelBase):
    name = TextField(unique=True, index=True)
    description = TextField(null=True)
    path = TextField()  # Anything that can be used by PyFilesystem

    @property
    def metadata(self):
        return PresamplesPackage(self.as_loadable()).metadata

    def as_loadable(self):
        """Maybe need to do something here with PyFilesystem."""
        return self.path


class CampaignOrdering(ModelBase):
    _order_field = "order"

    campaign = ForeignKeyField(Campaign)
    package = ForeignKeyField(PresampleResource)
    order = IntegerField()


def init_campaigns():
    db = SubstitutableDatabase(
        os.path.join(projects.dir, "campaigns.db"),
        [Campaign, PresampleResource, CampaignOrdering]
    )
    config.sqlite3_databases.append((
        "campaigns.db",
        db,
    ))
    return db


def init_campaigns_fallback():
    return SubstitutableDatabase(
        os.path.join(presamples_dir(), "campaigns.db"),
        [Campaign, PresampleResource, CampaignOrdering]
    )

if projects:
    db = init_campaigns()
else:
    db = init_campaigns_fallback()

