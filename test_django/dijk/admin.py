from django.contrib import admin

# Register your models here.

from .models import Ville, Rue
admin.site.register(Ville)
admin.site.register(Rue)
