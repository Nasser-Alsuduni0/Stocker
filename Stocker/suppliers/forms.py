from django import forms
from .models import Supplier

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
