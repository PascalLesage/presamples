import datetime
import os
import shutil
import uuid
from pathlib import Path

from bw2data import config, projects
from bw2data.sqlite import create_database
from peewee import (DateTimeField, ForeignKeyField, IntegerField, Model,
                    TextField, fn)

presamples_dir = Path(projects.request_directory("presamples"))


class ModelBase(Model):
    _order_field = "name"

    __repr__ = lambda x: str(x)

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

    def resources(self):
        return (
            PresampleResource
            .select()
            .join(CampaignOrdering)
            .where(CampaignOrdering.campaign == self)
            .order_by(PresampleResource.order.asc())
        )

    def __iter__(self):
        for resource in self.resources():
            yield resource.as_loadable()

    def _order_value(self):
        return getattr(self, "_order_field")

    def _shift_presamples_at_index(self, index):
        """Shift the order of all presamples >= ``index`` up by one."""
        CampaignOrdering.update(order = CampaignOrdering.order + 1).where(
            CampaignOrdering.campaign == self,
            CampaignOrdering.order > index - 1
        ).execute()

    def _max_order(self):
        return CampaignOrdering.select(fn.Max(CampaignOrdering.order)).where(
            CampaignOrdering.campaign == self
        ).scalar()

    def add_local_presamples(self, dirpath, index=None, copy=True):
        """Add presamples directory at ``dirpath``.

        ``index`` is an optional index in the order of presamples.
        Existing presamples will be shifted if necessary.

        If true, ``copy`` will cause the directory to be copied to the
        project directory."""
        assert os.path.isdir(dirpath)
        # TODO: Validate files correct
        # TODO: Get name and description from metadata
        if index is not None:
            self._shift_presamples_at_index(index)
        else:
            index = self._max_order() + 1

        if copy:
            path = presamples_dir / uuid.uuid4().hex
            shutil.copytree(dirpath, path, symlinks=True)
            name = os.path.split(dirpath)[-1]
            dirpath = path

        resource = PresampleResource.create(
            name=name,
            kind='local',
            resource=os.path.abspath(dirpath)
        )
        CampaignOrdering.create(
            campaign=self,
            resource=resource,
            order=index
        )

    def add_child(self, name, description=None):
        """Add child campaign, including all presamples.

        Returns new ``Campaign`` object."""
        with db.atomic() as transaction:
            campaign = Campaign.create(
                name=name,
                description=description,
                parent=self
            )
            for pr in PresampleResource.select().where(
                    PresampleResource.campaign == self):
                PresampleResource.create(
                    campaign=campaign,
                    resource=pr.resource,
                    order=pr.order
                )
        return campaign

    @property
    def children(self):
        return Campaign.select().where(Campaign.parent == self)

    # TODO: Ancestors, descendents


class PresampleResource(ModelBase):
    name = TextField(null=True)
    description = TextField(null=True)
    kind = TextField(default="local")
    resource = TextField()  # localpath for files

    @property
    def metadata(self):
        # TODO: Load metadata from datapackage
        return None

    def as_loadable(self):
        """Return resource location to be loaded by ``MatrixPresamples``.

        Currently only support local resources; more types could be added later."""
        if self.kind == "local":
            return self.resource
        else:
            raise ValueError("This presample resource cant be loaded")


class CampaignOrdering(ModelBase):
    _order_field = "order"

    campaign = ForeignKeyField(Campaign)
    resource = ForeignKeyField(PresampleResource)
    order = IntegerField()


def init_campaigns():
    db = create_database(
        os.path.join(projects.dir, "campaigns.db"),
        [Campaign, PresampleResource, CampaignOrdering]
    )
    config.sqlite3_databases.append((
        "campaigns.db",
        db,
        [Campaign, PresampleResource, CampaignOrdering]
    ))
    return db

db = init_campaigns()
