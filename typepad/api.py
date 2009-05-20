"""

The `typepad.api` module contains `TypePadObject` implementations of all the
content objects provided in the TypePad API.

"""

from remoteobjects.dataobject import find_by_name

from typepad.tpobject import *
from typepad import fields
import re

def xid_from_atom_id(atom_id):
    try:
        # tag:api.typepad.com,2009:6e01148739c04077bd0119f49c602c9c4b
        # tag:api.typepad.com,2003:user-6p00000001
        return re.match('^tag:(?:[\w-]+[.]?)+,\d{4}:(?:\w+-)?(\w+)$', atom_id).groups()[0]
    except:
        return None

class User(TypePadObject):

    """A TypePad user.

    This includes those who own TypePad blogs, those who use TypePad Connect
    and registered commenters who have either created a TypePad account or
    signed in with OpenID.

    """

    object_type = "tag:api.typepad.com,2009:User"

    id                 = fields.Field()
    url_id             = fields.Field(api_name='urlId')
    display_name       = fields.Field(api_name='displayName')
    preferred_username = fields.Field(api_name='preferredUsername')
    email              = fields.Field()
    about_me           = fields.Field(api_name='aboutMe')
    interests          = fields.List(fields.Field())
    urls               = fields.List(fields.Field())
    accounts           = fields.List(fields.Field())
    links              = fields.Object('LinkSet')
    relationships      = fields.Link(ListOf('Relationship'))
    events             = fields.Link(ListOf('Event'))
    comments           = fields.Link(ListOf('Comment'), api_name='comments-sent')
    favorites          = fields.Link(ListOf('Favorite'))
    notifications      = fields.Link(ListOf('Event'))
    memberships        = fields.Link(ListOf('Relationship'))
    elsewhere_accounts = fields.Link(ListOf('ElsewhereAccount'), api_name='elsewhere-accounts')

    @classmethod
    def get_self(cls, **kwargs):
        """Returns a `User` instance representing the account as whom the
        client library is authenticating."""
        return cls.get('/users/@self.json', **kwargs)

    @classmethod
    def get_by_id(cls, id, **kwargs):
        """Returns a `User` instance by their unique identifier.
        
        Asserts that the url_id parameter matches ^\w+$."""
        id = xid_from_atom_id(id)
        assert id, "valid id parameter required"
        return cls.get_by_url_id(id, **kwargs)

    @classmethod
    def get_by_url_id(cls, url_id, **kwargs):
        """Returns a `User` instance by their url identifier.
        
        Asserts that the url_id parameter matches ^\w+$."""
        # FIXME: What chracters are permitted for usernames? is '-' okay?
        assert re.match('^\w+$', url_id), "invalid url_id parameter given"
        return cls.get('/users/%s.json' % url_id, **kwargs)


class ElsewhereAccount(TypePadObject):

    """A user account on an external website."""

    domain            = fields.Field()
    username          = fields.Field()
    user_id           = fields.Field(api_name='userId')
    url               = fields.Field()
    provider_name     = fields.Field(api_name='providerName')
    provider_url      = fields.Field(api_name='providerURL')
    provider_icon_url = fields.Field(api_name='providerIconURL')


class Relationship(TypePadObject):

    """The unidirectional relationship between pairs of users and groups."""

    source = fields.Object('TypePadObject')
    target = fields.Object('TypePadObject')
    status = fields.Object('RelationshipStatus')


class RelationshipStatus(TypePadObject):

    """A representation of just the relationship type of a relationship,
    without the associated endpoints."""

    types = fields.List(fields.Field())


