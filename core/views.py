from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from django.contrib.auth.models import User
from .models import Order
from .serializers import OrderSerializer
from decimal import Decimal
from django.db.models import Sum, F, Q
from core.models import Discount, Order, OrderItem, Product


@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return orders for the logged-in user or admin
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def apply_discounts(self, order):
        # Clear existing discounts (in case of re-calculation)
        order.discounts.all().delete()

        total_order_value = order.items.aggregate(
            total=Sum(F('price_at_purchase') * F('quantity'))
        )['total'] or Decimal('0')

        user = order.user
        discounts = []

        # Discount amounts
        percent_discount = None
        flat_discount = None
        loyalty_user = False

        # 1. Percentage Discount — 10% off if total > ₹5000
        if total_order_value > Decimal('5000'):
            percent_discount = total_order_value * Decimal('0.10')

        # 2. Flat Discount — ₹500 off if user completed 5 eligible purchases
        eligible_orders = Order.objects.filter(
            user=user,
            status__in=['completed', 'shipped']
        ).exclude(id=order.id).count()

        if eligible_orders >= 5:
            flat_discount = Decimal('500')
            loyalty_user = True

        # Decide between flat and percentage
        if flat_discount and percent_discount:
            if loyalty_user:
                # Apply both
                discounts.append(Discount(
                    order=order,
                    discount_type='percentage',
                    description='10% off for orders above ₹5000',
                    amount=percent_discount
                ))
                discounts.append(Discount(
                    order=order,
                    discount_type='flat',
                    description='Loyalty bonus: ₹500 off after 5 completed purchases',
                    amount=flat_discount
                ))
            else:
                # Apply the better one
                if flat_discount > percent_discount:
                    discounts.append(Discount(
                        order=order,
                        discount_type='flat',
                        description='Loyalty bonus: ₹500 off after 5 completed purchases',
                        amount=flat_discount
                    ))
                else:
                    discounts.append(Discount(
                        order=order,
                        discount_type='percentage',
                        description='10% off for orders above ₹5000',
                        amount=percent_discount
                    ))
        elif flat_discount:
            discounts.append(Discount(
                order=order,
                discount_type='flat',
                description='Loyalty bonus: ₹500 off after 5 completed purchases',
                amount=flat_discount
            ))
        elif percent_discount:
            discounts.append(Discount(
                order=order,
                discount_type='percentage',
                description='10% off for orders above ₹5000',
                amount=percent_discount
            ))

        # 3. Category-Based Discount — 5% off Electronics if quantity > 3
        electronics_items = order.items.filter(product__category='electronics')
        electronics_quantity = electronics_items.aggregate(
            total_qty=Sum('quantity')
        )['total_qty'] or 0

        if electronics_quantity > 3:
            electronics_total = electronics_items.aggregate(
                total=Sum(F('price_at_purchase') * F('quantity'))
            )['total'] or Decimal('0')
            electronics_discount = electronics_total * Decimal('0.05')

            discounts.append(Discount(
                order=order,
                discount_type='category_based',
                description='5% off on Electronics (more than 3 items)',
                amount=electronics_discount
            ))

        # Save all calculated discounts
        Discount.objects.bulk_create(discounts)


    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        self.apply_discounts(order)

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"error": "Only admins can update order status."},
                            status=status.HTTP_403_FORBIDDEN)

        order = self.get_object()
        print(order)
        new_status = request.data.get('status')

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()
        return Response({"message": f"Order status for id {order.id} updated to '{new_status}'."})
