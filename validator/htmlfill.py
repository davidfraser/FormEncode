import HTMLParser
import cgi

def default_formatter(error):
    return '<span class="error">%s</span><br>\n' % error

class FillingParser(HTMLParser.HTMLParser):
    r"""
    Fills HTML with default values, as in a form.

    Examples::

        >>> defaults = {'name': 'Bob Jones',
        ...             'occupation': 'Crazy Cultist',
        ...             'address': '14 W. Canal\nNew Guinea',
        ...             'living': 'no',
        ...             'nice_guy': 0}
        >>> parser = FillingParser(defaults)
        >>> parser.feed('<input type="text" name="name" value="fill">\
        ... <select name="occupation"><option value="">Default</option>\
        ... <option value="Crazy Cultist">Crazy cultist</option>\
        ... </select> <textarea cols=20 style="width: 100%" name="address">An address\
        ... </textarea> <input type="radio" name="living" value="yes">\
        ... <input type="radio" name="living" value="no">\
        ... <input type="checkbox" name="nice_guy" checked="checked">')
        >>> print parser.text()
        <input type="text" name="name" value="Bob Jones">
        <select name="occupation">
        <option value="">Default</option>
        <option value="Crazy Cultist" selected="selected">Crazy cultist</option>
        </select>
        <textarea cols=20 style="width: 100%" name="address">14 W. Canal
        New Guinea</textarea>
        <input type="radio" name="living" value="yes">
        <input type="radio" name="living" value="no" selected="selected">
        <input type="checkbox" name="nice_guy">
    """

    def __init__(self, defaults, errors=None, use_all_keys=False,
                 error_formatters=None):
        HTMLParser.HTMLParser.__init__(self)
        self.content = []
        self.source = None
        self.lines = None
        self.source_pos = None
        self.defaults = defaults
        self.in_textarea = None
        self.in_select = None
        self.skip_next = False        
        self.errors = errors or {}
        self.in_error = None
        self.skip_error = False
        self.use_all_keys = use_all_keys
        self.used_keys = {}
        self.used_errors = {}
        if error_formatters is None:
            self.error_formatters = {'default': default_formatter}
        else:
            self.error_formatters = error_formatters

    def feed(self, data):
        self.source = data
        self.lines = data.split('\n')
        self.source_pos = 1, 0
        HTMLParser.HTMLParser.feed(self, data)

    def close(self):
        HTMLParser.HTMLParser.close(self)
        if self.use_all_keys:
            unused = self.defaults.copy()
            unused_errors = self.errors.copy()
            for key in self.used_keys.keys():
                if unused.has_key(key):
                    del unused[key]
            for key in self.used_errors.keys():
                if unused_errors.has_key(key):
                    del unused_errors[key]
            assert not unused, (
                "These keys from defaults were not used in the form: %s"
                % unused.keys())
            assert not unused_errors, (
                "These keys from errors were not used in the form: %s"
                % unused_errors.keys())

    def add_key(self, key):
        self.used_keys[key] = 1

    def handle_starttag(self, tag, attrs):
        self.write_pos()
        if tag == 'input':
            self.handle_input(attrs)
        elif tag == 'textarea':
            self.handle_textarea(attrs)
        elif tag == 'select':
            self.handle_select(attrs)
        elif tag == 'option':
            self.handle_option(attrs)
        elif tag == 'form:error':
            self.handle_error(attrs)
        elif tag == 'form:iferror':
            self.handle_iferror(attrs)

    def handle_misc(self, whatever):
        self.write_pos()
    handle_charref = handle_misc
    handle_entityref = handle_misc
    handle_data = handle_misc
    handle_comment = handle_misc
    handle_decl = handle_misc
    handle_pi = handle_misc
    unknown_decl = handle_misc

    def handle_endtag(self, tag):
        self.write_pos()
        if tag == 'textarea':
            self.handle_end_textarea()
        elif tag == 'select':
            self.handle_end_select()
        elif tag == 'form:iferror':
            self.handle_end_iferror()

    def handle_iferror(self, attrs):
        name = self.get_attr(attrs, 'name')
        assert name, "Name attribute in <iferror> required (%s)" % self.getpos()
        self.in_error = name
        if not self.errors.get(name):
            self.skip_error = True
        self.skip_next = True

    def handle_end_iferror(self, attrs):
        self.in_error = None
        self.skip_error = False
        self.skip_next = False

    def handle_error(self, attrs):
        name = self.get_attr(attrs, 'name')
        formatter = self.get_attr(attrs, 'format') or 'default'
        if not name:
            name = self.in_error
        assert name, (
            "Name attribute in <error> required if not contained in "
            "<iferror> (%s)" % self.getpos())
        error = self.errors.get(name, '')
        if error:
            error = self.error_formatters[formatter](error)
            self.write_text(error)
        self.skip_next = True
        self.used_errors[name] = 1

    def handle_input(self, attrs):
        t = (self.get_attr(attrs, 'type') or 'text').lower()
        name = self.get_attr(attrs, 'name')
        value = self.defaults.get(name)
        if t == 'text':
            self.set_attr(attrs, 'value', value or '')
            self.write_tag('input', attrs)
            self.skip_next = True
            self.add_key(name)
        elif t == 'checkbox':
            if str(value) == self.get_attr(attrs, 'value'):
                self.set_attr(attrs, 'checked', 'checked')
            else:
                self.del_attr(attrs, 'checked')
            self.write_tag('input', attrs)
            self.skip_next = True
            self.add_key(name)
        elif t == 'radio':
            if str(value) == self.get_attr(attrs, 'value'):
                self.set_attr(attrs, 'selected', 'selected')
            else:
                self.del_attr(attrs, 'selected')
            self.write_tag('input', attrs)
            self.skip_next = True
            self.add_key(name)
        elif t in ('file', 'button', 'submit', 'reset'):
            pass # don't skip next
        else:
            assert 0, "I don't know about this kind of <input>: %s (pos: %s)" \
                   % (t, self.getpos())

    def handle_textarea(self, attrs):
        self.write_tag('textarea', attrs)
        name = self.get_attr(attrs, 'name')
        value = self.defaults.get(name, '')
        self.write_text(cgi.escape(value, 1))
        self.write_text('</textarea>')
        self.in_textarea = True
        self.add_key(name)

    def handle_end_textarea(self):
        self.in_textarea = False
        self.skip_next = True

    def handle_select(self, attrs):
        self.in_select = self.get_attr(attrs, 'name')

    def handle_end_select(self):
        self.in_select = None

    def handle_option(self, attrs):
        assert self.in_select, "<option> outside of <select>: %s" % self.getpos()
        if str(self.defaults.get(self.in_select, '')) == \
               self.get_attr(attrs, 'value'):
            self.set_attr(attrs, 'selected', 'selected')
            self.add_key(self.in_select)
        else:
            self.del_attr(attrs, 'selected')
        self.write_tag('option', attrs)
        self.skip_next = True

    def write_text(self, text):
        self.content.append(text)

    def write_tag(self, tag, attrs):
        attr_text = ''.join([' %s="%s"' % (n, cgi.escape(v, 1))
                             for (n, v) in attrs])
        self.write_text('<%s%s>' % (tag, attr_text))

    def write_pos(self):
        cur_line, cur_offset = self.getpos()
        if self.in_textarea or self.skip_error:
            self.source_pos = self.getpos()
            return
        if self.skip_next:
            self.skip_next = False
            self.source_pos = self.getpos()
            return
        if cur_line == self.source_pos[0]:
            self.write_text(
                self.lines[cur_line-1][self.source_pos[1]:cur_offset])
        else:
            self.write_text(
                self.lines[self.source_pos[0]-1][self.source_pos[1]:])
            for i in range(self.source_pos[0]+1, cur_line):
                self.write_text(self.lines[i-1])
                self.write_text('\n')
            self.write_text(self.lines[cur_line-1][:cur_offset])
        self.source_pos = self.getpos()

    def get_attr(self, attr, name, default=None):
        for n, value in attr:
            if n.lower() == name:
                return value
        return default

    def set_attr(self, attr, name, value):
        for i in range(len(attr)):
            if attr[i][0].lower() == name:
                attr[i] = (name, value)
                return
        attr.append((name, value))

    def del_attr(self, attr, name):
        for i in range(len(attr)):
            if attr[i][0].lower() == name:
                del attr[i]
                break
            
    def text(self):
        return ''.join(self.content)
