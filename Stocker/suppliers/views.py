from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from .forms import SupplierForm, PurchaseOrderForm, PurchaseOrderItemAddForm, ReceiveItemForm 
from inventory.models import Product, StockMovement

class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = "suppliers/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        return (Supplier.objects.filter(owner=self.request.user)
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

    def get_queryset(self):
        return Supplier.objects.filter(owner=self.request.user)

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "suppliers/supplier_form.html"
    success_url = reverse_lazy("suppliers:supplier_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class SupplierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "suppliers.change_supplier"
    model = Supplier
    form_class = SupplierForm
    template_name = "suppliers/supplier_form.html"
    success_url = reverse_lazy("suppliers:supplier_list")

    def get_queryset(self):
        return Supplier.objects.filter(owner=self.request.user)

class SupplierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "suppliers.delete_supplier"
    model = Supplier
    template_name = "suppliers/supplier_confirm_delete.html"
    success_url = reverse_lazy("suppliers:supplier_list")

    def get_queryset(self):
        return Supplier.objects.filter(owner=self.request.user)

@method_decorator(login_required, name='dispatch')
class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = "suppliers/purchaseorder_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related("supplier").filter(owner=self.request.user)
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")


@method_decorator(login_required, name='dispatch')
class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "suppliers/purchaseorder_form.html"
    success_url = reverse_lazy("suppliers:purchaseorder_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


@login_required
def purchaseorder_detail(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.select_related("supplier"), pk=pk, owner=request.user)
    add_form = PurchaseOrderItemAddForm(user=request.user)
    if request.method == "POST" and "add_item" in request.POST and not po.is_closed:
        add_form = PurchaseOrderItemAddForm(request.POST, user=request.user)
        if add_form.is_valid():
            PurchaseOrderItem.objects.update_or_create(
                po=po,
                product=add_form.cleaned_data["product"],
                defaults={
                    "quantity_ordered": add_form.cleaned_data["quantity_ordered"],
                    "unit_cost": add_form.cleaned_data["unit_cost"],
                },
            )
            po.status = PurchaseOrder.STATUS_SUBMITTED
            po.save(update_fields=["status", "updated_at"])
            return redirect("suppliers:purchaseorder_detail", pk=po.pk)

    items = po.items.select_related("product").all()
    receive_forms = [ReceiveItemForm(initial={"item_id": it.id}) for it in items if it.remaining > 0]
    return render(request, "suppliers/purchaseorder_detail.html", {
        "po": po,
        "items": items,
        "add_form": add_form,
        "receive_forms": receive_forms,
    })


@login_required
def receive_item(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, owner=request.user)
    if request.method == "POST" and not po.is_closed:
        form = ReceiveItemForm(request.POST)
        if form.is_valid():
            item = get_object_or_404(PurchaseOrderItem, pk=form.cleaned_data["item_id"], po=po)
            qty = int(form.cleaned_data["quantity"])
            qty = max(0, min(qty, item.remaining))
            if qty > 0:
                # Apply to inventory
                StockMovement.apply(
                    product_id=item.product_id,
                    movement_type="IN",
                    qty=qty,
                    reason=f"PO#{po.pk}",
                    user=request.user,
                )
                item.quantity_received = (item.quantity_received or 0) + qty
                item.save(update_fields=["quantity_received"])
                po.recompute_status()
                po.save(update_fields=["status", "updated_at"])
    return redirect("suppliers:purchaseorder_detail", pk=po.pk)


