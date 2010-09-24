from django.conf import settings
from django import newforms as forms
from datetime import datetime, time, date
from time import strptime

# DATETIMEWIDGET
calbtn = u"""
<script type="text/javascript">
    Calendar.setup({
        inputField     :    "%s",
        ifFormat       :    "%s",
        button         :    "%s",
        singleClick    :    true,
        showsTime      :    %s
    });
</script>"""

class DateTimeWidget(forms.TextInput):
    dformat = '%Y-%m-%d %H:%M'
    disabled = False
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '': 
            try:
                final_attrs['value'] = value.strftime(self.dformat)
            except:
                final_attrs['value'] = value
        if not final_attrs.has_key('id'):
            final_attrs['id'] = u'%s_id' % (name)
        id = final_attrs['id']

        if self.disabled:
            final_attrs['enabled'] = 0
        else:
            final_attrs['enabled'] = 1
        
        jsdformat = self.dformat #.replace('%', '%%')
        cal = calbtn % (id, jsdformat, id, 'true')
        a = u'<input%s />%s' % (forms.util.flatatt(final_attrs), cal)
        return a

    def disable(self):
        self.disabled = True

    def value_from_datadict(self, data, name):
        dtf = forms.fields.DEFAULT_DATETIME_INPUT_FORMATS
        empty_values = forms.fields.EMPTY_VALUES

        value = data.get(name, None)
        if value in empty_values:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day)
        for format in dtf:
            try:
                return datetime(*strptime(value, format)[:6])
            except ValueError:
                continue
        return None

class DateWidget(forms.TextInput):
    dformat = '%Y-%m-%d'
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '': 
            try:
                final_attrs['value'] = value.strftime(self.dformat)
            except:
                final_attrs['value'] = value
        if not final_attrs.has_key('id'):
            final_attrs['id'] = u'%s_id' % (name)
        id = final_attrs['id']
        
        jsdformat = self.dformat #.replace('%', '%%')
        cal = calbtn % (id, jsdformat, id, 'false')
        a = u'<input%s />%s' % (forms.util.flatatt(final_attrs), cal)
        return a

    def value_from_datadict(self, data, name):
        dtf = forms.fields.DEFAULT_DATETIME_INPUT_FORMATS
        empty_values = forms.fields.EMPTY_VALUES

        value = data.get(name, None)
        if value in empty_values:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day)
        for format in dtf:
            try:
                return datetime(*strptime(value, format)[:6])
            except ValueError:
                continue
        return None
