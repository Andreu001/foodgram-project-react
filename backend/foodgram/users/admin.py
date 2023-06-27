from django.contrib import admin

from .models import User


@admin.register(User)
class UsersAdmin(admin.ModelAdmin):
    """ Админ панель управление пользователями """
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')
    ordering = ('username', )
    empty_value_display = '-пусто-'
