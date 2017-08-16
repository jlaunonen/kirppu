from __future__ import unicode_literals, print_function, absolute_import

import json

from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.html import escape, format_html
from django.utils.translation import ugettext_lazy as ugettext, ngettext

from .forms import (
    ClerkGenerationForm,
    ReceiptItemAdminForm,
    ReceiptAdminForm,
    UITextForm,
    ClerkEditForm,
    ClerkSSOForm,
    VendorSetSelfForm,
)

from .models import (
    Clerk,
    Item,
    Vendor,
    Counter,
    Receipt,
    ReceiptExtraRow,
    ReceiptItem,
    ReceiptNote,
    UIText,
    ItemStateLog,
    Box,
)

__author__ = 'jyrkila'


def _gen_ean(modeladmin, request, queryset):
    for item in queryset:
        if item.code is None or len(item.code) == 0:
            item.code = Item.gen_barcode()
            item.save(update_fields=["code"])
_gen_ean.short_description = ugettext(u"Generate bar codes for items missing it")


def _del_ean(modeladmin, request, queryset):
    queryset.update(code="")
_del_ean.short_description = ugettext(u"Delete generated bar codes")


def _regen_ean(modeladmin, request, queryset):
    _del_ean(modeladmin, request, queryset)
    _gen_ean(modeladmin, request, queryset)
_regen_ean.short_description = ugettext(u"Re-generate bar codes for items")


class FieldAccessor(object):
    """
    Abstract base class for field-links to be used in Admin.list_display.
    Sub-classes must implement __call__ that is used to generate the field text / link.
    """
    def __init__(self, field_name, description):
        """
        :param field_name: Field to link to.
        :type field_name: str
        :param description: Column description.
        :type description: str
        """
        self._field_name = field_name
        self._description = description

    def __call__(self, obj):
        """
        :param obj: Model object from the query.
        :rtype: str
        :return: Unsafe string containing the field value.
        """
        raise NotImplementedError

    @property
    def short_description(self):
        return self._description

    def __str__(self):
        # Django 1.9 converts the field to string for id.
        return self._field_name

    @property
    def __name__(self):
        # Django 1.10 lookups the field name via __name__.
        return self._field_name


class RefLinkAccessor(FieldAccessor):
    """
    Accessor function that returns a link to given FK-field admin.
    """
    def __call__(self, obj):
        field = getattr(obj, self._field_name)
        if field is None:
            return u"(None)"
        # noinspection PyProtectedMember
        info = field._meta.app_label, field._meta.model_name
        return format_html(
            u'<a href="{0}">{1}</a>',
            reverse("admin:%s_%s_change" % info, args=(field.id,)),
            escape(field)
        )


"""
Admin UI list column that displays user name with link to the user model itself.

:param obj: Object being listed, such as Clerk or Vendor.
:type obj: Clerk | Vendor | T
:return: Contents for the field.
:rtype: unicode
"""
_user_link = RefLinkAccessor("user", ugettext(u"User"))


class VendorAdmin(admin.ModelAdmin):
    ordering = ('user__first_name', 'user__last_name')
    search_fields = ['id', 'user__first_name', 'user__last_name', 'user__username']
    list_display = ['id', _user_link, "terms_accepted"]

    @staticmethod
    def _can_set_user(request, obj):
        return obj is not None and\
            request.user.is_superuser and\
            not obj.user.is_superuser and\
            settings.KIRPPU_SU_AS_USER

    def get_form(self, request, obj=None, **kwargs):
        if self._can_set_user(request, obj):
            kwargs["form"] = VendorSetSelfForm
        return super(VendorAdmin, self).get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        fields = ["user"] if obj is not None and not self._can_set_user(request, obj) else []
        fields.append("terms_accepted")
        return fields

admin.site.register(Vendor, VendorAdmin)


class ClerkEditLink(FieldAccessor):
    def __call__(self, obj):
        """
        :type obj: Clerk
        :return:
        """
        value = getattr(obj, self._field_name)
        info = obj._meta.app_label, obj._meta.model_name
        if obj.user is None:
            return escape(value)
        else:
            return format_html(
                u'<a href="{0}">{1}</a>',
                reverse("admin:%s_%s_change" % info, args=(obj.id,)),
                escape(value)
            )


