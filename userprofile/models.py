# coding=UTF-8
from countries import CountryField
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile, File
from django.core.files.storage import get_storage_class
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template import loader, Context
from django.utils.translation import ugettext as _
import datetime
import os.path
import settings
try:
    from PIL import Image
except ImportError:
    import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class BaseProfile(models.Model):
    """
    User profile model
    """
    user = models.ForeignKey(User, unique=True)
    creation_date = models.DateTimeField(default=datetime.datetime.now)
    country = CountryField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True

    def has_avatar(self):
        return Avatar.objects.filter(user=self.user, valid=True).count()

    def __unicode__(self):
        return _("%s's profile") % self.user

    def get_absolute_url(self):
        return reverse("profile_public", args=[self.user])


class AvatarManager(models.Manager):

    def get_for_user(self, user):
        if not user.is_active and settings.DEFAULT_AVATAR_FOR_INACTIVES_USER:
            return self.get_default_avatar()
        elif user.is_anonymous():
            return self.get_default_avatar()

        try:
            return self.get_query_set().get(user=user, valid=True)
        except Avatar.DoesNotExist:
            return self.get_default_avatar()

    def get_default_avatar(self):
        """Return Avatar model instance with default avatar image from static files storage"""
        static_storage = get_storage_class(django_settings.STATICFILES_STORAGE)()
        image = static_storage.open(settings.DEFAULT_AVATAR)
        avatar = Avatar(image=image, valid=True)
        avatar.image.storage = static_storage
        avatar.image.name = settings.DEFAULT_AVATAR
        return avatar


class Avatar(models.Model):
    """
    Avatar model
    """
    image = models.ImageField(upload_to="avatars/%Y/%b/%d", storage=settings.MEDIA_STORAGE)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField()

    objects = AvatarManager()

    class Meta:
        unique_together = (('user', 'valid'),)

    def __unicode__(self):
        return _("%s's Avatar") % self.user

    def get_resized_image_filename(self, size=None, sizes=None):
        base, filename = os.path.split(self.image.name)
        name, extension = os.path.splitext(filename)
        if size is None:
            if sizes is not None:
                return [os.path.join(base, "%s.%s%s" % (name, size, extension)) for size in sizes]
            else:
                raise TypeError(u'get_resized_image_filename() requires size or sizes arguments')
        else:
            return os.path.join(base, "%s.%s%s" % (name, size, extension))

    def get_resized_image_url(self, size):
        resized_filename = self.get_resized_image_filename(size)
        if not self.image.storage.exists(resized_filename):
            if not self.image.storage.exists(self.image.name) and settings.REMOVE_LOST_AVATAR:
                self.delete()
                return Avatar.objects.get_default_avatar().get_resized_image_url(size)
            thumb = Image.open(self.image)
            if thumb.mode != 'RGB':
                thumb = thumb.convert('RGB')
            img_format = thumb.format
            if not settings.CAN_ENLARGE_AVATAR or (thumb.size[0] > size or thumb.size[1] > size or not hasattr(thumb, 'resize')):
                thumb.thumbnail((size, size), Image.ANTIALIAS)
            else:
                thumb = thumb.resize((size, size), Image.BICUBIC)
            f = File(StringIO(), name=resized_filename)
            try:
                thumb.save(f, img_format, **settings.SAVE_IMG_PARAMS.get(img_format, {}))
            except:
                thumb.save(f, img_format)
            f.seek(0)
            self.image.storage.save(resized_filename, ContentFile(f.read()))
        return self.image.storage.url(resized_filename)

    def delete_avatar_thumbs(self):
        if self.image.name is None or self.image.name == settings.DEFAULT_AVATAR:
            return
        for filename in self.get_resized_image_filename(sizes=settings.AVATAR_SIZES):
            try:
                self.image.storage.delete(filename)
            except:
                pass

    def delete(self):
        if self.image.name != settings.DEFAULT_AVATAR:
            self.delete_avatar_thumbs()
            # deleting avatar source
            try:
                self.image.storage.delete(self.image.name)
            except:
                pass
        super(Avatar, self).delete()


class EmailValidationManager(models.Manager):
    """
    Email validation manager
    """
    def verify(self, key):
        try:
            verify = self.get(key=key)
            if not verify.is_expired():
                verify.user.email = verify.email
                if settings.REQUIRE_EMAIL_CONFIRMATION:
                    verify.user.is_active = True
                verify.user.save()
                verify.verified = True
                verify.save()
                return True
            else:
                if not verify.verified:
                    verify.delete()
                return False
        except:
            return False

    def getuser(self, key):
        try:
            return self.get(key=key).user
        except:
            return False

    def add(self, user, email):
        """
        Add a new validation process entry
        """
        while True:
            key = User.objects.make_random_password(70)
            try:
                EmailValidation.objects.get(key=key)
            except EmailValidation.DoesNotExist:
                break

        template_body = "userprofile/email/validation.txt"
        template_subject = "userprofile/email/validation_subject.txt"
        site_name, domain = Site.objects.get_current().name, Site.objects.get_current().domain
        body = loader.get_template(template_body).render(Context(locals()))
        subject = loader.get_template(template_subject).render(Context(locals())).strip()
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[email])
        user = User.objects.get(username=str(user))
        self.filter(user=user).delete()
        return self.create(user=user, key=key, email=email)

class EmailValidation(models.Model):
    """
    Email Validation model
    """
    user = models.ForeignKey(User, unique=True)
    email = models.EmailField(blank=True)
    key = models.CharField(max_length=70, unique=True, db_index=True)
    verified = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    objects = EmailValidationManager()

    def __unicode__(self):
        return _("Email validation process for %(user)s") % { 'user': self.user }

    def is_expired(self):
        expiration_delay = settings.EMAIL_CONFIRMATION_DELAY
        return self.verified or \
            (self.created + datetime.timedelta(days=expiration_delay) <= datetime.datetime.now())

    def resend(self):
        """
        Resend validation email
        """
        template_body = "userprofile/email/validation.txt"
        template_subject = "userprofile/email/validation_subject.txt"
        site_name, domain = Site.objects.get_current().name, Site.objects.get_current().domain
        key = self.key
        body = loader.get_template(template_body).render(Context(locals()))
        subject = loader.get_template(template_subject).render(Context(locals())).strip()
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[self.email])
        self.created = datetime.datetime.now()
        self.save()
        return True
