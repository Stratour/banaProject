from django.contrib import admin
from .models import Members 

@admin.register(Members) 
class MembersAdmin(admin.ModelAdmin): 
    list_display = ('memb_user_fk',) 
    search_fields = ('memb_user_fk__id','memb_gender',)
# Register your models here.
