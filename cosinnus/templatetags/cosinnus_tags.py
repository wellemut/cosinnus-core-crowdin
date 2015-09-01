# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict

import six
from six.moves.urllib.parse import parse_qsl
from copy import copy, deepcopy

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve, reverse, Resolver404
from django.http import HttpRequest
from django.template.defaulttags import URLNode, url as url_tag, url
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _, get_language

from cosinnus.conf import settings
from cosinnus.core.registries import app_registry, attached_object_registry
from cosinnus.models.group import CosinnusGroup, CosinnusGroupManager,\
    CosinnusSociety, CosinnusProject, CosinnusPortal
from cosinnus.utils.permissions import (check_ug_admin, check_ug_membership,
    check_ug_pending, check_object_write_access,
    check_group_create_objects_access, check_object_read_access, get_user_token,
    check_user_portal_admin)
from django.template.base import TemplateSyntaxError
from cosinnus.core.registries.group_models import group_model_registry
from django.core.cache import cache
from cosinnus.utils.urls import group_aware_reverse, get_domain_for_portal

import logging
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.templatetags.staticfiles import static
logger = logging.getLogger('cosinnus')

register = template.Library()


@register.filter
def is_group_admin(user, group):
    """Template filter to check if the given user is an admin of the given
    group.

    .. seealso:: func:`cosinnus.utils.permissions.check_ug_admin`
    """
    return check_ug_admin(user, group)


@register.filter
def is_group_member(user, group):
    """Template filter to check if the given user is a member of the given
    group.

    .. seealso:: func:`cosinnus.utils.permissions.check_ug_membership`
    """
    return check_ug_membership(user, group)


@register.filter
def is_group_pending(user, group):
    """Template filter to check if the given user is a member of the given
    group.

    .. seealso:: func:`cosinnus.utils.permissions.check_ug_membership`
    """
    return check_ug_pending(user, group)

@register.filter
def has_read_access(user, obj):
    """
    Template filter to check if an object (either CosinnusGroup or BaseTaggableObject)
    is visibible to a user.
    This factors in all aspects of superusers and group memberships.
    """
    return check_object_read_access(obj, user)

@register.filter
def has_write_access(user, obj):
    """
    Template filter to check if a user can edit/update/delete an object 
    (either CosinnusGroup or BaseTaggableObject).
    If a CosinnusGroup is supplied, this will check if the user is a group admin or a site admin.
    This factors in all aspects of superusers and group memberships.
    """
    return check_object_write_access(obj, user)

@register.filter
def can_create_objects_in(user, group):
    """
    Template filter to check if a user can create objects in a CosinnusGroup.
    This factors in all aspects of superusers and group memberships.
    """
    return check_group_create_objects_access(group, user)

@register.filter
def can_create_groups(user):
    """
    Template filter to check if a user can create CosinnusGroups.
    """
    return user.is_authenticated()

@register.filter
def is_portal_admin(user):
    """
    Template filter to check if a user is a portal admin.
    """
    return check_user_portal_admin(user)

@register.filter
def full_name(value):
    """Template filter to get a readable name for the given user

    .. code-block:: django

        {{ user|full_name }}

    :param AbstractBaseUser value: the user object
    :return: either the full user name or the login user name.
    """
    from django.contrib.auth.models import AbstractBaseUser
    if isinstance(value, AbstractBaseUser):
        if not value.is_active:
            return _("(Deleted User)")
        return value.get_full_name() or value.get_username()
    return ""

@register.filter
def profile_url(value):
    """Template filter to get the profile page url for a given user

    .. code-block:: django

        {{ user|profile_url }}

    :param AbstractBaseUser value: the user object
    :return: the url to the user's profile
    """
    from django.contrib.auth.models import AbstractBaseUser
    if isinstance(value, AbstractBaseUser):
        if not value.is_active:
            return "#"
        return reverse('cosinnus:profile-detail', kwargs={'username': value.username})
    return ""

@register.filter
def url_target_blank(link):
    """ Template filter that turns any html link into a target="_blank" link.
    """
    return mark_safe(link.replace('<a ', '<a target="_blank" '))


@register.filter
def multiply(value, arg):
    """Template filter to multiply two numbers
    """
    return value * arg