class Group(TypePadObject):

    """A group that users can join, and to which users can post assets.

    TypePad API social applications are represented as groups.

    """

    object_type = "tag:api.typepad.com,2009:Group"

    id           = fields.Field()
    url_id       = fields.Field(api_name='urlId')
    display_name = fields.Field(api_name='displayName')
    tagline      = fields.Field()
    urls         = fields.List(fields.Field())
    links        = fields.Object('LinkSet')

    # TODO: these aren't really Relationships because the target is really a group
    memberships  = fields.Link(ListOf('Relationship'))
    assets       = fields.Link(ListOf('Asset'))
    events       = fields.Link(ListOf('Event'))
    comments     = fields.Link(ListOf('Asset'))

    # comments     = fields.Link(ListOf(Asset), api_name='comment-assets')
    post_assets  = fields.Link(ListOf('Post'), api_name='post-assets')
    photo_assets = fields.Link(ListOf('Photo'), api_name='photo-assets')
    link_assets  = fields.Link(ListOf('LinkAsset'), api_name='link-assets')
    video_assets = fields.Link(ListOf('Video'), api_name='video-assets')
    audio_assets = fields.Link(ListOf('Audio'), api_name='audio-assets')

    @classmethod
    def get_by_id(cls, id, **kwargs):
        """Returns a `Group` instance by their unique identifier.
        
        Asserts that the url_id parameter matches ^\w+$."""
        id = xid_from_atom_id(id)
        assert id, "valid id parameter required"
        return cls.get_by_url_id(id, **kwargs)

    @classmethod
    def get_by_url_id(cls, url_id):
        """Returns a `Group` instance by the group's url identifier.
        
        Asserts that the url_id parameter matches ^\w+$."""
        assert re.match('^\w+$', url_id), "invalid url_id parameter given"
        return cls.get('/groups/%s.json' % url_id)


class Application(TypePadObject):

    """An application that can authenticate to the TypePad API using OAuth.

    An application is identified by its OAuth consumer key, which in the case
    of a hosted group is the same as the identifier for the group itself.

    """

    api_key = fields.Field(api_name='apiKey')
    # TODO: this can be a User or Group
    owner   = fields.Object('Group')
    links   = fields.Object('LinkSet')

    @property
    def oauth_request_token(self):
        """The URL from which to request the OAuth request token."""
        return self.links['oauth-request-token-endpoint'].href

    @property
    def oauth_authorization_page(self):
        """The URL at which end users can authorize the application to access
        their accounts."""
        return self.links['oauth-authorization-page'].href

    @property
    def oauth_access_token_endpoint(self):
        """The URL from which to request the OAuth access token."""
        return self.links['oauth-access-token-endpoint'].href

    @property
    def session_sync_script(self):
        """The URL from which to request session sync javascript."""
        return self.links['session-sync-script'].href

    @property
    def oauth_identification_page(self):
        """The URL at which end users can identify themselves to sign into 
        typepad, thereby signing into this site."""
        return self.links['oauth-identification-page'].href

    @property
    def signout_page(self):
        """The URL at which end users can sign out of TypePad."""
        return self.links['signout-page'].href
    
    @property
    def user_flyouts_script(self):
        """The URL from which to request typepad user flyout javascript."""
        return self.links['user-flyouts-script'].href

    @property
    def browser_upload_endpoint(self):
        """The endpoint to use for uploading file assets directly to
        TypePad."""
        return '/browser-upload.json'

    @classmethod
    def get_by_api_key(cls, api_key):
        """Returns an `Application` instance by the API key.
        
        Asserts that the api_key parameter matches ^\w+$."""
        assert re.match('^\w+$', api_key), "invalid api_key parameter given"
        return cls.get('/applications/%s.json' % api_key)


class Event(TypePadObject):

    """An action that a user or group did.

    An event has an `actor`, which is the user or group that did the action; a
    set of `verbs` that describe what kind of action occured; and an `object`
    that is the object that the action was done to. In the current TypePad API
    implementation, only assets, users and groups can be the object of an
    event.

    """

    id        = fields.Field()
    url_id    = fields.Field(api_name='urlId')
    # TODO: vary these based on verb content? oh boy
    actor     = fields.Object('User')
    object    = fields.Object('Asset')
    published = fields.Datetime()
    verbs     = fields.List(fields.Field())

    def __unicode__(self):
        return unicode(self.object)


