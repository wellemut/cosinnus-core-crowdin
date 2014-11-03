# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from taggit.managers import TaggableManager

from cosinnus.conf import settings
from cosinnus.models.group import CosinnusGroup
from cosinnus.utils.functions import unique_aware_slugify
from cosinnus.models.widget import WidgetConfig
from cosinnus.core.registries.widgets import widget_registry
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured


class LocationModelMixin(models.Model):
    location_place = models.CharField(max_length=255, default='', blank=True)

    class Meta:
        abstract = True


class PeopleModelMixin(models.Model):
    people_name = models.CharField(max_length=255, default='', blank=True)

    class Meta:
        abstract = True


class PublicModelMixin(models.Model):
    public = models.BooleanField(_('Public'), default=False, blank=True)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class BaseTagObject(models.Model):

    VISIBILITY_USER = 0
    VISIBILITY_GROUP = 1
    VISIBILITY_ALL = 2

    #: Choices for :attr:`visibility`: ``(int, str)``
    # Empty first choice must be included for select2 placeholder compatibility!
    VISIBILITY_CHOICES = (
        ('', ''),
        (VISIBILITY_USER, _('User')),
        (VISIBILITY_GROUP, _('Group')),
        (VISIBILITY_ALL, _('All')),
    )

    group = models.ForeignKey(CosinnusGroup, verbose_name=_('Group'),
        related_name='+', null=True, on_delete=models.CASCADE)

    persons = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
        null=True, verbose_name=_('Persons'), related_name='+')
    
    tags = TaggableManager(_('Tags'), blank=True)

    visibility = models.PositiveSmallIntegerField(_('Permissions'), blank=True,
        default=VISIBILITY_GROUP, choices=VISIBILITY_CHOICES)
    
    class Meta:
        abstract = True

    def __str__(self):
        return "Tag object {0}".format(self.pk)


class TagObject(LocationModelMixin, PeopleModelMixin, PublicModelMixin,
                BaseTagObject):

    class Meta:
        app_label = 'cosinnus'
        swappable = 'COSINNUS_TAG_OBJECT_MODEL'


@python_2_unicode_compatible
class AttachedObject(models.Model):
    """
    A generic object to serve as attachable object connector for all cosinnus
    objects.
    """

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    target_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        app_label = 'cosinnus'
        ordering = ('content_type',)
        unique_together = (('content_type', 'object_id'),)
        verbose_name = _('Attached object')
        verbose_name_plural = _('Attached objects')

    def __str__(self):
        return '<attach: %s::%s>' % (self.content_type, self.object_id)

    @property
    def model_name(self):
        """
        The model name used in the cosinnus attached file configurations, e.g.:
        `'cosinnus_file.FileEntry'`
        """
        if not hasattr(self, '_model_name'):
            ct = self.content_type
            self._model_name = '%s.%s' % (ct.app_label, ct.model_class().__name__)
        return self._model_name


