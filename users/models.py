from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class AmazonImageVerify(models.Model):
    user = models.ForeignKey(User,null=True,on_delete= models.CASCADE)
    a_image = models.ImageField(upload_to = 'amazon_images')
    

    def __str__(self):
        return str(self.a_image)
 
class FlipcartImageVerify(models.Model):
    user = models.ForeignKey(User,null=True,on_delete= models.CASCADE)
    f_image = models.ImageField(upload_to = 'flipcart_images')

    def __str__(self):
        return str(self.f_image)

class PointsForVerifiedUploads(models.Model):
    user = models.ForeignKey(User,null=True,on_delete= models.CASCADE)
    points = models.IntegerField(default=1)

    def __str__(self):
        return str(self.points)
    