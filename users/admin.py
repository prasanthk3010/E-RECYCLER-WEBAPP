from django.contrib import admin
from .models import AmazonImageVerify,FlipcartImageVerify,PointsForVerifiedUploads

# Register your models here.

admin.site.register(AmazonImageVerify)
admin.site.register(FlipcartImageVerify)
admin.site.register(PointsForVerifiedUploads)
