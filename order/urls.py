# order/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet,
    LocationViewSet,
    InverterStatusViewSet,
    InverterViewSet,
    GeneratorViewSet,
    SiteContactViewSet,
    OrderViewSet,
    InverterSimDetailViewSet,
    InverterUtilizationStatusViewSet,
    InverterUtilizationViewSet,
    ServiceStatusViewSet,
    ServiceRecordsViewSet,
    UsageViewSet,
    UsageUploadView,
    InverterStatusSummaryView,
    InverterUsageReportView,
    ChecklistViewSet
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'inverter-statuses', InverterStatusViewSet)
router.register(r'inverters', InverterViewSet)
router.register(r'generators', GeneratorViewSet)
router.register(r'site-contacts', SiteContactViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'inverter-sim-details', InverterSimDetailViewSet)
router.register(r'inverter-utilization-statuses', InverterUtilizationStatusViewSet)
router.register(r'inverter-utilizations', InverterUtilizationViewSet)
router.register(r'service-statuses', ServiceStatusViewSet)
router.register(r'service-records', ServiceRecordsViewSet)
router.register(r'usages', UsageViewSet)
router.register(r'checklists', ChecklistViewSet)



urlpatterns = router.urls + [
    path("usages-upload/", UsageUploadView.as_view(), name="usage-upload"),
    path('api/inverter-status-summary/', InverterStatusSummaryView.as_view(), name='inverter-status-summary'),
   
    path("inverter-usage-report/<uuid:inverter_id>/", InverterUsageReportView.as_view()),
]

