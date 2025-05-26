"""
core/serializers.py

Defines
1. Product Serializer
2. User Serializer
3. Discount Serializer
4. Order Item Serializer
5. Order Serializer

for handling API serialization, validation and responses.
"""
from django.core.cache import cache
from rest_framework import serializers
from .models import Product, Order, OrderItem, Discount, User

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category']

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['discount_type', 'description', 'amount']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), write_only=True, source='product'
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    discounts = DiscountSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'user' , 'items', 'total_quantity', 'discounts', 'total_price', 'final_price']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = validated_data.pop('user')
        order = Order.objects.create(user=user, **validated_data)

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price_at_purchase=item['product'].price
            )

        return order
    
    def get_total_price(self, obj):
        cache_key = f"order_{obj.id}_total_price"
        value = cache.get(cache_key)
        if value is None:
            value = f"{obj.get_total_price():.2f}"
            cache.set(cache_key, value, timeout=300)  # Cache for 5 mins
        return value

    def get_final_price(self, obj):
        cache_key = f"order_{obj.id}_final_price"
        value = cache.get(cache_key)
        if value is None:
            value = f"{obj.get_final_price():.2f}"
            cache.set(cache_key, value, timeout=300)
        return value
    
    def get_total_quantity(self, obj):
        cache_key = f"order_{obj.id}_total_quantity"
        value = cache.get(cache_key)
        if value is None:
            value = sum(item.quantity for item in obj.items.all())
            cache.set(cache_key, value, timeout=300)
        return value