@register.filter
def subtract(value, arg):
    """Template filter to multiply two numbers
    """
    return value - arg

@register.filter
def intify(value):
    """Template filter to multiply two numbers
    """
    return int(value)

@register.simple_tag(takes_context=True)
def cosinnus_group_url_path(context, group=None):
    group = group or context.get('group', None)
    if group:
        return group_model_registry.group_type_index[group.type]
    else:
        return group_model_registry.get_default_group_key()


def _appsmenu_apps_sort_key(app_name):
    try:
        return settings.COSINNUS_APPS_MENU_ORDER.index(app_name)
    except Exception, e:
        return 999

@register.simple_tag(takes_context=True)
def cosinnus_menu(context, template="cosinnus/navbar.html"):
    if 'request' not in context:
        raise ImproperlyConfigured("Current request missing in rendering "
            "context. Include 'django.core.context_processors.request' in the "
            "TEMPLATE_CONTEXT_PROCESSORS.")

    request = context['request']
    user = request.user
    if user.is_authenticated():
        context['groups'] = CosinnusProject.objects.get_for_user(request.user)
        context['societies'] = CosinnusSociety.objects.get_for_user(request.user)
    
    try:
        current_app = resolve(request.path).app_name
    except Resolver404:
        pass
    active_app = None
    active_app_name = None
    if 'group' in context:
        group = context['group']
        apps = []
        for app, name, label in app_registry.items():
            if app in settings.COSINNUS_HIDE_APPS:
                continue
            #print ">>", "TODO: tags: filter for self.group.id for deactivated apps"
            if group.is_app_deactivated(app):
                continue
            
            url = group_aware_reverse('cosinnus:%s:index' % name, kwargs={'group': group})
            if app == current_app:
                active_app = app
                active_app_name = name
            apps.append({
                'active': app == current_app,
                'label': label,
                'url': url,
                'app': app,
            })
            
        apps = sorted(apps, key=lambda x: _appsmenu_apps_sort_key(x['app']))
        context.update({
            'apps': apps,
            'app_nav': True,
        })
        if group.type == CosinnusGroup.TYPE_PROJECT:
            context['appsmenu_group'] = group
        elif group.type == CosinnusGroup.TYPE_SOCIETY:
            context['appsmenu_society'] = group
    else:
        context['app_nav'] = False

    context.update({
        'active_app': active_app,
        'active_app_name': active_app_name,
    })
    return render_to_string(template, context)

@register.simple_tag(takes_context=True)
def cosinnus_render_widget(context, widget):
    """ Renders a given widget config and passes all context on to its template """
    flat = {}
    for d in context.dicts:
        flat.update(d)
    return mark_safe(widget.render(**flat))

@register.simple_tag(takes_context=True)
def cosinnus_render_attached_objects(context, source, filter=None):
    """
    Renders all attached files on a given source cosinnus object. This will
    collect and group all attached objects (`source.attached_objects`) by their
    model group and send them to the configured renderer for that model type
    (in each cosinnus app's `cosinnus_app.ATTACHABLE_OBJECT_RENDERERS`).

    :param source: the source object to check for attached objects
    :param filter: a comma seperated list of allowed Object types to be
        rendered. eg.: 'cosinnus_event.Event,cosinnus_file.FileEntry' will
        allow only Files and events to be rendered.
    """
    attached_objects = source.attached_objects.all()
    allowed_types = filter.replace(' ', '').split(',') if filter else []

    typed_objects = defaultdict(list)
    for att in attached_objects:
        attobj = att.target_object
        content_model = att.model_name
        if filter and content_model not in allowed_types:
            continue
        if attobj is not None:
            typed_objects[content_model].append(attobj)

    rendered_output = []
    for model_name, objects in six.iteritems(typed_objects):
        # find manager object for attached object type
        Renderer = attached_object_registry.get(model_name)  # Renderer is a class
        if Renderer:
            # pass the list to that manager and expect a rendered html string
            rendered_output.append(Renderer.render(context, objects))
        elif settings.DEBUG:
            rendered_output.append(_('<i>Renderer for %(model_name)s not found!</i>') % {
                'model_name': model_name
            })

    return ''.join(rendered_output)


