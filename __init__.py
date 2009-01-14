import httplib2
# TODO: require 2.0+ version of simplejson that doesn't provide unicode keys
import simplejson
import logging
from urlparse import urljoin
import types

# TODO configurable?
BASE_URL = 'http://127.0.0.1:8080/'
USERNAME = 'markpasc'
PASSWORD = 'password'

def omit_nulls(data):
    if not isinstance(data, dict):
        data = dict(data.__dict__)
    for key in data.keys():
        # TODO: don't have etag in obj data in the first place?
        if data[key] is None or key == 'etag':
            del data[key]
    return data

class RemoteObject(object):
    fields = {}

    def __init__(self, **kwargs):
        self._id = None
        self.update(**kwargs)

    def update(self, **kwargs):
        for field_name, field_class in self.fields.iteritems():
            value = kwargs.get(field_name)
            # TODO: reuse child objects as appropriate
            if isinstance(value, list) or isinstance(value, tuple):
                new_value = []
                for item in value:
                    o = field_class(**item)
                    o.parent = self
                    new_value.append(o)
                value = new_value
            elif isinstance(value, dict):
                value = field_class(**value)
                value.parent = self # e.g. reference to blog from entry
            setattr(self, field_name, value)

    @classmethod
    def get(cls, id, http=None, **kwargs):
        # TODO accept atom or whatever other response format
        url = id
        logging.debug('Fetching %s' % (url,))

        if http is None:
            http = httplib2.Http()
        (response, content) = http.request(url)
        logging.debug('Got content %s' % (content,))

        # TODO make sure astropad is returning the proper content type
        #if data and resp.get('content-type') == 'application/json':
        data = simplejson.loads(content)
        x = cls(**data)
        x._id = response['content-location']  # follow redirects
        if 'etag' in response:
            x._etag = response['etag']
        return x

    def save(self, http=None):
        if http is None:
            http = httplib2.Http()
        http.add_credentials(USERNAME, PASSWORD)

        body = simplejson.dumps(self, default=omit_nulls)

        httpextra = {}
        if self._id is not None:
            url = self._id
            method = 'PUT'
            if hasattr(self, _etag) and self._etag is not None:
                httpextra['headers'] = {'if-match': self._etag}
        elif self.parent is not None and self.parent._id is not None:
            url = self.parent._id
            method = 'POST'
        else:
            raise ValueError('nowhere to save this object to?')

        (response, content) = http.request(url, method=method, body=body, **httpextra)

        # TODO: follow redirects first?
        new_body = simplejson.loads(content)
        logging.debug('Yay saved my obj, now turning %s into new content' % (content,))
        if 'etag' in response:
            new_body['etag'] = response['etag']
        self.update(**new_body)


class User(RemoteObject):
    """User from TypePad API.

    >>> user = User.get(1)
    >>> user.name
    u'Mike Malone'
    >>> user.email
    u'mjmalone@gmail.com'
    """

    fields = {
        'name':  basestring,
        'email': basestring,
        'uri':   basestring,
    }
    set_url = r'/users.json'
    url     = r'/users/%(id)s.json'


class Entry(RemoteObject):
    fields = {
        'slug':     basestring,
        'title':    basestring,
        'content':  basestring,
        'pub_date': basestring,
        'mod_date': basestring,
        'authors':  User,
    }
    set_url = r'/blogs/%(blog_id)s.json'
    url     = r'/blogs/%(blog_id)s/entries/%(id)s.json'


class Blog(RemoteObject):
    """Blog from TypePad API.
    
    >>> blog = Blog.get(1)
    >>> blog.title
    u'Fred'
    """

    fields = {
        'title':    basestring,
        'subtitle': basestring,
        'entries':  Entry,
    }
    set_url = r'/blogs.json'
    url     = r'/blogs/%(id)s.json'
