# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, patterns, url

from cosinnus.core.registries import url_registry
from cosinnus.conf import settings
from cosinnus.core.registries.group_models import group_model_registry

urlpatterns = patterns('cosinnus.views',
    # we do not define an index anymore and let CMS handle that.

    url(r'^signup/$', 'user.user_create', name='user-add'),
    url(r'^users/$', 'user.user_list', name='user-list'),
    url(r'^portal/admins/$', 'user.portal_admin_list', name='portal-admin-list'),
    url(r'^users/map/$', 'user.user_list_map', name='user-list-map'),
    url(r'^user/(?P<username>[^/]+)/$', 'profile.detail_view', name='profile-detail'),
    #url(r'^user/(?P<username>[^/]+)/edit/$', 'user.user_update', name='user-edit'),
    url(r'^profile/$', 'profile.detail_view', name='profile-detail'),
    url(r'^profile/dashboard/$', 'widget.user_dashboard', name='user-dashboard'),
    url(r'^profile/edit/$', 'profile.update_view', name='profile-edit'),
    url(r'^profile/delete/$', 'profile.delete_view', name='profile-delete'),
    url(r'^language/(?P<language>[^/]+)/$', 'common.switch_language', name='switch-language'),
    
    
    url(r'^widgets/list/$', 'widget.widget_list', name='widget-list'),
    url(r'^widgets/add/user/$', 'widget.widget_add_user', name='widget-add-user-empty'),
    url(r'^widgets/add/user/(?P<app_name>[^/]+)/(?P<widget_name>[^/]+)/$', 'widget.widget_add_user', name='widget-add-user'),
    url(r'^widget/(?P<id>\d+)/$', 'widget.widget_detail', name='widget-detail'),
    url(r'^widget/(?P<id>\d+)/(?P<offset>\d+)/$', 'widget.widget_detail', name='widget-detail-offset'),
    url(r'^widget/(?P<id>\d+)/delete/$', 'widget.widget_delete', name='widget-delete'),
    url(r'^widget/(?P<id>\d+)/edit/$', 'widget.widget_edit', name='widget-edit'),
    url(r'^widget/(?P<id>\d+)/edit/(?P<app_name>[^/]+)/(?P<widget_name>[^/]+)/$', 'widget.widget_edit', name='widget-edit-swap'),

    url(r'^search/$', 'search.search', name='search'),
    
    url(r'^housekeeping/$', 'housekeeping.housekeeping', name='housekeeping'),
    url(r'^housekeeping/deletespamusers/$', 'housekeeping.delete_spam_users', name='housekeeping_delete_spam_users'),
    

    url(r'^select2/', include('cosinnus.urls_select2', namespace='select2')),
)


for url_key in group_model_registry:
    plural_url_key = group_model_registry.get_plural_url_key(url_key, url_key + '_s')
    prefix = group_model_registry.get_url_name_prefix(url_key, '')
    
    urlpatterns += patterns('cosinnus.views',
        url(r'^%s/$' % plural_url_key, 'group.group_list', name=prefix+'group-list'),
        url(r'^%s/map/$' % plural_url_key, 'group.group_list_map', name=prefix+'group-list-map'),
        url(r'^%s/add/$' % plural_url_key, 'group.group_create', name=prefix+'group-add'),
        url(r'^%s/(?P<group>[^/]+)/$' % url_key, 'widget.group_dashboard', name=prefix+'group-dashboard'),
        url(r'^%s/(?P<group>[^/]+)/microsite/$' % url_key, 'cms.group_microsite', name=prefix+'group-microsite'),
        url(r'^%s/(?P<group>[^/]+)/microsite/edit/$' % url_key, 'cms.group_microsite_edit', name=prefix+'group-microsite-edit'),
        url(r'^%s/(?P<group>[^/]+)/members/$' % url_key, 'group.group_detail', name=prefix+'group-detail'),
        url(r'^%s/(?P<group>[^/]+)/members/map/$' % url_key, 'group.group_members_map', name=prefix+'group-members-map'),
        url(r'^%s/(?P<group>[^/]+)/edit/$' % url_key, 'group.group_update', name=prefix+'group-edit'),
        url(r'^%s/(?P<group>[^/]+)/delete/$' % url_key, 'group.group_delete', name=prefix+'group-delete'),
        url(r'^%s/(?P<group>[^/]+)/join/$' % url_key, 'group.group_user_join', name=prefix+'group-user-join'),
        url(r'^%s/(?P<group>[^/]+)/leave/$' % url_key, 'group.group_user_leave', name=prefix+'group-user-leave'),
        url(r'^%s/(?P<group>[^/]+)/withdraw/$' % url_key, 'group.group_user_withdraw', name=prefix+'group-user-withdraw'),
        url(r'^%s/(?P<group>[^/]+)/users/$' % url_key, 'group.group_user_list', name=prefix+'group-user-list'),
        url(r'^%s/(?P<group>[^/]+)/users/add/$' % url_key, 'group.group_user_add', name=prefix+'group-user-add-generic'),
        url(r'^%s/(?P<group>[^/]+)/users/add/(?P<username>[^/]+)/$' % url_key, 'group.group_user_add', name=prefix+'group-user-add'),
        url(r'^%s/(?P<group>[^/]+)/users/delete/(?P<username>[^/]+)/$' % url_key, 'group.group_user_delete', name=prefix+'group-user-delete'),
        url(r'^%s/(?P<group>[^/]+)/users/edit/(?P<username>[^/]+)/$' % url_key, 'group.group_user_update', name=prefix+'group-user-edit'),
        url(r'^%s/(?P<group>[^/]+)/export/$' % url_key, 'group.group_export', name=prefix+'group-export'),
    
        url(r'^%s/(?P<group>[^/]+)/widgets/add/$' % url_key, 'widget.widget_add_group', name=prefix+'widget-add-group-empty'),
        url(r'^%s/(?P<group>[^/]+)/widgets/add/(?P<app_name>[^/]+)/(?P<widget_name>[^/]+)/$' % url_key, 'widget.widget_add_group', name=prefix+'widget-add-group'),
        
        url(r'^%s/(?P<group>[^/]+)/attachmentselect/(?P<model>[^/]+)$' % url_key, 'attached_object.attachable_object_select2_view', name=prefix+'attached_object_select2_view'),
    )

urlpatterns += url_registry.urlpatterns
