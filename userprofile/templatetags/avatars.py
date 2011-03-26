# coding=UTF-8
from cStringIO import StringIO
from django.conf import settings
from django.core.files.base import ContentFile
from django.template import Library, Node, TemplateSyntaxError, Variable
from django.utils.translation import ugettext as _
from userprofile.models import Avatar
from userprofile.settings import AVATAR_SIZES, DEFAULT_AVATAR_FOR_INACTIVES_USER, \
    DEFAULT_AVATAR, SAVE_IMG_PARAMS, DEFAULT_AVATAR_SIZE, MEDIA_STORAGE, \
    CAN_ENLARGE_AVATAR
import os
import urllib
import urlparse
try:
    from PIL import Image
except ImportError:
    import Image

register = Library()

class ResizedThumbnailNode(Node):
    def __init__(self, size, username=None):
        try:
            self.size = int(size)
        except:
            self.size = Variable(size)

        if username:
            self.user = Variable(username)
        else:
            self.user = Variable("user")

    def render(self, context):
        # If size is not an int, then it's a Variable, so try to resolve it.
        size = self.size
        if not isinstance(size, int):
            size = int(self.size.resolve(context))

        if not size in AVATAR_SIZES:
            return ''

        try:
            user = self.user.resolve(context)
            if DEFAULT_AVATAR_FOR_INACTIVES_USER and not user.is_active:
                raise
            avatar = Avatar.objects.get(user=user, valid=True).image
            avatar_path = avatar.get_image_path()
            if not MEDIA_STORAGE.exists(avatar_path):
                raise
            base, filename = os.path.split(avatar_path)
            name, extension = os.path.splitext(filename)
            filename = os.path.join(base, "%s.%s%s" % (name, size, extension))
            base_url = avatar.url

        except:
            avatar_path = DEFAULT_AVATAR
            avatar = open(avatar_path)
            base, filename = os.path.split(avatar_path)
            name, extension = os.path.splitext(filename)
            filename = os.path.join(base, "%s.%s%s" % (name, size, extension))
            base_url = filename.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)

        url_tuple = urlparse.urlparse(base_url)
        url = urlparse.urljoin(urllib.unquote(urlparse.urlunparse(url_tuple)), "%s.%s%s" % (name, size, extension))

        if not MEDIA_STORAGE.exists(filename):
            thumb = Image.open(ContentFile(avatar.read()))
            if thumb.mode != 'RGB':
                thumb = thumb.convert('RGB')
            img_format = thumb.format
            if not CAN_ENLARGE_AVATAR or (thumb.size[0] > size or thumb.size[1] > size or not hasattr(thumb, 'resize')):
                thumb.thumbnail((size, size), Image.ANTIALIAS)
            else:
                thumb = thumb.resize((size, size), Image.BICUBIC)
            f = StringIO()
            try:
                thumb.save(f, img_format, **SAVE_IMG_PARAMS.get(img_format, {}))
            except:
                thumb.save(f, img_format)
            f.seek(0)
            MEDIA_STORAGE.save(filename, ContentFile(f.read()))

        return url

@register.tag('avatar')
def Thumbnail(parser, token):
    bits = token.contents.split()
    username = None
    if len(bits) > 3:
        raise TemplateSyntaxError, _(u"You have to provide only the size as \
            an integer (both sides will be equal) and optionally, the \
            username.")
    elif len(bits) == 3:
        username = bits[2]
    elif len(bits) < 2:
        bits.append(str(DEFAULT_AVATAR_SIZE))
    return ResizedThumbnailNode(bits[1], username)
