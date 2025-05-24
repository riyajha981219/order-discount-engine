from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, F

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('home', 'Home & Living'),
    ]
    
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Placed'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    def get_total_price(self):
        # Sum of all order items (price * quantity)
        total = self.items.aggregate(
            total=Sum(F('price_at_purchase') * F('quantity'))
        )['total'] or 0
        return total

    def get_final_price(self):
        total = self.get_total_price()
        discounts = self.discounts.aggregate(
            total_discount=Sum('amount')
        )['total_discount'] or 0
        return total - discounts

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"

    def get_total_price(self):
        return self.price_at_purchase * self.quantity

class Discount(models.Model):
    order = models.ForeignKey(Order, related_name='discounts', on_delete=models.CASCADE)
    discount_type = models.CharField(max_length=50)  # e.g., 'percentage', 'flat', 'category_based'
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.discount_type} - ₹{self.amount} (Order #{self.order.id})"


class DiscountRule(models.Model):
    PERCENTAGE = 'percentage'
    FLAT = 'flat'
    CATEGORY_BASED = 'category_based'

    RULE_TYPE_CHOICES = [
        (PERCENTAGE, 'Percentage Discount'),
        (FLAT, 'Flat Discount'),
        (CATEGORY_BASED, 'Category-Based Discount'),
    ]

    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    threshold = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Minimum order total to qualify (for percentage discount)"
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Discount percentage (e.g., 10 for 10%)"
    )
    flat_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Flat discount amount"
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Category for category-based discount"
    )
    min_quantity = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Minimum quantity required for category-based discount"
    )
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_rule_type_display()} rule"

    class Meta:
        verbose_name = "Discount Rule"
        verbose_name_plural = "Discount Rules"