from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Supplier
from .forms import SupplierForm 

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = "suppliers/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        return (Supplier.objects
                .annotate(product_count=Count("products"))
                .filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q) | Q(website__icontains=q))
                .order_by("name"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx

class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = "suppliers/supplier_detail.html"
    context_object_name = "supplier"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sup = self.object
        ctx["products"] = sup.products.select_related("category").order_by("name")
        return ctx

class SupplierCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "suppliers.add_supplier"
    model = Supplier
    form_class = SupplierForm
    template_name = "suppliers/supplier_form.html"
    success_url = reverse_lazy("suppliers:supplier_list")

class SupplierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "suppliers.change_supplier"
    model = Supplier
    form_class = SupplierForm
    template_name = "suppliers/supplier_form.html"
    success_url = reverse_lazy("suppliers:supplier_list")

class SupplierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "suppliers.delete_supplier"
    model = Supplier
    template_name = "suppliers/supplier_confirm_delete.html"
    success_url = reverse_lazy("suppliers:supplier_list")


