from modelsdoc.wrappers import FieldWrapper
from modelsdoc.utils import get_foreignkey  # , get_choices


def get_choices_custom(field):
    if getattr(field, "choices", None):
        # return ', '.join(['{}:{}'.format(*c) for c in field.choices])
        return "**UNE SEULE valeur possible**<br>" + "<br>".join(
            ["- {}".format(c[1]) for c in field.choices]
        )
    elif getattr(field, "base_field", None) and (getattr(field, "default") == list):
        return "**PLUSIEURS valeurs possible**<br>" + "<br>".join(
            ["- {}".format(c[1]) for c in field.base_field.choices]
        )
    else:
        return ""


class CustomFieldWrapper(FieldWrapper):
    """
    Custom Field Wrapper to have a nice list of choices
    https://github.com/tell-k/django-modelsdoc/issues/8
    """

    def __init__(self, field, model, connection, attrdocs):
        super().__init__(field, model, connection, attrdocs)

    @property
    def comment(self):
        comment = get_foreignkey(self._field)
        comment += get_choices_custom(self._field)
        key = (self._model._model.__name__, self._field.name)
        comment += " ".join(self._attrdocs.get(key, []))
        return comment
