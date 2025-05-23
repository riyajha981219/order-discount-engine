from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from django.contrib.auth.models import User
from .models import Order
from .serializers import OrderSerializer
from decimal import Decimal
from django.db.models import Sum, F, Q
from core.models import Discount, Order, DiscountRule

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

        # Fetch active discount rules
        rules = DiscountRule.objects.filter(active=True)

        # Initialize discount amounts
        percent_discount = None
        flat_discount = None
        category_discounts = []

        # Check loyalty eligibility once
        eligible_orders = Order.objects.filter(
            user=user,
            status__in=['completed', 'shipped']
        ).exclude(id=order.id).count()

        loyalty_user = eligible_orders >= 5

        for rule in rules:
            if rule.rule_type == DiscountRule.PERCENTAGE:
                # Check threshold for percentage discount
                if total_order_value >= (rule.threshold or 0) and rule.percentage:
                    amount = total_order_value * (rule.percentage / 100)
                    percent_discount = {
                        'amount': amount,
                        'description': f"{rule.percentage}% off orders above ₹{rule.threshold}"
                    }

            elif rule.rule_type == DiscountRule.FLAT:
                # Apply flat discount only if user is loyal (based on your existing logic)
                if loyalty_user and rule.flat_amount:
                    flat_discount = {
                        'amount': rule.flat_amount,
                        'description': f"Flat ₹{rule.flat_amount} off for loyalty program"
                    }

            elif rule.rule_type == DiscountRule.CATEGORY_BASED:
                # Calculate category-based discount
                if rule.category and rule.percentage and rule.min_quantity:
                    cat_items = order.items.filter(product__category=rule.category)
                    total_qty = cat_items.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

                    if total_qty >= rule.min_quantity:
                        cat_total = cat_items.aggregate(
                            total=Sum(F('price_at_purchase') * F('quantity'))
                        )['total'] or Decimal('0')
                        amount = cat_total * (rule.percentage / 100)
                        category_discounts.append({
                            'amount': amount,
                            'description': f"{rule.percentage}% off on {rule.category.name} (min {rule.min_quantity} items)"
                        })

        # Stack discounts as per your original logic

        # Apply category discounts first (stackable)
        for cat_discount in category_discounts:
            discounts.append(Discount(
                order=order,
                discount_type='category_based',
                description=cat_discount['description'],
                amount=cat_discount['amount']
            ))

        # Decide between percentage and flat discount
        if flat_discount and percent_discount:
            if loyalty_user:
                # Apply both
                discounts.append(Discount(
                    order=order,
                    discount_type='percentage',
                    description=percent_discount['description'],
                    amount=percent_discount['amount']
                ))
                discounts.append(Discount(
                    order=order,
                    discount_type='flat',
                    description=flat_discount['description'],
                    amount=flat_discount['amount']
                ))
            else:
                # Apply the better discount only
                better = flat_discount if flat_discount['amount'] > percent_discount['amount'] else percent_discount
                discount_type = 'flat' if better == flat_discount else 'percentage'
                discounts.append(Discount(
                    order=order,
                    discount_type=discount_type,
                    description=better['description'],
                    amount=better['amount']
                ))
        elif flat_discount:
            discounts.append(Discount(
                order=order,
                discount_type='flat',
                description=flat_discount['description'],
                amount=flat_discount['amount']
            ))
        elif percent_discount:
            discounts.append(Discount(
                order=order,
                discount_type='percentage',
                description=percent_discount['description'],
                amount=percent_discount['amount']
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
