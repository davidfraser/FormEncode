"""
simplehtmlgen.py
5 Oct 2002
Ian Bicking <ianb@colorstudy.com>

Kind of like htmlgen, only much simpler.  The only important symbol that
is exported is ``html``.

You create tags with attribute access.  I.e., the "A" anchor tag is
html.a.  The attributes of the HTML tag are done with keyword
arguments.  The contents of the tag are the non-keyword arguments
(concatenated).  You can also use the special "c" keyword, passing a
list, tuple, or single tag, and it will make up the contents (this is
useful because keywords have to come after all non-keyword arguments,
which is non-intuitive).

If the value of an attribute is Exclude, then no attribute will be
inserted.  I.e.::

    >>> html.a(href='http://www.yahoo.com', name=Exclude, c='Click Here')
    '<a href=\"http://www.yahoo.com\">Click Here</a>'

If the value is None, then the empty string is used.  Otherwise str()
is called on the value.

``html`` can also be called, and it will concatenate the string
representations of its arguments.

``html.input`` is special, in that you can use ``html.input.radio()``
to get an ``<input type=\"radio\">`` tag.  You can still use
``html.input(type=\"radio\")`` though, just like normal.

``html.comment`` will generate an HTML comment, like
``html.comment('comment text', 'and some more text')`` -- note that
it cannot take keyword arguments (because they wouldn't mean anything).

Examples::

    >>> print html.html(
    ...    html.head(html.title("Page Title")),
    ...    html.body(
    ...    bgcolor='#000066',
    ...    text='#ffffff',
    ...    c=[html.h1('Page Title'),
    ...       html.p('Hello world!')],
    ...    ))
    <html>
    <head>
    <title>Page Title</title>
    </head>
    <body text=\"#ffffff\" bgcolor=\"#000066\">
    <h1>Page Title</h1><p>
    Hello world!
    </p>
    .
    </body>
    .
    </html>
    >>> html.a(href='#top', c='return to top')
    '<a href=\"#top\">return to top</a>'
    >>> 1.4
    1.4

"""

from cgi import escape
import elementtree.ElementTree as et

default_encoding = 'utf-8'

class _HTML:

    def __getattr__(self, attr):
        if attr.startswith('_'):
            raise AttributeError
        attr = attr.lower()
        if attr == 'comment':
            return Element(et.Comment, {})
        else:
            return Element(attr, {})
        
    def __call__(self, *args):
        return ElementList(args)

    def quote(self, arg):
        return escape(unicode(arg), 1)

    def str(self, arg, encoding=None):
        if isinstance(arg, str):
            return arg
        elif isinstance(arg, unicode):
            return arg.encode(default_encoding)
        elif isinstance(arg, (list, tuple)):
            return ''.join(map(self.str, arg))
        elif isinstance(arg, Element):
            return str(arg)
        else:
            return unicode(arg).encode(default_encoding)

html = _HTML()

class Element(et._ElementInterface):

    def __call__(self, *args, **kw):
        el = self.__class__(self.tag, self.attrib)
        if kw.has_key('c'):
            if args:
                raise ValueError(
                    "You may either provide positional arguments or a "
                    "'c' keyword argument, but not both")
            args = kw['c']
            del kw['c']
        for name, value in kw.items():
            if value is Exclude:
                del kw[name]
                continue
            if name.endswith('_'):
                kw[name[:-1]] = value
                del kw[name]
        el.attrib.update(kw)
        el.text = self.text
        last = None
        for item in self.getchildren():
            last = item
            el.append(item)
        for arg in flatten(args):
            if not et.iselement(arg):
                if last is None:
                    if el.text is None:
                        el.text = unicode(arg)
                    else:
                        el.text += unicode(arg)
                else:
                    if last.tail is None:
                        last.tail = unicode(arg)
                    else:
                        last.tail += unicode(arg)
            else:
                last = arg
                el.append(last)
        return el

    def __str__(self):
        return et.tostring(self, default_encoding)

    def __unicode__(self):
        # This is lame!
        return str(self).decode(default_encoding)

    def __repr__(self):
        return '<Element %r>' % str(self)

class UnfinishedInput:

    def __init__(self, tag, type=None):
        self._type = type
        UnfinishedTag.__init__(self, tag)

    def __call__(self, *args, **kw):
        if self._type:
            kw['type'] = self._type
        return UnfinishedTag.__call__(self, *args, **kw)

    def __getattr__(self, attr):
        if attr.startswith('__'):
            raise AttributeError
        return self.__class__(self._tag, type=attr.lower())

class Exclude:
    pass

class ElementList(list):
    
    def __str__(self):
        return html.str(self)

    def __repr__(self):
        return 'ElementList(%s)' % list.__repr__(self)

def flatten(items):
    for item in items:
        if isinstance(item, ElementList):
            for sub in flatten(item):
                yield sub
        else:
            yield item
