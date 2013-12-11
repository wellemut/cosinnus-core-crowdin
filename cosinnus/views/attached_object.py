# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.edit import CreateView, UpdateView
from django.db.models.loading import get_model

from cosinnus.core.loaders.attached_objects import cosinnus_attached_object_registry as caor

'''
Created on 11.12.2013

@author: Sascha Narr
'''


class AttachableMixin(object):
    
    def get_form_kwargs(self):
        kwargs = CreateView.get_form_kwargs(self)
        
        print(kwargs)
        source_model_id = self.model._meta.app_label + '.' + self.model._meta.object_name
        #self.model
        
        attachable_objects = caor.attachable_to.get(source_model_id, [])
        
        print(">>> Attachable objects:")
        print(attachable_objects)
        
        querysets = dict()
        
        #import ipdb; ipdb.set_trace();
        for attach_model_id in attachable_objects:
            #attach_model_name ="cosinnus_file.FileEntry"
            app_label, model_name = attach_model_id.split('.')
            attach_model_class = get_model(app_label, model_name)
            query_set = attach_model_class._default_manager.filter(group=self.group)
            
            print(">>> model_class")
            print(attach_model_class)
            print(query_set)
            querysets['attached_' + attach_model_id.replace('.', '_')] = query_set
            #import ipdb; ipdb.set_trace();
        
        
        
        kwargs.update({'attached_files_querysets': querysets})
        return kwargs


class CreateViewAttachable(AttachableMixin, CreateView):
    pass

class UpdateViewAttachable(AttachableMixin, UpdateView):
    pass
    