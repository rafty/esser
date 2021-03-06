import os
from datetime import datetime
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute,
    JSONAttribute, MapAttribute
)
from esser.constants import AGGREGATE_KEY_DELIMITER


class DynamoDBEventModel(Model):
    """
    A DynamoDB Event model
    """
    class Meta:
        region = os.environ.get('AWS_REGION', 'ap-southeast-2')
        table_name = os.environ.get("EVENT_TABLE", "events")
        host = os.environ.get('DYNAMODB_HOST', None)
    aggregate_name = UnicodeAttribute(hash_key=True)
    aggregate_key = UnicodeAttribute(range_key=True)
    event_type = UnicodeAttribute()
    created_at = UTCDateTimeAttribute()
    event_data = JSONAttribute()

    @classmethod
    def _conditional_operator_check(cls, conditional_operator):
        pass

    @property
    def aggregate_id(self):
        return self.aggregate_key.split(AGGREGATE_KEY_DELIMITER)[0]

    @property
    def version(self):
        return int(self.aggregate_key.split(
            AGGREGATE_KEY_DELIMITER
        )[1])


class Snapshot(Model):

    class Meta:
        table_name = "snapshots"
        host = os.getenv('DYNAMODB_HOST', None)
    aggregate_name = UnicodeAttribute(hash_key=True)
    aggregate_key = UnicodeAttribute(range_key=True)
    created_at = UTCDateTimeAttribute()
    state = MapAttribute()

    @classmethod
    def from_aggregate(cls, aggregate):
        state = aggregate.current_state
        last_event = aggregate.repository.get_last_event()
        snapshot = cls(
            aggregate_name=aggregate.aggregate_name,
            aggregate_key=last_event.aggregate_id,
            created_at=datetime.utcnow(),
            state=state
        )
        snapshot.save()
        return snapshot

    @classmethod
    def get_last_for(cls, aggregate, aggregate_id):
        cls.query(
            aggregate.aggregate_name,
            aggregate_key__begins_with=aggregate_id
        )
