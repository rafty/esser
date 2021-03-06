from esser.validators import EsserValidator
from esser.exceptions import EventValidationException
from esser.signals import event_pre_save


class BaseCommand(object):
    """Base Command class."""

    def __init__(self):
        """
        Initialise the validator for the event based on schema.

        A valid Command class should have Command.schema
        """
        self.validator = EsserValidator(
            self.schema, event=self
        )

    @property
    def event_name(self):
        raise NotImplementedError('Implement event_name property')

    @property
    def command_name(self):
        """Command name by default is the class name."""
        return self.__class__.__name__

    def get_version(self):
        """Increment version of the event for the aggregate."""
        return self.entity.get_last_aggregate_version() + 1

    def attach_entity(self, entity):
        """Allow entity to be attached to the event."""
        setattr(self, 'entity', entity)
        setattr(self.validator, 'aggregate', entity)

    def persist(self, attrs):
        event_version = self.get_version()
        # dispatch the signal before persisting
        event_pre_save.send(
            sender=self.__class__,
            aggregate_name=self.entity.aggregate_name,
            aggregate_id=self.entity.aggregate_id,
            event_name=self.event_name,
            version=event_version,
            payload=attrs,
        )
        return self.entity.repository.persist(
            aggregate_id=self.entity.aggregate_id,
            version=event_version,
            event_type=self.event_name,
            attrs=attrs
        )

    def save(self, attrs):
        """Validate event input before saving."""
        if not self.validator.validate(attrs):
            raise EventValidationException(
                errors=self.validator.errors
            )
        normalized = self.validator.normalized(attrs)
        return self.persist(normalized)


class CreateCommand(BaseCommand):
    """Command for creating an entity."""

    def save(self, attrs):
        """Generate aggregate id using uuid."""
        aggregate_id = self.entity.generate_new_guid()
        self.entity.aggregate_id = aggregate_id
        return super(CreateCommand, self).save(attrs)

    def get_version(self):
        return self.entity.INITIAL_VERSION


class DeleteCommand(BaseCommand):

    @property
    def event_name(self):
        return 'Deleted'
