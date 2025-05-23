from rest_framework import serializers
from .models import Product, Order, OrderItem, Discount

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category']

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['discount_type', 'description', 'amount']
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
    total_price = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'items', 'discounts', 'total_price', 'final_price']
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
        return obj.get_total_price()

    def get_final_price(self, obj):
        return obj.get_final_price()
