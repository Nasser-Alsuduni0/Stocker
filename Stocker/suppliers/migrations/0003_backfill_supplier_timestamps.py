from django.db import migrations
from django.utils import timezone

def forwards(apps, schema_editor):
    Supplier = apps.get_model('suppliers', 'Supplier')
    now = timezone.now()
    Supplier.objects.filter(created_at__isnull=True).update(created_at=now)
    Supplier.objects.filter(updated_at__isnull=True).update(updated_at=now)

class Migration(migrations.Migration):
    dependencies = [
        ('suppliers', '0002_alter_supplier_options_supplier_created_at_and_more'),
    ]
    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]