class Asset(TypePadObject):

    """An item of content generated by a user."""

    object_type = "tag:api.typepad.com,2009:Asset"

    # documented fields
    id           = fields.Field()
    url_id       = fields.Field(api_name='urlId')
    title        = fields.Field()
    author       = fields.Object('User')
    published    = fields.Datetime()
    updated      = fields.Datetime()
    summary      = fields.Field()
    content      = fields.Field()
    # TODO: categories should be Tags?
    categories   = fields.List(fields.Field())
    status       = fields.Object('PublicationStatus')
    links        = fields.Object('LinkSet')
    in_reply_to  = fields.Object('AssetRef', api_name='inReplyTo')

    @classmethod
    def get_by_id(cls, id, **kwargs):
        """Returns an `Asset` instance by the identifier for the asset.
        
        Asserts that the url_id parameter matches ^\w+$."""
        id = xid_from_atom_id(id)
        assert id, "valid id parameter required"
        return cls.get_by_url_id(id, **kwargs)

    @classmethod
    def get_by_url_id(cls, url_id):
        """Returns an `Asset` instance by the url id for the asset.
        
        Asserts that the url_id parameter matches ^\w+$."""
        assert re.match('^\w+$', url_id), "invalid url_id parameter given"
        a = cls.get('/assets/%s.json' % url_id)
        a.id = '%s-%s' % (cls.object_type, url_id)
        return a

    @property
    def actor(self):
        """This asset's author.

        This alias lets us use `Asset` instances interchangeably with `Event`
        instances in templates.
        """
        return self.author

    def comment_count(self):
        try:
            return self.links['replies'].total
        except (TypeError, KeyError):
            return 0

    comments = fields.Link(ListOf('Asset'))

    def favorite_count(self):
        try:
            return self.links['favorites'].total
        except (TypeError, KeyError):
            return 0

    favorites = fields.Link(ListOf('Asset'))

    @property
    def asset_ref(self):
        """An `AssetRef` instance representing this asset."""
        # TODO: "This is also stupid. Why not have in_reply_to just be another asset??"
        return AssetRef(url_id=self.url_id,
                        ref=self.id,
                        href='/assets/%s.json' % self.url_id,
                        type='application/json',
                        object_types=self.object_types)

    def __unicode__(self):
        return self.title or self.summary or self.content


class Comment(Asset):

    """A text comment posted in reply to some other asset."""

    object_type = "tag:api.typepad.com,2009:Comment"


class Favorite(Asset):

    """A favorite of some other asset.
    
    Asserts that the user_id and asset_id parameter match ^\w+$."""

    object_type = "tag:api.typepad.com,2009:Favorite"

    @classmethod
    def get_by_user_asset(cls, user_id, asset_id):
        assert re.match('^\w+$', user_id), "invalid user_id parameter given"
        assert re.match('^\w+$', asset_id), "invalid asset_id parameter given"
        return cls.get('/favorites/%s:%s.json' % (asset_id, user_id))


class Post(Asset):

    """An entry in a blog."""

    object_type = "tag:api.typepad.com,2009:Post"


class Photo(Asset):

    """An entry in a blog."""

    object_type = "tag:api.typepad.com,2009:Photo"


class Audio(Asset):

    """An entry in a blog."""

    object_type = "tag:api.typepad.com,2009:Audio"


class Video(Asset):

    """An entry in a blog."""

    object_type = "tag:api.typepad.com,2009:Video"


class LinkAsset(Asset):

    """A shared link to some URL."""

    object_type = "tag:api.typepad.com,2009:Link"


class Document(Asset):

    """A shared link to some URL."""

    object_type = "tag:api.typepad.com,2009:Document"


class AssetRef(TypePadObject):

    """A structure that refers to an asset without including its full
    content."""

    ref    = fields.Field()
    url_id = fields.Field(api_name='urlId')
    href   = fields.Field()
    type   = fields.Field()
    author = fields.Object('User')


class PublicationStatus(TypePadObject):

    """A container for the flags that represent an asset's publication status.

    Publication status is currently represented by two flags: published and
    spam. The published flag is false when an asset is held for moderation,
    and can be set to true to publish the asset. The spam flag is true when
    TypePad's spam filter has determined that an asset is spam, or when the
    asset has been marked as spam by a moderator.

    """

    published = fields.Field()
    spam      = fields.Field()


# TODO: write this class
class Tag(TypePadObject):
    pass