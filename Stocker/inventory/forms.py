from django import forms
from .models import Product, MOVEMENT_TYPES ,Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name","sku","category","description","unit",
            "price_cost","price_sale","reorder_level",
            "quantity_on_hand","expiry_date",
            "suppliers",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " w-full rounded-lg border px-3 py-2 text-sm").strip()

class StockAdjustForm(forms.Form):
    movement_type = forms.ChoiceField(choices=MOVEMENT_TYPES)
    quantity = forms.IntegerField(min_value=1)
    reason = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={"placeholder":"Reason (optional)"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " rounded-lg border px-3 py-2 text-sm").strip()

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " w-full rounded-lg border px-3 py-2 text-sm").strip()
        self.fields["description"].widget.attrs.setdefault("rows", 3)