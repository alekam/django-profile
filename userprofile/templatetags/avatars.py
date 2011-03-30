# coding=UTF-8
from django.template import Library, Node, TemplateSyntaxError, Variable
from django.utils.translation import ugettext as _
from userprofile.models import Avatar
from userprofile.settings import AVATAR_SIZES, DEFAULT_AVATAR_SIZE

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

        user = self.user.resolve(context)
        avatar = Avatar.objects.get_for_user(user)
        return avatar.get_resized_image_url(size)

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