@register.simple_tag(takes_context=True)
def cosinnus_render_single_object(context, object):
    """
    Render a single cosinnus BaseTaggableObject using the
     configured renderer for that model type
    (in each cosinnus app's `cosinnus_app.ATTACHABLE_OBJECT_RENDERERS`).

    :param object: the source object to render
    """
    model_name = object.__class__.__module__.split('.')[0] + '.' + object.__class__.__name__
    
    # find manager object for attached object type
    Renderer = attached_object_registry.get(model_name)  # Renderer is a class
    
    rendered_output = ''
    if Renderer:
        # pass the list to that manager and expect a rendered html string
        rendered_output = Renderer.render_single(context, object)
    elif settings.DEBUG:
        rendered_output = _('<i>Renderer for %(model_name)s not found!</i>') % {
            'model_name': model_name
        }

    return rendered_output


@register.inclusion_tag('cosinnus/autocomplete.html')
def cosinnus_autocomplete(field, objects):
    return {
        'field': field,
        'objects': objects
    }


class URLNodeOptional(URLNode):
    """
    Exactly the same as `django.template.defaulttags.url` *except* `kwargs`
    needs to evaluate to `True`. All other `kwargs` are removed. This allows a
    bit more flexibility than the use of `{% url %}`.

    .. seealso:: http://code.djangoproject.com/ticket/9176
    """
    def render(self, context):
        self.kwargs = {k: v for k, v in six.iteritems(self.kwargs) if v.resolve(context)}
        return super(URLNodeOptional, self).render(context)


@register.tag
def url_optional(parser, token):
    """
    Creates the default `URLNode`, then routes it through the optional resolver
    with the same properties by first creating the `URLNode`. The parsing stays
    in Django core where it belongs.
    """
    urlnode = url_tag(parser, token)
    return URLNodeOptional(urlnode.view_name, urlnode.args, urlnode.kwargs,
        urlnode.asvar)
    
@register.tag(name='captureas')
def do_captureas(parser, token):
    """
        Captures block content into template variables.
        Source: https://djangosnippets.org/snippets/545/
        Usage:
            {% captureas label %}{% trans "Posteingang" %}{% if unread_count %} <strong>({{ unread_count }})</strong>{% endif %}{% endcaptureas %}
            {% include "cosinnus/leftnav_button.html" label=label  %}
    """
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name.")
    nodelist = parser.parse(('endcaptureas',))
    parser.delete_first_token()
    return CaptureasNode(nodelist, args)


class CaptureasNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        output = self.nodelist.render(context)
        context[self.varname] = output
        return ""
    

@register.simple_tag(takes_context=True)
def strip_params(context, qs, *keys):
    """
    Given a URL query string (`foo=bar&lorem=ipsum`) and an arbitrary key /
    list of keys, strips those from the QS:
    """
    if isinstance(qs, six.string_types):
        parsed = dict(parse_qsl(qs))
    elif isinstance(qs, HttpRequest):
        from copy import copy
        parsed = copy(qs.GET.dict())
    else:
        parsed = {}
    for k in keys:
        parsed.pop(k, None)
    return urlencode(parsed)


@register.simple_tag(takes_context=True)
def add_current_params(context, request=None):
    """
    Given a URL query string (`foo=bar&lorem=ipsum`) and an arbitrary key /
    list of keys, strips those from the QS:
    """
    if not request and 'request' in context:
        request = context['request']
    if not request:
        return ''
    parsed = copy(request.GET.dict())
    if not parsed:
        return ''
    return '?%s' % urlencode(parsed)


@register.filter
def cosinnus_setting(user, setting):
    """
    Retrieves a user setting's value or an empty string if the setting does not exist yet.
    """
    from django.contrib.auth.models import AbstractBaseUser
    if isinstance(user, AbstractBaseUser):
        value = user.cosinnus_profile.settings.get(setting, None)
        return value
    raise ImproperlyConfigured("User setting tag got passed a non-user argument.")
    

@register.simple_tag(takes_context=True)
def cosinnus_user_token(context, token_name, request=None):
    """
    Returns URL params (`user=999&token=1234567`) for the current user and a 
    permanent token specific to the token_name. If the user does not have a token 
    for that token_name yet, one will be generated. 
    """
    if not request and 'request' in context:
        request = context['request']
    if not request or not request.user.is_authenticated:
        return ''
    token = get_user_token(request.user, token_name)
    return 'user=%s&token=%s' % (request.user.id, token)


