from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from datetime import timedelta
from django.utils import timezone
from django.db.models import (
    Q, Count, F, Sum, Case, When, IntegerField, DecimalField, ExpressionWrapper, Value as V
)
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .models import Product, StockMovement, Category
from .forms import ProductForm, StockAdjustForm, CategoryForm
from suppliers.models import Supplier  # for supplier summaries in reports

import csv

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related("category").order_by("name")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(sku__icontains=q) |
                Q(category__name__icontains=q)
            )
        status = self.request.GET.get("status")
        if status == "low":
            qs = qs.filter(quantity_on_hand__lte=F("reorder_level"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status"] = self.request.GET.get("status", "")
        return ctx

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "inventory/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["movements"] = self.object.movements.all()[:20]
        ctx["form"] = StockAdjustForm()
        return ctx

class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "inventory.add_product"
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")

class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "inventory.change_product"
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "inventory.delete_product"
    model = Product
    template_name = "inventory/product_confirm_delete.html"
    success_url = reverse_lazy("inventory:product_list")

@login_required
@permission_required("inventory.add_stockmovement", raise_exception=True)
def adjust_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = StockAdjustForm(request.POST)
        if form.is_valid():
            mv = StockMovement.apply(
                product_id=product.id,
                movement_type=form.cleaned_data["movement_type"],
                qty=form.cleaned_data["quantity"],
                reason=form.cleaned_data["reason"],
                user=request.user,
            )
            return redirect("inventory:product_detail", pk=product.pk)
    else:
        form = StockAdjustForm()
    return render(request, "inventory/stock_adjust_form.html", {"product": product, "form": form})

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "inventory/category_list.html"
    context_object_name = "categories"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        return (Category.objects
                .annotate(product_count=Count("products"))
                .filter(Q(name__icontains=q) | Q(description__icontains=q))
                .order_by("name"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx

class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "inventory.add_category"
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:category_list")

class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "inventory.change_category"
    model = Category
    form_class = CategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:category_list")

class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "inventory.delete_category"
    model = Category
    template_name = "inventory/category_confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")

def _parse_dates(request):
    """Parse ?start=YYYY-MM-DD&end=YYYY-MM-DD; default = last 30 days (inclusive)."""
    today = timezone.localdate()
    default_start = today - timedelta(days=29)
    s = request.GET.get("start")
    e = request.GET.get("end")
    try:
        start = timezone.datetime.fromisoformat(s).date() if s else default_start
    except Exception:
        start = default_start
    try:
        end = timezone.datetime.fromisoformat(e).date() if e else today
    except Exception:
        end = today
    if start > end:
        start, end = end, start
    return start, end

class ReportsView(TemplateView):
    template_name = "inventory/reports.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(next=request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        start, end = _parse_dates(self.request)

        # INVENTORY SUMMARY
        value_expr = ExpressionWrapper(
            F("quantity_on_hand") * F("price_cost"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        inv_agg = Product.objects.aggregate(
            total_products=Count("id"),
            total_on_hand=Coalesce(Sum("quantity_on_hand"), V(0)),
            total_value=Coalesce(Sum(value_expr), V(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            low_stock=Count(
                Case(
                    When(quantity_on_hand__lte=F("reorder_level"), then=1),
                    output_field=IntegerField(),
                )
            ),
        )

        category_rows = (
            Product.objects
            .values("category__id", "category__name")
            .annotate(
                product_count=Count("id"),
                on_hand=Coalesce(Sum("quantity_on_hand"), V(0)),
                value=Coalesce(Sum(value_expr), V(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            )
            .order_by("category__name")
        )

        mvs = StockMovement.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        mv_agg = mvs.aggregate(
            in_qty=Coalesce(Sum(Case(When(movement_type="IN", then=F("quantity")), output_field=IntegerField())), V(0)),
            out_qty=Coalesce(Sum(Case(When(movement_type="OUT", then=F("quantity")), output_field=IntegerField())), V(0)),
            adj_qty=Coalesce(Sum(Case(When(movement_type="ADJ", then=F("quantity")), output_field=IntegerField())), V(0)),
        )
        mv_agg["net_change"] = mv_agg["in_qty"] - mv_agg["out_qty"] + mv_agg["adj_qty"]

        recent_movements = (
            mvs.select_related("product")
               .order_by("-created_at")[:20]
        )

        p_val_expr = ExpressionWrapper(
            F("products__quantity_on_hand") * F("products__price_cost"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        supplier_rows = (
            Supplier.objects
            .annotate(
                product_count=Count("products", distinct=True),
                on_hand=Coalesce(Sum("products__quantity_on_hand"), V(0)),
                value=Coalesce(Sum(p_val_expr), V(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
            )
            .order_by("name")
        )

        daily = (
            mvs.annotate(d=TruncDate("created_at"))
               .values("d")
               .annotate(
                   in_qty=Coalesce(Sum(Case(When(movement_type="IN", then=F("quantity")), output_field=IntegerField())), V(0)),
                   out_qty=Coalesce(Sum(Case(When(movement_type="OUT", then=F("quantity")), output_field=IntegerField())), V(0)),
                   adj_qty=Coalesce(Sum(Case(When(movement_type="ADJ", then=F("quantity")), output_field=IntegerField())), V(0)),
               )
               .order_by("d")
        )
        
        chart_mov_labels = [row["d"].strftime("%Y-%m-%d") for row in daily]
        chart_mov_in  = [int(row["in_qty"] or 0)  for row in daily]
        chart_mov_out = [int(row["out_qty"] or 0) for row in daily]
        chart_mov_adj = [int(row["adj_qty"] or 0) for row in daily]
        chart_mov_net = [i - o + a for i, o, a in zip(chart_mov_in, chart_mov_out, chart_mov_adj)]
        
        cat_labels = []
        cat_values = []
        for r in category_rows:
            cat_labels.append(r["category__name"] or "Uncategorized")
            cat_values.append(float(r["value"] or 0))
        
        top_suppliers = list(supplier_rows[:8])
        sup_labels = [s.name for s in top_suppliers]
        sup_values = [float(s.value or 0) for s in top_suppliers]
        
        ctx.update({
            "chart_mov_labels": chart_mov_labels,
            "chart_mov_in": chart_mov_in,
            "chart_mov_out": chart_mov_out,
            "chart_mov_adj": chart_mov_adj,
            "chart_mov_net": chart_mov_net,
            "chart_cat_labels": cat_labels,
            "chart_cat_values": cat_values,
            "chart_sup_labels": sup_labels,
            "chart_sup_values": sup_values,
        })

        low_stock_list = (
            Product.objects
            .filter(quantity_on_hand__lte=F("reorder_level"))
            .select_related("category")
            .order_by("name")[:20]
        )

        ctx.update({
            "start": start, "end": end,
            "inv": inv_agg,
            "category_rows": category_rows,
            "mv": mv_agg,
            "recent_movements": recent_movements,
            "supplier_rows": supplier_rows,
            "low_stock_list": low_stock_list,
        })
        return ctx


@login_required
def inventory_report_csv(request):
    """Export products inventory CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory_report.csv"'
    writer = csv.writer(response)
    writer.writerow(["SKU","Name","Category","On hand","Reorder level","Cost","Valuation","Low stock?"])
    qs = Product.objects.select_related("category").order_by("name")
    for p in qs:
        valuation = (p.quantity_on_hand or 0) * (p.price_cost or 0)
        writer.writerow([
            p.sku, p.name, getattr(p.category, "name", "") or "",
            p.quantity_on_hand, p.reorder_level,
            p.price_cost, f"{valuation:.2f}",
            "Yes" if p.quantity_on_hand <= p.reorder_level else "No",
        ])
    return response


@login_required
def supplier_report_csv(request):
    """Export supplier summary CSV."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="supplier_report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Supplier","Products","On hand (sum)","Valuation (cost)"])
    p_val_expr = ExpressionWrapper(
        F("products__quantity_on_hand") * F("products__price_cost"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    qs = (
        Supplier.objects
        .annotate(
            product_count=Count("products", distinct=True),
            on_hand=Coalesce(Sum("products__quantity_on_hand"), V(0)),
            value=Coalesce(Sum(p_val_expr), V(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
        )
        .order_by("name")
    )
    for s in qs:
        writer.writerow([s.name, s.product_count, s.on_hand, f"{s.value:.2f}"])
    return response