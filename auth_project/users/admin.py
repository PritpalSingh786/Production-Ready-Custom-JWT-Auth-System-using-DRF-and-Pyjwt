from django.contrib import admin
from .models import User, Device


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'email', 'is_active', 'email_verified')
    list_display_links = ('id', 'user_id')
    readonly_fields = ('id',)  # This shows ID on edit page
    fields = ('id', 'user_id', 'email', 'password', 'is_active', 'email_verified')  # ID will be first


# class DeviceAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'device_name')
#     list_display_links = ('id', 'device_name')
#     readonly_fields = ('id',)
#     fields = ('id', 'user', 'device_name', 'device_id', 'ip_address')


admin.site.register(User, UserAdmin)
# admin.site.register(Device, DeviceAdmin)
admin.site.register(Device)
