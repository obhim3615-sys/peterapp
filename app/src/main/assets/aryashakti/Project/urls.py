"""tracebility_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin

from django.conf import settings
from django.urls import  include,  path,re_path
from drf_yasg import openapi
from django.conf.urls.static import static
#from grappelli.urls import urlpatterns as grappelli_urls
from drf_yasg.views import get_schema_view
from app_farm.admin import bd_dash,exportBdManager,bd_dash_details
from recordActivity.admin import bd_activity_subtask,bd_activity_subtask_template
from certification_card.views import ComingSoon
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Arya Shakti API Docs",
        default_version='v1',
        description="API documentation",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

#admin.site.site_header = "AgTrace"
admin.site.site_title = "Arya"
admin.site.index_title = "Arya"

admin.autodiscover()
admin.site.enable_nav_sidebar = False

urlpatterns = [    
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('swagger/',
         schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),

    path('redoc/',
         schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
    path('admin/bd_dash/', bd_dash),    
    path('admin/export_bd_dash/', exportBdManager),
    path('admin/bd_dash_details/<str:name>/', bd_dash_details),
    path('admin/bd-activity-subtask/',bd_activity_subtask_template ),
    path('admin/bd-subtask-show/<id>',bd_activity_subtask ),
    path('admin/', admin.site.urls),
    #path('appapi/',include('appapp.urls')),
    path('api/',include('app_farm.urls')),
    path('api/v1/',include('app_farm.routes')),    
    path('api/v1/verify/',include('verification.urls')),    
    path('api/v1/onemoney/',include('onemoney.urls')),
    path('api/v1/record/',include('recordActivity.urls')),
    path('api/v1/pop/',include('pop_manage.urls')),
    path('api/v1/requests/',include('all_requests.urls')),
    path('api/v1/cms/',include('cms.urls')),
    path('api/v1/farm_category/',include('farm_category.urls')),
    path('api/v1/broadcast/',include('broadcast.urls')),
    path('vision/',include('vision.urls')),
    path('kisancard/<phonenumber>/', ComingSoon.as_view(),name='getcard'),
    path('api/v1/certification/',include('certification_card.urls')),
    path('api/v1/subscription_service/',include('subscription_service.urls')),
    path('api/v1/payment/',include('payment.urls')),
    path('api/v1/sponsor/',include('sponsor.urls')),
    path('api/v1/survey/',include('survey.urls')),
    path('api/v1/core/',include('core.urls')),
    path('api/v1/procurement/',include('procurement.urls')),
    path('api/v1/insurance/',include('insurance.urls')),

    #-------------------Desktop views--------------------#
    path('dashboard/', include('webdashboard.urls')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
]
urlpatterns=urlpatterns + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
urlpatterns=urlpatterns + static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)

# if settings.DEBUG:
#     urlpatterns += path('__debug__/', include('debug_toolbar.urls')),

#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
