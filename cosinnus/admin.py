# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from cosinnus.models.group import CosinnusGroupMembership,\
    CosinnusSociety, CosinnusProject, CosinnusPortal, CosinnusPortalMembership,\
    CosinnusGroup, MEMBERSHIP_MEMBER, MEMBERSHIP_PENDING
from cosinnus.models.profile import get_user_profile_model
from cosinnus.models.tagged import AttachedObject
from cosinnus.models.cms import CosinnusMicropage


class SingleDeleteActionMixin(object):
    
    def get_actions(self, request):
        self.actions.append('really_delete_selected')
        actions = super(SingleDeleteActionMixin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        if queryset.count() == 1:
            message = _("1 %(object)s was deleted successfully") % \
                {'object': queryset.model._meta.verbose_name}
        else:
            message = _("%(number)d %(objects)s were deleted successfully") %  \
                {'number': queryset.count(), 'objects': queryset.model._meta.verbose_name_plural}
        self.message_user(request, message)
    really_delete_selected.short_description = _("Delete selected entries")



# group related admin

class MembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user_email', 'status', 'date',)
    list_filter = ('group', 'user', 'status',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'group__name')
    
admin.site.register(CosinnusGroupMembership, MembershipAdmin)



class PortalMembershipAdmin(admin.ModelAdmin):
    list_display = ('group', 'user_email', 'status', 'date',)
    list_filter = ('group', 'user', 'status',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'group__name')

admin.site.register(CosinnusPortalMembership, PortalMembershipAdmin)



""" Unused, because very inefficient with 2000+ users """
class MembershipInline(admin.StackedInline):
    model = CosinnusGroupMembership
    extra = 0


class CosinnusProjectAdmin(SingleDeleteActionMixin, admin.ModelAdmin):
    actions = ['convert_to_society', 'add_members_to_current_portal', 'move_members_to_current_portal']
    list_display = ('name', 'slug', 'portal', 'public',)
    list_filter = ('portal', 'public',)
    search_fields = ('name', )
    prepopulated_fields = {'slug': ('name', )}
    
    def convert_to_society(self, request, queryset):
        """ Converts this CosinnusGroup's type """
        converted_names = []
        slugs = []
        for group in queryset:
            group.type = CosinnusGroup.TYPE_SOCIETY
            group.save(allow_type_change=True)
            if group.type == CosinnusGroup.TYPE_SOCIETY:
                converted_names.append(group.name)
                slugs.append(group.slug)
        CosinnusGroup._clear_cache(slugs=slugs)
        message = _('The following Projects were converted to Societies:') + '\n' + ", ".join(converted_names)
        self.message_user(request, message)
    convert_to_society.short_description = _("Convert selected Projects to Societies")
    
    
    def add_members_to_current_portal(self, request, queryset, remove_all_other_memberships=False):
        """ Converts this CosinnusGroup's type """
        member_names = []
        members = []
        
        for group in queryset:
            group.clear_member_cache()
            members.extend(group.members)
        
        members = list(set(members))
        users = get_user_model().objects.filter(id__in=members)
        
        
        if remove_all_other_memberships:
            # delete all other portal memberships because users were supposed to be moved
            CosinnusPortalMembership.objects.filter(user__in=users).delete()
        else:
            # just add them, that means that pending statuses will be removed to be replaced by members statuses in a second
            CosinnusPortalMembership.objects.filter(status=MEMBERSHIP_PENDING, 
                    group=CosinnusPortal.get_current(), user__in=users).delete()
        for user in users:
            membership, created = CosinnusPortalMembership.objects.get_or_create(group=CosinnusPortal.get_current(), user=user, 
                    defaults={'status': MEMBERSHIP_MEMBER})
            # this ensures that join-signals for all members really arrive (for putting new portal members into the Blog, etc)
            post_save.send(sender=CosinnusPortalMembership, instance=membership, created=True)
            member_names.append('%s %s (%s)' % (user.first_name, user.last_name, user.email))
        
        
        message = _('The following Users were added to this portal:') + '\n' + ", ".join(member_names)
        self.message_user(request, message)
    add_members_to_current_portal.short_description = _("Add all members to this Portal")
    
    
    def move_members_to_current_portal(self, request, queryset):
        """ Converts this CosinnusGroup's type """
        self.add_members_to_current_portal(request, queryset, remove_all_other_memberships=True)
        message = _('In addition, the members were removed from all other Portals.')
        self.message_user(request, message)
    move_members_to_current_portal.short_description = _("Move all members to this Portal (removes all other memberships!)")
    
admin.site.register(CosinnusProject, CosinnusProjectAdmin)


class CosinnusSocietyAdmin(CosinnusProjectAdmin):
    
    actions = ['convert_to_project']
    
    def get_actions(self, request):
        actions = super(CosinnusSocietyAdmin, self).get_actions(request)
        del actions['convert_to_society']
        return actions
    
    def convert_to_project(self, request, queryset):
        """ Converts this CosinnusGroup's type """
        converted_names = []
        slugs = []
        for group in queryset:
            group.type = CosinnusGroup.TYPE_PROJECT
            group.save(allow_type_change=True)
            if group.type == CosinnusGroup.TYPE_PROJECT:
                converted_names.append(group.name)
                slugs.append(group.slug)
        CosinnusGroup._clear_cache(slugs=slugs)
        message = _('The following Societies were converted to Projects:') + '\n' + ", ".join(converted_names)
        self.message_user(request, message)
    convert_to_project.short_description = _("Convert selected Societies to Projects")
    
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("parent", )
        return super(CosinnusSocietyAdmin, self).get_form(request, obj, **kwargs)

admin.site.register(CosinnusSociety, CosinnusSocietyAdmin)


class CosinnusPortalAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'site', 'public')
    prepopulated_fields = {'slug': ('name', )}

admin.site.register(CosinnusPortal, CosinnusPortalAdmin)



class CosinnusMicropageAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'last_edited_by', 'last_edited')

admin.site.register(CosinnusMicropage, CosinnusMicropageAdmin)



admin.site.register(AttachedObject)


# user / user profile related admin

USER_PROFILE_MODEL = get_user_profile_model()
USER_MODEL = get_user_model()


class UserProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('settings',)

admin.site.register(get_user_profile_model(), UserProfileAdmin)


class UserProfileInline(admin.StackedInline):
    model = USER_PROFILE_MODEL
    readonly_fields = ('settings',)

class PortalMembershipInline(admin.TabularInline):
    model = CosinnusPortalMembership
    extra = 0
    
class GroupMembershipInline(admin.TabularInline):
    model = CosinnusGroupMembership
    extra = 0

class UserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline, PortalMembershipInline, GroupMembershipInline)
    actions = ['deactivate_users']
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    
    def deactivate_users(self, request, queryset):
        count = 0
        for user in queryset:
            user.is_active = False
            user.save()
            count += 1
        message = _('%d Users were deactivated successfully.') % count
        self.message_user(request, message)
    deactivate_users.short_description = _('Deactivate users (will keep all all items they created on the site)')
    

admin.site.unregister(USER_MODEL)
admin.site.register(USER_MODEL, UserAdmin)



class SpamUserModel(USER_MODEL):
    class Meta:
        proxy = True

class SpamUserAdmin(UserAdmin):

    def queryset(self, request):
        """ For non-admins, only show the routepoints from their caravan """
        qs = super(SpamUserAdmin, self).queryset(request)
        qs = qs.filter(cosinnus_profile__website__contains='.pl', is_active=True)
        return qs

admin.site.register(SpamUserModel, SpamUserAdmin)


