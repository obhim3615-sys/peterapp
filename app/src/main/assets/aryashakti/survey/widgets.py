from django import forms
from django_json_widget.widgets import JSONEditorWidget

class ReadOnlyJSONEditorWidget(JSONEditorWidget):
    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs['readonly'] = True
        super().__init__(attrs)
