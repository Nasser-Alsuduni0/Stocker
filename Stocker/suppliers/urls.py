from django.urls import path
from . import views

app_name = "suppliers"

urlpatterns = [
    path("", views.SupplierListView.as_view(), name="supplier_list"),
    path("<int:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),
    path("new/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path("<int:pk>/edit/", views.SupplierUpdateView.as_view(), name="supplier_update"),
    path("<int:pk>/delete/", views.SupplierDeleteView.as_view(), name="supplier_delete"),
    # Purchase Orders
    path("po/", views.PurchaseOrderListView.as_view(), name="purchaseorder_list"),
    path("po/new/", views.PurchaseOrderCreateView.as_view(), name="purchaseorder_create"),
    path("po/<int:pk>/", views.purchaseorder_detail, name="purchaseorder_detail"),
    path("po/<int:pk>/receive/", views.receive_item, name="purchaseorder_receive"),
]

