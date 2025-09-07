from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, F, Case, When, IntegerField, DecimalField, ExpressionWrapper, Value 
from django.db.models.functions import Coalesce,TruncDate
from datetime import date, timedelta
from django.core.paginator import Paginator
from django.db.models import Q

from inventory.models import Product, StockMovement
from django.utils.translation import gettext as _
from .forms import UserProfileForm, PreferencesForm

def home(request):
    features = [
        {
            "title": _("Product Management"),
            "image": "images/features/product.png",
            "desc": _("Add, edit, and safely archive products. Track SKU, unit, cost/sell price, reorder level, and optional expiry date. Quick view and detailed pages included.")
        },
        {
            "title": _("Stock Management"),
            "image": "images/features/stock.png",
            "desc": _("Record IN/OUT/ADJUST movements with reasons and user stamps. Auto-update on-hand quantity and keep a full movement history for audits.")
        },
        {
            "title": _("Category Management"),
            "image": "images/features/category.png",
            "desc": _("Create, rename, and remove categories. Assign products to a single category and filter/search by category across the app.")
        },
        {
            "title": _("Supplier Management"),
            "image": "images/features/supplier.png",
            "desc": _("Store supplier details (logo, email, phone, website) and link them to products. See each supplier’s supplied items and recent activity.")
        },
        {
            "title": _("Reports & Analytics"),
            "image": "images/features/reports.png",
            "desc": _("Inventory snapshot, low-stock list, expiring-soon items, and supplier reports. Trends over time and CSV export for external analysis.")
        },
        {
            "title": _("Notifications & Alerts"),
            "image": "images/features/alerts.png",
            "desc": _("Email alerts for low stock and approaching expiry. Run the built-in daily job to notify managers before issues impact operations.")
        },
    ]
    return render(request, "main/home.html", {"features": features})

@login_required
def dashboard(request):
    value_expr = ExpressionWrapper(
        F("quantity_on_hand") * F("price_cost"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )

    agg = Product.objects.filter(owner=request.user).aggregate(
        total_products=Coalesce(Count("id"), Value(0)),
        total_on_hand=Coalesce(Sum("quantity_on_hand"), Value(0)),
        total_value=Coalesce(Sum(value_expr), Value(0), output_field=DecimalField(max_digits=14, decimal_places=2)),
        low_stock=Coalesce(
            Count(Case(When(quantity_on_hand__lte=F("reorder_level"), then=1), output_field=IntegerField())),
            Value(0),
        ),
    )

    stat_cards = [
        {"label": _("Total Products"),  "value": int(agg["total_products"] or 0)},
        {"label": _("On Hand (Sum)"),   "value": int(agg["total_on_hand"] or 0)},
        {"label": _("Inventory Value"), "value": f'{float(agg["total_value"] or 0):.2f}'},
        {"label": _("Low Stock"),       "value": int(agg["low_stock"] or 0)},
    ]

    recent_rows = (
        StockMovement.objects.select_related("product").filter(product__owner=request.user)
        .order_by("-created_at")[:6]
    )

   
    end = date.today()
    start = end - timedelta(days=29)
    mvs30 = StockMovement.objects.filter(product__owner=request.user, created_at__date__range=(start, end))
    daily = (
        mvs30.annotate(d=TruncDate("created_at"))
             .values("d")
             .annotate(
                 in_qty=Coalesce(Sum(Case(When(movement_type="IN",  then=F("quantity")), output_field=IntegerField())), Value(0)),
                 out_qty=Coalesce(Sum(Case(When(movement_type="OUT", then=F("quantity")), output_field=IntegerField())), Value(0)),
                 adj_qty=Coalesce(Sum(Case(When(movement_type="ADJ", then=F("quantity")), output_field=IntegerField())), Value(0)),
             )
             .order_by("d")
    )
    chart_labels = [row["d"].strftime("%Y-%m-%d") for row in daily]
    chart_in  = [int(row["in_qty"] or 0) for row in daily]
    chart_out = [int(row["out_qty"] or 0) for row in daily]
    chart_adj = [int(row["adj_qty"] or 0) for row in daily]
    chart_net = [i - o + a for i, o, a in zip(chart_in, chart_out, chart_adj)]


    q = (request.GET.get("q") or "").strip()
    qs = (
        Product.objects.select_related("category")
        .prefetch_related("suppliers")
        .filter(owner=request.user)
    )
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(category__name__icontains=q) |
            Q(suppliers__name__icontains=q)
        ).distinct()

  
    order = request.GET.get("o") or "-quantity_on_hand"
    qs = qs.order_by(order)

    per_page = int(request.session.get("items_per_page", 10))
    paginator = Paginator(qs, per_page)  
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "stat_cards": stat_cards,
        "recent_rows": recent_rows,
        "chart_labels": chart_labels,
        "chart_in": chart_in,
        "chart_out": chart_out,
        "chart_adj": chart_adj,
        "chart_net": chart_net,
        # table context
        "page_obj": page_obj,
        "q": q,
        "order": order,
    }
    return render(request, "main/dashboard.html", context)


@login_required
def settings_view(request):
    user = request.user
    profile_form = UserProfileForm(instance=user)
    prefs_initial = {"items_per_page": int(request.session.get("items_per_page", 10))}
    prefs_form = PreferencesForm(initial=prefs_initial)

    if request.method == "POST":
        if "save_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
        elif "save_prefs" in request.POST:
            prefs_form = PreferencesForm(request.POST)
            if prefs_form.is_valid():
                request.session["items_per_page"] = prefs_form.cleaned_data["items_per_page"]
    return render(request, "main/settings.html", {
        "profile_form": profile_form,
        "prefs_form": prefs_form,
    })