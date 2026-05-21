from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, Role


class ProfileInline(admin.StackedInline):
    """Встраиваемый профиль в страницу пользователя"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    # Укажите только те поля, которые есть в вашей модели
    fields = ['role', 'photo', 'bio', 'location']  # Измените под свои поля


class CustomUserAdmin(UserAdmin):
    """Кастомный админ для пользователей"""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_active')
    
    def get_role(self, obj):
        """Получение роли пользователя"""
        if hasattr(obj, 'profile') and obj.profile and obj.profile.role:
            return obj.profile.role.name
        return '-'
    get_role.short_description = 'Роль'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Админ-панель для профилей"""
    list_display = ('id', 'user', 'get_full_name', 'role', 'get_phone_or_email')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name')
    
    def get_full_name(self, obj):
        return obj.get_full_name() if hasattr(obj, 'get_full_name') else f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Полное имя'
    
    def get_phone_or_email(self, obj):
        """Показывает телефон или email"""
        if hasattr(obj, 'phone') and obj.phone:
            return obj.phone
        return obj.user.email if obj.user else '-'
    get_phone_or_email.short_description = 'Контакт'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Админ-панель для ролей"""
    list_display = ('id', 'name')
    search_fields = ('name',)


# Перерегистрируем модель User с нашим админом
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)