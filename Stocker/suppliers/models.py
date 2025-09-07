from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Supplier(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="suppliers/logos/", blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="supplier_owner_name_unique"),
        ]


class PurchaseOrder(models.Model):
    STATUS_DRAFT = "DRAFT"
    STATUS_SUBMITTED = "SUBMITTED"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_RECEIVED = "RECEIVED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_PARTIAL, "Partially Received"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchase_orders")
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    order_date = models.DateField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    invoice_number = models.CharField(max_length=80, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO#{self.pk} - {self.supplier.name}"

    @property
    def is_closed(self):
        return self.status in {self.STATUS_RECEIVED, self.STATUS_CANCELLED}

    def recompute_status(self):
        items = list(self.items.all())
        if not items:
            self.status = self.STATUS_DRAFT
            return
        all_recv = all((it.quantity_received or 0) >= (it.quantity_ordered or 0) for it in items)
        any_recv = any((it.quantity_received or 0) > 0 for it in items)
        if all_recv:
            self.status = self.STATUS_RECEIVED
        elif any_recv:
            self.status = self.STATUS_PARTIAL
        else:
            # keep submitted if already submitted, else draft
            if self.status not in (self.STATUS_SUBMITTED,):
                self.status = self.STATUS_DRAFT


class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["po", "product"], name="po_product_unique")
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity_ordered}"

    @property
    def remaining(self):
        return max(0, (self.quantity_ordered or 0) - (self.quantity_received or 0))

    def __str__(self):
        return self.name


