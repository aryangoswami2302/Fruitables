from django.db import models
from django.utils import timezone

# Create your models here.
class user(models.Model):
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    mobile = models.PositiveIntegerField()
    address = models.TextField()
    profile_picture = models.ImageField(upload_to='profile_pictures/')
    usertype = models.CharField(max_length=100, default='buyer')

    def __str__(self):
        return self.fname + ' ' + self.lname

class product(models.Model):
    seller = models.ForeignKey(user, on_delete=models.CASCADE)
    catagory = (
        ('fruits', 'Fruits'),
        ('vegetables', 'Vegetables'),
    )
    product_catagory = models.CharField(max_length=100, choices=catagory)
    product_name = models.CharField(max_length=100)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_desc = models.TextField()
    product_image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return self.seller.fname + ' ' + self.product_name

class Wishlist(models.Model):
    user=models.ForeignKey(user,on_delete=models.CASCADE)
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.fname+" - "+self.product.product_name


class Cart(models.Model):
    user=models.ForeignKey(user,on_delete=models.CASCADE)
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    date=models.DateTimeField(default=timezone.now)
    product_price=models.PositiveBigIntegerField()
    product_qty=models.PositiveBigIntegerField()
    total_price=models.PositiveBigIntegerField()
    payment_status=models.BooleanField(default=False)

    def __str__(self):
        return self.user.fname+" - "+self.product.product_name


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='orders')
    stripe_session_id = models.CharField(max_length=500, unique=True, null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=500, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.fname} - {self.order_status}"
    
    class Meta:
        ordering = ['-created_at']