@register.simple_tag(takes_context=True)
def cosinnus_cross_portal_token(context, portal):
    """
    Returns a token that will force the URL group resolution 
    (``cosinnus.core.decorators.views.get_group_for_request()``) into another portal on POST requests,
    while still being able to post to the domain of the current portal.
    This is very useful to avoid CSRF failures when posting i.e. comments on Notes from another
    CosinnusPortal's group that appeared in a user's stream in another portal.
    """
    if type(portal) is CosinnusPortal:
        portal_id = portal.id
    else:
        portal_id = int(portal)
    return '<input type="hidden" name="cosinnus_cross_portal" value="%s">' % portal_id


def group_aware_url_name(view_name, group_slug, portal_id=None):
    """ Modifies a URL name that points to a URL within a CosinnusGroup so that the URL
        points to the correct sub-url of the type of the CosinnusGroup Model for the given
        group slug.
        
        @return: A modified URL view name
    """
    # retrieve group type cached
    group_type = cache.get(CosinnusGroupManager._GROUP_SLUG_TYPE_CACHE_KEY % (CosinnusPortal.get_current().id, group_slug))
    if group_type is None:
        group_type = CosinnusGroup.objects.get(slug=group_slug, portal_id=portal_id).type
        cache.set(CosinnusGroupManager._GROUP_SLUG_TYPE_CACHE_KEY % (CosinnusPortal.get_current().id, group_slug), group_type,
                  31536000) # 1 year cache
        
    # retrieve that type's prefix and add to URL viewname
    prefix = group_model_registry.get_url_name_prefix_by_type(group_type, 0)
    if ":" in view_name:
        view_name = (":%s" % prefix).join(view_name.rsplit(":", 1))
    else:
        view_name = prefix + view_name
    
    return view_name