_clerk_id_link = ClerkEditLink("id", ugettext("ID"))
_clerk_access_code_link = ClerkEditLink("access_code", ugettext("Access code"))


# noinspection PyMethodMayBeStatic
class ClerkAdmin(admin.ModelAdmin):
    uses_sso = settings.KIRPPU_USE_SSO  # Used by the overridden template.
    actions = ["_gen_clerk_code", "_del_clerk_code", "_move_clerk_code"]
    list_display = (_clerk_id_link, _user_link, _clerk_access_code_link, 'access_key', 'is_enabled')
    ordering = ('user__first_name', 'user__last_name')
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    exclude = ['access_key']
    list_display_links = None

    def _gen_clerk_code(self, request, queryset):
        for clerk in queryset:
            if not clerk.is_valid_code:
                clerk.generate_access_key()
                clerk.save(update_fields=["access_key"])
    _gen_clerk_code.short_description = ugettext(u"Generate missing Clerk access codes")

    def _del_clerk_code(self, request, queryset):
        for clerk in queryset:
            while True:
                clerk.generate_access_key(disabled=True)
                try:
                    clerk.save(update_fields=["access_key"])
                except IntegrityError:
                    continue
                else:
                    break
    _del_clerk_code.short_description = ugettext(u"Delete Clerk access codes")

    def _move_error(self, request):
        self.message_user(request,
                          ugettext(u"Must select exactly one 'unbound' and one 'bound' Clerk for this operation"),
                          messages.ERROR)

    @transaction.atomic
    def _move_clerk_code(self, request, queryset):
        if len(queryset) != 2:
            self._move_error(request)
            return

        # Guess the order.
        unbound = queryset[0]
        bound = queryset[1]
        if queryset[1].user is None:
            # Was wrong, swap around.
            bound, unbound = unbound, bound

        if unbound.user is not None or bound.user is None:
            # Selected wrong rows.
            self._move_error(request)
            return

        # Assign the new code to be used. Remove the unbound item first, so unique-check doesn't break.
        bound.access_key = unbound.access_key

        self.log_access_key_move(request, unbound, bound)
        unbound.delete()
        bound.save(update_fields=["access_key"])

        self.message_user(request, ugettext(u"Access code set for '{0}'").format(bound.user))
    _move_clerk_code.short_description = ugettext(u"Move unused access code to existing Clerk.")

    def get_form(self, request, obj=None, **kwargs):
        # Custom creation form if SSO is enabled.
        if "sso" in request.GET and self.uses_sso:
            return ClerkSSOForm

        # Custom form for editing already created Clerks.
        if obj is not None:
            return ClerkEditForm

        return super(ClerkAdmin, self).get_form(request, obj, **kwargs)

    def has_change_permission(self, request, obj=None):
        # Don't allow changing unbound Clerks. That might create unusable codes (because they are not printed).
        if obj is not None and obj.user is None:
            return False
        return True

    def save_related(self, request, form, formsets, change):
        if isinstance(form, (ClerkEditForm, ClerkSSOForm)):
            # No related fields...
            return
        return super(ClerkAdmin, self).save_related(request, form, formsets, change)

    def save_model(self, request, obj, form, change):
        if change and isinstance(form, ClerkEditForm):
            # Need to save the form instead of obj.
            form.save()
        else:
            super(ClerkAdmin, self).save_model(request, obj, form, change)

    def get_urls(self):
        info = self.opts.app_label, self.opts.model_name
        return super(ClerkAdmin, self).get_urls() + [
            url(r'^bulk_unbound$', self.bulk_add_unbound, name="%s_%s_bulk" % info)
        ]

    def bulk_add_unbound(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        from .util import get_form
        form = get_form(ClerkGenerationForm, request)

        if request.method == 'POST' and form.is_valid():
            objs = form.generate()
            self.log_bulk_addition(request, objs)

            msg = format_html(
                ngettext('One unbound clerk added.', '{count} unbound clerks added.', form.get_count()),
                count=form.get_count()
            )
            self.message_user(request, msg, messages.SUCCESS)

            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse("admin:%s_%s_changelist" % (self.opts.app_label, self.opts.model_name)))

        from django.contrib.admin.helpers import AdminForm
        admin_form = AdminForm(
            form,
            form.get_fieldsets(),
            {},
            {},
            model_admin=self)
        media = self.media + admin_form.media

        context = dict(
            self.admin_site.each_context(request),
            title=force_text(ugettext('Add unbound clerk')),
            media=media,
            adminform=admin_form,
            is_popup=False,
            show_save_and_continue=False,
        )

        return self.render_change_form(request, context)

    def log_bulk_addition(self, request, objects):
        # noinspection PyProtectedMember
        change_message = json.dumps([{
            'added': {
                'name': force_text(added_object._meta.verbose_name),
                'object': force_text(added_object),
            }
        } for added_object in objects])

        from .util import shorten_text
        object_repr = ", ".join([shorten_text(force_text(added_object), 5) for added_object in objects])

        return LogEntry.objects.create(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(objects[0]).pk,
            object_repr=object_repr[:200],
            action_flag=ADDITION,
            change_message=change_message,
        )

    def log_access_key_move(self, request, unbound, target):
        # noinspection PyProtectedMember
        change_message = [{
            'changed': {
                'name': force_text(target._meta.verbose_name),
                'object': force_text(target),
                'fields': ["access_key"],
            },
            'deleted': {
                'name': force_text(unbound._meta.verbose_name),
                'object': force_text(unbound)
            }
        }]
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(target).pk,
            object_id=target.pk,
            object_repr=force_text(target),
            action_flag=CHANGE,
            change_message=change_message,
        )


