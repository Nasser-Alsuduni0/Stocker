from django.db import models, transaction
from django.contrib.auth import get_user_model
from suppliers.models import Supplier 

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

UNIT_CHOICES = [
    ("PCS", "Pieces"), ("BOX", "Box"), ("KG", "Kilogram"), ("L", "Liter"),
]

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=8, choices=UNIT_CHOICES, default="PCS")
    price_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_sale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    quantity_on_hand = models.IntegerField(default=0)  
    expiry_date = models.DateField(null=True, blank=True)
    suppliers = models.ManyToManyField("suppliers.Supplier", blank=True, related_name="products")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.reorder_level

MOVEMENT_TYPES = [
    ("IN", "Stock In"),
    ("OUT", "Stock Out"),
    ("ADJ", "Adjustment"),
]

class StockMovement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  
    reason = models.CharField(max_length=200, blank=True)
    resulting_quantity = models.IntegerField(default=0)  
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} on {self.product}"

    @staticmethod
    @transaction.atomic
    def apply(product_id, movement_type, qty, reason, user):
        
        prod = Product.objects.select_for_update().get(pk=product_id)
        if movement_type == "IN":
            new_q = prod.quantity_on_hand + abs(qty)
        elif movement_type == "OUT":
            new_q = prod.quantity_on_hand - abs(qty)
        else:  # ADJ
            new_q = prod.quantity_on_hand + qty 

        prod.quantity_on_hand = new_q
        prod.save(update_fields=["quantity_on_hand", "updated_at"])

        mv = StockMovement.objects.create(
            product=prod,
            movement_type=movement_type,
            quantity=qty,
            reason=reason or "",
            resulting_quantity=new_q,
            created_by=user if user and user.is_authenticated else None,
        )
        return mv
