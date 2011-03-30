"""
This one collect the application settings
"""
from django.conf import settings
from django.core.files.storage import default_storage
import os


# path to the default avatar image.
DEFAULT_AVATAR = getattr(settings, 'DEFAULT_AVATAR', os.path.join("userprofile", "generic.jpg"))

DEFAULT_AVATAR_FOR_INACTIVES_USER = getattr(settings, 'DEFAULT_AVATAR_FOR_INACTIVES_USER', False)

# params to pass to the save method in PIL (dict with formats (JPEG, PNG, GIF...) as keys)
# see http://www.pythonware.com/library/pil/handbook/format-jpeg.htm and format-png.htm for options
SAVE_IMG_PARAMS = getattr(settings, 'SAVE_IMG_PARAMS', {})

AVATARS_DIR = getattr(settings, 'AVATARS_DIR', os.path.join(settings.MEDIA_ROOT, 'avatars'))

# If set to True, it will enable the Google Picasa web search of avatars.
AVATAR_WEBSEARCH = getattr(settings, 'AVATAR_WEBSEARCH', False)

# Max upload size (in MB) of the avatar image.
AVATAR_QUOTA = getattr(settings, 'AVATAR_QUOTA', None)

# Media storage for static files
MEDIA_STORAGE = getattr(settings, 'AVATAR_MEDIA_STORAGE', default_storage)

REMOVE_LOST_AVATAR = getattr(settings, 'REMOVE_LOST_AVATAR', True) 

# You need a valid Google Maps API Key so your users can use the Google
# Maps positioning functionality. Obtain one for your site name here:
# http://www.google.com/apis/maps/signup.html
GOOGLE_MAPS_API_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)

# If set to True, the user e-mail will be required to get an account on the system.
EMAIL_CONFIRMATION_DELAY = getattr(settings, 'EMAIL_CONFIRMATION_DELAY', 1)
REQUIRE_EMAIL_CONFIRMATION = getattr(settings, 'REQUIRE_EMAIL_CONFIRMATION', False)

# Specify which set of classes use for html structure of django-profile
#  - blueprint (the default, for blueprint css framework, full width)
#  - 960gs-12 (for 960.gs css framework, 12 columns, full width)
#  - 960-gs-16 (for 960.gs, 16 columns, full width)
#  - 960gs-12-in-9 (for 960.gs css, in a width of 9 columns, given as example)
#  - 960gs-24 (for 960.gs css framework, 24 columns, full width)
USERPROFILE_CSS_CLASSES = getattr(settings, 'USERPROFILE_CSS_CLASSES', 'blueprint')

AUTH_PROFILE_MODULE = getattr(settings, 'AUTH_PROFILE_MODULE', None)

REGISTRATION_FORM = getattr(settings, 'REGISTRATION_FORM', 'userprofile.forms.RegistrationForm')


CAN_ENLARGE_AVATAR = getattr(settings, 'CAN_ENLARGE_AVATAR', True)

AVATAR_SIZES = getattr(settings, 'AVATAR_SIZES', (128, 96, 64, 48, 32, 24, 16))

DEFAULT_AVATAR_SIZE = getattr(settings, 'DEFAULT_AVATAR_SIZE', 96)
if DEFAULT_AVATAR_SIZE not in AVATAR_SIZES:
    DEFAULT_AVATAR_SIZE = AVATAR_SIZES[0]
DEFAULT_AVATAR_WIDTH = getattr(settings, 'DEFAULT_AVATAR_SIZE', 96)

MIN_AVATAR_SIZE = getattr(settings, 'MIN_AVATAR_SIZE', DEFAULT_AVATAR_SIZE)