class GroupURLNode(URLNode):
    """ This URL node will adjust its view name to the prefix-type of the CosinnusGroup type. 
        Group type is found through the group slug, and looked up in the group-slug -> group-type cache.
        Group types never change, so this cache won't need smart resetting.
        ~Should~ be thread-safe.
        
        :param group: The group slug for the group's url you are targeting
        :param portal_id: (optional) can override the portal used.
        :ignoreErrors: (optional) if set to True, this tag will return silently '' instead of throwing a 
            DoesNotExist exception when the targeted group is not found
    """

    def render(self, context):
        
        if not hasattr(self, 'base_view_name'):
            self.base_view_name = copy(self.view_name)
        else:
            self.view_name = copy(self.base_view_name)
        view_name = self.view_name.resolve(context)
        
        ignoreErrors = 'ignoreErrors' in self.kwargs and self.kwargs.get('ignoreErrors').resolve(context) or False
        
        group_arg = self.kwargs["group"].resolve(context)
        group_slug = ""
        foreign_portal = None
        portal_id = getattr(self, '_portal_id', None)
        force_local_domain = getattr(self, '_force_local_domain', False)
        
        try:
            # the portal id if given to the tag can override the group's portal
            self._portal_id = self.kwargs["portal_id"].resolve(context)
            portal_id = self._portal_id
            del self.kwargs["portal_id"]
        except KeyError:
            pass
        
        try:
            # this will retain the local domain. useful for avoiding POSTs to cross-portal domains and CSRF-failing
            self._force_local_domain = bool(self.kwargs["force_local_domain"].resolve(context))
            force_local_domain = self._force_local_domain
            del self.kwargs["force_local_domain"]
        except KeyError:
            pass
        
        patched_group_slug_arg = None
        
        # we accept a group object or a group slug
        if issubclass(group_arg.__class__, CosinnusGroup):
            # determine the portal from the group
            group_slug = group_arg.slug
            
            # if not explicitly given, learn the portal id from the group
            if not portal_id:
                portal_id = group_arg.portal_id
                if not portal_id == CosinnusPortal.get_current().id:
                    foreign_portal = group_arg.portal
                    
            # we patch the variable given to the tag here, to restore the regular slug-passed-url-resolver functionality
            patched_group_slug_arg = deepcopy(self.kwargs['group'])
            patched_group_slug_arg.token += '.slug'
            patched_group_slug_arg.var.var += '.slug'
            patched_group_slug_arg.var.lookups = list(self.kwargs['group'].var.lookups) + ['slug']
        elif not isinstance(group_arg, six.string_types):
            raise TemplateSyntaxError("'group_url' tag requires a group kwarg that is a group or a slug! Have you passed one? (You passed: 'group=%s')" % group_arg)
        else:
            group_slug = group_arg
        
            
        # make sure we have the foreign portal. we might not have yet retrieved it if we had a portal id explicitly set
        if portal_id and not portal_id == CosinnusPortal.get_current().id and not foreign_portal:
            foreign_portal = CosinnusPortal.objects.get(id=portal_id)

        try:
            try:
                view_name = group_aware_url_name(view_name, group_slug, portal_id)
            except CosinnusGroup.DoesNotExist:
                # ignore errors if the group doesn't exist if it is inactive (return empty link)
                if ignoreErrors or (not group_arg.is_active):
                    return ''
                
                logger.error(u'Cosinnus__group_url_tag: Could not find group for: group_arg: %s, view_name: %s, group_slug: %s, portal_id: %s' % (str(group_arg), view_name, group_slug, portal_id))
                raise
            
            self.view_name.var = view_name
            self.view_name.token = "'%s'" % view_name
            
            # to retain django core code for rendering, we patch this node to look like a proper url node, 
            # with a slug argument.
            # and then restore it later, so that the node object can be reused for other group arguments 
            # if we didn't do that, this group node's group argument would have been replaced already, and
            # lost to other elements that use the group_url tag in a for-loop, for example
            # (we cannot store anything on the object itself, down that road madness lies)
            if patched_group_slug_arg:
                self.kwargs['group'], patched_group_slug_arg = patched_group_slug_arg, self.kwargs['group']
                
            ret_url = super(GroupURLNode, self).render(context)
            # swap back the patched arg for the original
            if patched_group_slug_arg:
                self.kwargs['group'] = patched_group_slug_arg
            
            if foreign_portal and not force_local_domain:
                domain = get_domain_for_portal(foreign_portal)
                # attach to either output or given "as" variable
                if self.asvar:
                    context[self.asvar] = domain + context[self.asvar]
                else:
                    ret_url = domain + ret_url
            
            return ret_url
        except:
            if ignoreErrors:
                return ''
            else:
                raise
        

@register.tag
def group_url(parser, token):
    """
    A proxy wrapper for the Django 'url' tag for URLs pointing to pages within a CosinnusGroup.
    This tag is aware of which type of group is being pointed to and will automatically chose
    the correct URL path specific for the group type, as configured with group_model_registry.py.
    
    Otherwise this uses the django 'url' tag definition.
    """
    
    urlnode = url(parser, token)
    
    if not "group" in urlnode.kwargs:
        raise TemplateSyntaxError("'group_url' tag requires a group kwarg!")
    
    return GroupURLNode(urlnode.view_name, urlnode.args, urlnode.kwargs, urlnode.asvar)


@register.simple_tag(takes_context=True)
def cosinnus_report_object_action(context, obj=None):
    if not context['request'].user.is_authenticated():
        return ''
    if not obj:
        return ''
    
    app_label = obj.__class__.__module__.split('.')[0]
    model_name = obj.__class__.__name__
    model_str = '%s.%s' % (app_label, model_name)
    if model_name.lower() == 'user':
        title = full_name(obj)
    else:
        title = getattr(obj, 'title', getattr(obj, 'name', None))
    if not title:
        title = force_text(obj)
    
    # mark_safe doesn't really seem to work here
    title = escape(title.replace('"', "'"))
    return mark_safe(' onclick=\'$.cosinnus.Feedback.cosinnus_report_object("%s", %d, "%s");\' ' % (model_str, obj.id, title))


@register.simple_tag()
def localized_js(path):
    """ Acts like the {% static ... %} tag, but returns a javascript file
        from the localized folder for the current language. 
        We add a parameter so the client caches each language seperately """
    lang = get_language()
    return static('js/locale/%s/%s' % (lang, path)) + '?lang=%s' % lang


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    ret = mark_safe(str(arg1) + str(arg2))
    return ret

