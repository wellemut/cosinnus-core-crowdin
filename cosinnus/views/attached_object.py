# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.loading import get_model
from django.views.generic.edit import CreateView, UpdateView

from cosinnus.core.registries import attached_object_registry
from django_select2.views import Select2View, NO_ERR_RESP
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from cosinnus.models.group import CosinnusGroup
from django.contrib.auth.models import User
from cosinnus.views.mixins.group import RequireReadMixin, FilterGroupMixin,\
    GroupFormKwargsMixin
from cosinnus.views.mixins.user import UserFormKwargsMixin


class AttachableViewMixin(object):
    """
    Used together with FormAttachable.

    Extending this view will add form fields for Cosinnus attachable objects to
    `CreateView`s and `UpdateView`s. Configure which cosinnus objects may be
    attached to your object in `settings.COSINNUS_ATTACHABLE_OBJECTS`.
    """

    def form_valid(self, form):
        # retrieve the attached objects from the form and save them
        # after saving the object itself
        ret = super(AttachableViewMixin, self).form_valid(form)
        # if hasattr(form, 'save_m2m'):
        #     form.save_m2m()
        form.save_attachable()
        return ret


class CreateViewAttachable(AttachableViewMixin, CreateView):
    pass


class UpdateViewAttachable(AttachableViewMixin, UpdateView):
    pass


class AttachableObjectSelect2View(RequireReadMixin, Select2View):
    """
        This view is used as API backend to serve the suggestions for the message recipient field.
    """
    def check_all_permissions(self, request, *args, **kwargs):
        user = request.user 
        
        # Check if current user is member of this group
        current_group = self.kwargs.get('group', None)
        usergroups = CosinnusGroup.objects.get_for_user(request.user)
        is_member = any((current_group == group.slug) for group in usergroups)
        
        if not user.is_authenticated() or not is_member:
            raise PermissionDenied
        
    def get_results(self, request, term, page, context):
        term = term.lower() 
        print ">>> term:", term
        
        #import ipdb; ipdb.set_trace();
        """
            ipdb> self.kwargs
            {u'model': u'cosinnus_note.Note', u'group': u'newgroup'}
        """
        
        results = []
        
        for attach_model_id in attached_object_registry.get_attachable_to(self.kwargs.get('model', None)):
            app_label, model_name = attach_model_id.split('.')
            attach_model_class = get_model(app_label, model_name)
            queryset = attach_model_class._default_manager.filter(group__slug=self.kwargs.get('group', None))
            queryset = queryset.filter(Q(title__icontains=term))
            # TODO: Sascha: make a more sophisticated filter that allows filtering for "Event" tokens
        
            # these result sets are what select2 uses to build the choice list
            results.extend( [ (attach_model_id+":"+str(res.id), "%s %s" % (attach_model_id, res.title),) for res in queryset ] )
            
        print ">> results", results
        
        return (NO_ERR_RESP, False, results) # Any error response, Has more results, options list

