from django.urls import path
from django.contrib import admin

urlpatterns = [
    # Examples:
    # url(r'^$', 'trackmodels_proj.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    path(r'admin/', admin.site.urls),
]