admin.site.register(Clerk, ClerkAdmin)

admin.site.register(Counter)
admin.site.register(ReceiptExtraRow)


class UITextAdmin(admin.ModelAdmin):
    model = UIText
    ordering = ["identifier"]
    form = UITextForm
    list_display = ["identifier", "text_excerpt"]

admin.site.register(UIText, UITextAdmin)


class ItemAdmin(admin.ModelAdmin):
    actions = [_gen_ean, _del_ean, _regen_ean]
    list_display = ('name', 'code', 'price', 'state', RefLinkAccessor('vendor', ugettext("Vendor")))
    ordering = ('vendor', 'name')
    search_fields = ['name', 'code']
admin.site.register(Item, ItemAdmin)


class ReceiptItemAdmin(admin.TabularInline):
    model = ReceiptItem
    ordering = ["add_time"]
    form = ReceiptItemAdminForm
    readonly_fields = ["item"]


class ReceiptExtraAdmin(admin.TabularInline):
    model = ReceiptExtraRow


class ReceiptNoteAdmin(admin.TabularInline):
    model = ReceiptNote
    ordering = ["timestamp"]
    readonly_fields = ["clerk", "text"]


class ReceiptAdmin(admin.ModelAdmin):
    inlines = [
        ReceiptItemAdmin,
        ReceiptExtraAdmin,
        ReceiptNoteAdmin,
    ]
    ordering = ["clerk", "start_time"]
    list_display = ["__str__", "status", "total", "counter", "end_time"]
    list_filter = [
        ("type", admin.ChoicesFieldListFilter),
    ]
    form = ReceiptAdminForm
    search_fields = ["items__code", "items__name"]
    actions = ["re_calculate_total"]

    def re_calculate_total(self, request, queryset):
        for i in queryset:  # type: Receipt
            i.calculate_total()
            i.save(update_fields=["total"])
    re_calculate_total.short_description = "Re-calculate total sum of receipt"

    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(Receipt, ReceiptAdmin)


class ItemStateLogAdmin(admin.ModelAdmin):
    model = ItemStateLog
    ordering = ["-id"]
    search_fields = ['item__code', 'clerk__user__username']
    list_display = ['id', 'time',
                    RefLinkAccessor("item", ugettext("Item")),
                    'old_state', 'new_state',
                    RefLinkAccessor("clerk", ugettext("Clerk")),
                    'counter']

admin.site.register(ItemStateLog, ItemStateLogAdmin)

admin.site.register(Box)
