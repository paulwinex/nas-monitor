import logging

from tortoise import models, fields, Tortoise
from nas_monitor.config import config


class Device(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, unique=True)
    type = fields.CharField(max_length=50, db_index=True)  # cpu, ram, hdd, zfs_pool, net
    enabled = fields.BooleanField(default=True)
    details = fields.JSONField(null=True)


class MetricBase(models.Model):
    timestamp = fields.DatetimeField(db_index=True)
    device = fields.ForeignKeyField('models.Device')
    label = fields.CharField(max_length=50, db_index=True)
    value = fields.FloatField()

    class Meta: abstract = True


class RawMetric(MetricBase): pass


class HourlyMetric(MetricBase): pass


class HistoryMetric(MetricBase): pass


class MigrationState(models.Model):
    stage = fields.CharField(max_length=20, primary_key=True)
    last_processed_id = fields.BigIntField(default=0)



def model_to_dict(obj):
    # _meta.fields содержит список всех имен полей модели
    return {field: getattr(obj, field) for field in obj._meta.fields}


async def init_db():
    await Tortoise.init(db_url=config.DB_PATH, modules={'models': [__name__]})
    await Tortoise.generate_schemas()
    logging.info('Schemas generated!')


async def disconnect_db():
    await Tortoise.close_connections()