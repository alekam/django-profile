# coding=UTF-8
from countries import CountryField
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template import loader, Context
from django.utils.translation import ugettext as _
import datetime
import os.path
import settings
import urllib



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


class Avatar(models.Model):
    """
    Avatar model
    """
    image = models.ImageField(upload_to="avatars/%Y/%b/%d", storage=settings.MEDIA_STORAGE)
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField()

    class Meta:
        unique_together = (('user', 'valid'),)

    def __unicode__(self):
        return _("%s's Avatar") % self.user
    
    def get_image_path(self):
        if settings.USE_AWS_STORAGE_BACKEND:
            path = urllib.unquote(self.image.name)
        else:
            path = self.image.path
        return path        

    def delete(self):
        base, filename = os.path.split(self.get_image_path())
        name, extension = os.path.splitext(filename)
        for key in settings.AVATAR_SIZES:
            try:
                settings.MEDIA_STORAGE.delete(os.path.join(base, "%s.%s%s" % (name, key, extension)))
            except:
                pass
        super(Avatar, self).delete()

    def save(self, *args, **kwargs):
        path = self.get_image_path()
        for avatar in Avatar.objects.filter(user=self.user, valid=self.valid).exclude(id=self.id):

            base, filename = os.path.split(path)
            name, extension = os.path.splitext(filename)
            for key in settings.AVATAR_SIZES:
                try:
                    settings.MEDIA_STORAGE.delete(os.path.join(base, "%s.%s%s" % (name, key, extension)))
                except:
                    pass
            avatar.delete()

        super(Avatar, self).save(*args, **kwargs)


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
