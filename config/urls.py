from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

# Admin site customization
admin.site.site_header = "DecisionOS Admin"
admin.site.site_title = "DecisionOS"
admin.site.index_title = "Dashboard"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('decisions/', include('decisions.urls')),
    path('', RedirectView.as_view(url='/decisions/', permanent=False)),
]