@python_2_unicode_compatible
class BaseTaggableObjectModel(models.Model):
    """
    Represents the base for all cosinnus main models. Each inheriting model
    has a set of simple ``tags`` which are just strings. Additionally each
    model has a ``media_tag`` that refers to all general tags like a location,
    people and so on.
    """

    media_tag = models.OneToOneField(settings.COSINNUS_TAG_OBJECT_MODEL,
        blank=True, null=True, on_delete=models.SET_NULL)

    attached_objects = models.ManyToManyField(AttachedObject, blank=True, null=True)

    group = models.ForeignKey(CosinnusGroup, verbose_name=_('Group'),
        related_name='%(app_label)s_%(class)s_set', on_delete=models.CASCADE)

    title = models.CharField(_('Title'), max_length=255)
    slug = models.SlugField(max_length=55, blank=True)  # human readable part is 50 chars

    creator = models.ForeignKey(settings.AUTH_USER_MODEL,
        verbose_name=_('Creator'),
        on_delete=models.PROTECT,
        null=True,
        related_name='%(app_label)s_%(class)s_set')
    created = models.DateTimeField(
        verbose_name=_('Created'),
        editable=False,
        default=now,
        auto_now_add=True)

    class Meta:
        abstract = True
        unique_together = (('group', 'slug'),)

    def __str__(self):
        return self.title

    def __repr__(self):
        return "<tagged object {0} {1} (ID: {2})>".format(
            self.__class__.__name__, self.title, self.pk)

    def save(self, *args, **kwargs):
        unique_aware_slugify(self, 'title', 'slug', group=self.group)
        if hasattr(self, '_media_tag_cache'):
            del self._media_tag_cache
        super(BaseTaggableObjectModel, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        #self.user.delete()
        print ">> call delete of basetagmodel", self
        return super(self.__class__, self).delete(*args, **kwargs)

    def media_tag_object(self):
        key = '_media_tag_cache'
        if not hasattr(self, key):
            if self.media_tag_id is None:
                setattr(self, key, self.group.media_tag)
            else:
                setattr(self, key, self.media_tag)
        return getattr(self, key)
    
    @cached_property
    def attached_image(self):
        """ Return the first image file attached to the event as the event's image """
        for attached_file in self.attached_objects.all():
            if attached_file.model_name == "cosinnus_file.FileEntry" and attached_file.target_object.is_image:
                return attached_file.target_object
        return None
    
    @cached_property
    def attached_images(self):
        """ Return the all image files attached to the event"""
        images = []
        for attached_file in self.attached_objects.all():
            if attached_file.model_name == "cosinnus_file.FileEntry" and attached_file.target_object.is_image:
                images.append(attached_file.target_object)
        return images
    
    
    @property
    def sort_key(self):
        """ The main property on which this object model is sorted """
        if not self.created:
            return now()
        return self.created
    
    def grant_extra_read_permissions(self, user):
        """ An overridable check for whether this object grants certain users read permissions
            even though by general rules that user couldn't read the object.
            
            @param user: The user to check for extra permissions for """
        return False
    
    def grant_extra_write_permissions(self, user):
        """ An overridable check for whether this object grants certain users write permissions
            even though by general rules that user couldn't write the object.
            
            @param user: The user to check for extra permissions for """
        return False
    
    def get_delete_url(self):
        """ Similar to get_absolute_url, this returns the URL for this object's implemented delete view.
            Needs to be set by a specific implementation of BaseTaggableObjectModel """
        raise ImproperlyConfigured("The get_delete_url function must be implemented for model '%s'" % self.__class__)
    

class BaseHierarchicalTaggableObjectModel(BaseTaggableObjectModel):
    """
    Represents the base for hierarchical cosinnus models.
    """
    is_container = models.BooleanField(
        blank=False, null=False, default=False, editable=True)
    path = models.CharField(_('Path'),
        blank=False, null=False, default='/', max_length=100)

    class Meta(BaseTaggableObjectModel.Meta):
        abstract = True

    def __str__(self):
        return '%s (%s)' % (self.title, self.path)

    def save(self, *args, **kwargs):
        if self.path[-1] != '/':
            self.path += '/'
        super(BaseHierarchicalTaggableObjectModel, self).save(*args, **kwargs)
    
    @cached_property
    def container(self):
        """ Returns the hierarchical object's parent container or None if root or the object doesn't exist """
        if self.path == '/':
            return None
        if self.is_container:
            # go to parent folder path
            parentpath, _, _= self.path[:-1].rpartition('/')
            path = parentpath + '/'
        else:
            path = self.path
        
        qs = self.__class__.objects.all().filter(Q(group=self.group) & Q(is_container=True) & Q(path=path))
        first_list = list(qs[:1])
        if first_list:
            return first_list[0]
        return None

def ensure_container(sender, **kwargs):
    """ Creates a root container instance for all hierarchical objects in a newly created group """
    created = kwargs.get('created', False)
    if created:
        for model_class in BaseHierarchicalTaggableObjectModel.__subclasses__():
            if not model_class._meta.abstract:
                model_class.objects.create(group=kwargs.get('instance'), slug='_root_', title='_root_', path='/', is_container=True)
                
post_save.connect(ensure_container, sender=CosinnusGroup)

def get_tag_object_model():
    """
    Return the cosinnus tag object model that is defined in
    :data:`settings.COSINNUS_TAG_OBJECT_MODEL`
    """
    from django.core.exceptions import ImproperlyConfigured
    from django.db.models import get_model
    from cosinnus.conf import settings

    try:
        app_label, model_name = settings.COSINNUS_TAG_OBJECT_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured("COSINNUS_TAG_OBJECT_MODEL must be of the form 'app_label.model_name'")
    tag_model = get_model(app_label, model_name)
    if tag_model is None:
        raise ImproperlyConfigured("COSINNUS_TAG_OBJECT_MODEL refers to model '%s' that has not been installed" %
            settings.COSINNUS_TAG_OBJECT_MODEL)
    return tag_model


