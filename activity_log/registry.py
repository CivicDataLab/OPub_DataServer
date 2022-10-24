from inspect import isclass

from django.apps import apps
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured


class RegistrationError(Exception):
    pass


def setup_generic_relations(model_class):
    """
    Set up GenericRelations for actionable models.
    """
    Activity = apps.get_model('activity_log', 'activity')

    if Activity is None:
        raise RegistrationError(
            'Unable get actstream.Activity. Potential circular imports '
            'in initialisation. Try moving actstream app to come after the '
            'apps which have models to register in the INSTALLED_APPS setting.'
        )

    related_attr_name = 'related_query_name'
    related_attr_value = 'actions_with_%s' % label(model_class)

    relations = {}
    for field in ('target', 'action_object', 'target_group'):  # Removed actor
        attr = '%s_actions' % field
        attr_value = '{}_as_{}'.format(related_attr_value, field)
        kwargs = {
            'content_type_field': '%s_content_type' % field,
            'object_id_field': '%s_object_id' % field,
            related_attr_name: attr_value
        }
        rel = GenericRelation('activity_log.Activity', **kwargs)
        rel.contribute_to_class(model_class, attr)
        relations[field] = rel

        # @@@ I'm not entirely sure why this works
        setattr(Activity, attr_value, None)
    return relations


def label(model_class):
    if hasattr(model_class._meta, 'model_name'):
        model_name = model_class._meta.model_name
    else:
        model_name = model_class._meta.module_name
    return '{}_{}'.format(model_class._meta.app_label, model_name)


def validate(model_class, exception_class=ImproperlyConfigured):
    if isinstance(model_class, str):
        model_class = apps.get_model(*model_class.split('.'))
    if not isinstance(model_class, ModelBase):
        raise exception_class(
            'Object %r is not a Model class.' % model_class)
    return model_class


class ActionableModelRegistry(dict):

    def register(self, *model_classes_or_labels):
        for class_or_label in model_classes_or_labels:
            model_class = validate(class_or_label)
            if model_class not in self:
                self[model_class] = setup_generic_relations(model_class)

    def unregister(self, *model_classes_or_labels):
        for class_or_label in model_classes_or_labels:
            model_class = validate(class_or_label)
            if model_class in self:
                del self[model_class]

    def check(self, model_class_or_object):
        if getattr(model_class_or_object, '_deferred', None):
            model_class_or_object = model_class_or_object._meta.proxy_for_model
        if not isclass(model_class_or_object):
            model_class_or_object = model_class_or_object.__class__
        model_class = validate(model_class_or_object, RuntimeError)
        if model_class not in self:
            raise ImproperlyConfigured(
                'The model %s is not registered. Please use actstream.registry '
                'to register it.' % model_class.__name__)


registry = ActionableModelRegistry()
register = registry.register
unregister = registry.unregister
check = registry.check
