from django import forms
from .models import Supplier
from .models import PurchaseOrder, PurchaseOrderItem

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name","logo","email","phone","website","address","notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            cls = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (cls + " w-full rounded-lg border px-3 py-2 text-sm").strip()
        self.fields["address"].widget.attrs.setdefault("rows", 2)
        self.fields["notes"].widget.attrs.setdefault("rows", 3)


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "expected_date", "notes", "invoice_number", "invoice_date"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            cls = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (cls + " w-full rounded-lg border px-3 py-2 text-sm").strip()
        if user is not None and "supplier" in self.fields:
            self.fields["supplier"].queryset = self.fields["supplier"].queryset.filter(owner=user)


class PurchaseOrderItemAddForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ["product", "quantity_ordered", "unit_cost"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            cls = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (cls + " w-full rounded-lg border px-3 py-2 text-sm").strip()
        if user is not None and "product" in self.fields:
            self.fields["product"].queryset = self.fields["product"].queryset.filter(owner=user).order_by("name")


class ReceiveItemForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls = self.fields["quantity"].widget.attrs.get("class", "")
        self.fields["quantity"].widget.attrs["class"] = (cls + " w-full rounded-lg border px-3 py-2 text-sm").strip()
