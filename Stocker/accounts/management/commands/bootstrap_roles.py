from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = "Create Admin and Employee groups with proper permissions"

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        employee_group, _ = Group.objects.get_or_create(name='Employee')

        admin_perms = Permission.objects.filter(
            content_type__app_label__in=['inventory', 'suppliers']
        )
        admin_group.permissions.set(admin_perms)

        perms = Permission.objects.filter(codename__in=[
            'view_product', 'add_product', 'change_product',
            'view_stockmovement', 'add_stockmovement',
            'view_category', 'view_supplier'
        ])
        employee_group.permissions.set(perms)

        self.stdout.write(self.style.SUCCESS("Groups ready: Admin & Employee"))
