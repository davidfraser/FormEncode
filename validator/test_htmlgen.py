from htmlgen import html

def test_basic():
    output = '<a href="test">hey there</a>'
    assert str(html.a(href='test')('hey there')) == output
    assert str(html.a('hey there')(href='test')) == output
    assert str(html.a(href='test', c='hey there')) == output
    assert str(html.a('hey there', href='test')) == output

def test_compound():
    output = '<b>Hey <i>you</i>!</b>'
    assert str(html.b('Hey ', html.i('you'), '!')) == output
    assert str(html.b()('Hey ')(html.i()('you'))('!')) == output
    inner = html('Hey ', html.i('you'), '!')
    assert html.str(inner) == 'Hey <i>you</i>!'
    assert str(inner) == 'Hey <i>you</i>!'
    assert (repr(inner)
            == "ElementList(['Hey ', <Element '<i>you</i>'>, "
            "'!'])")
    assert str(html.b(inner)) == output

def test_unicode():
    uni_value = u'\xff'
    try:
        uni_value.encode('ascii')
    except ValueError:
        pass
    else:
        assert 0, (
            "We need something that can't be ASCII-encoded: %r (%r)"
            % (uni_value, uni_value.encode('ascii')))
    assert (str(html.b(uni_value))
            == ('<b>%s</b>' % uni_value).encode('utf-8'))
    
if __name__ == '__main__':
    test_basic()
    test_compound()
    test_unicode()
