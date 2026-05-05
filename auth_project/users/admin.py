from django.contrib import admin
from .models import User, Device, OutstandingToken, BlacklistedToken

admin.site.register(User)
admin.site.register(Device)
admin.site.register(OutstandingToken)
admin.site.register(BlacklistedToken)