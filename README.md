# Order Engine

## Project Overview
Order Engine is a Django-based backend system designed to manage product orders, apply complex discount rules, and provide clear API responses for order management. The system supports multiple discount types (percentage, flat, category-based), stackable discount logic, and caching for performance optimization. It also integrates user information and detailed order breakdowns for admin clarity.

## Getting Started
### Prerequisites

-   Python 3.8+
-   Django 5.x
-   PostgreSQL or preferred database
-   pip

### Installation
Run these commands to set up the project:
<pre>

    git clone https://github.com/riyajha981219/order-discount-engine.git  
    cd order_engine  
    python3 -m venv venv  
    source venv/bin/activate    # Linux/macOS  
    venv\Scripts\activate       # Windows  
    pip install -r requirements.txt

</pre>

### Database Setup

Configure your database settings in `settings.py` (default is SQLite for development). Then apply migrations:
<pre>python manage.py migrate</pre>
Create a superuser for admin access:
<pre>python manage.py createsuperuser</pre>

## Workflow
1. Users sign up or log in to place orders.
2. Each order contains multiple items referencing products.
3. The system applies discounts based on predefined rules:
    -   Percentage discounts
    -   Flat amount discounts
    -   Category-based discounts
4. Discounts are stackable and applied in the configured order.
5. The API response returns:
    -   Detailed user info
    -   Ordered items with product info and quantities
    -   Discount breakdown with descriptions and amounts
    -   Total price before discounts, total discounts, and final price after discounts
6. Caching optimizes repeated calculations for performance.

## Discount Logic
-   **Percentage Discount:** Applies a percentage off if conditions met (e.g. 10% off orders over ₹5000). 
-   **Flat Discount:** A fixed amount off the total price.
-   **Category-based Discount:** Discount applied only when buying minimum quantity from specific categories.
-   Discounts are stackable and applied in the order: category-based → percentage → flat.
-   Admin can create, edit, and delete discount rules through the Django admin panel.

# Project Structure & Documentation

-   **models.py** — Database models for Category, Orders, OrderItems, Discounts, DiscountsRules, Products
-   **serializers.py** — Django REST Framework serializers defining API input/output formats.
-   **views.py** — API views handling request logic.
-   **discounts.py** — Core discount engine applying stacking rules.
-   **utils.py** — Helper functions used across the project.

## Model Description
## Category
Represents product categories such as Electronics, Fashion, and Home & Living.
-  Fields:
    -  name: Name of the category (e.g., "electronics").
-  Usage: Used to classify products into categories for filtering and category-based discounts.

## Product
Defines individual products available for purchase.
-   Fields:
    -   name: Product name (e.g., "Smartphone").
    -   price: Price of the product as decimal.
    -   category: Product category, chosen from predefined options.
-   Usage: Products are added to orders via OrderItems and used in discount calculations.

## Order
Represents a user’s order containing multiple items and discounts.
-   Fields:
    -   user: ForeignKey to the User who placed the order.
    -   created_at: Timestamp when order was created.
    -   status: Current status (placed, shipped, completed, etc.).

-   Key methods:
    -   get_total_price(): Calculates total before discounts by summing each item’s price times quantity.
    -   get_final_price(): Returns total after subtracting sum of all discounts applied to this order.
-   Usage: Central model managing user orders and discount applications.

## OrderItem
Links individual products to orders with purchase quantity and price.
-   Fields:
    -   order: ForeignKey to the Order it belongs to.
    -   product: ForeignKey to the Product being ordered.
    -   quantity: Number of units purchased.
    -   price_at_purchase: Price of the product at time of order (to keep history).
-   Key methods:
    -   get_total_price(): Returns the total price for this item (price times quantity).
-   Usage: Represents the details of products in an order.

## Discount
Tracks discounts applied to each order.
-   Fields:
    -   order: ForeignKey to the related Order.
    -   discount_type: Type of discount ("percentage", "flat", or "category_based").
    -   description: Human-readable explanation of the discount.
    -   amount: Amount deducted by this discount from the order total.
-   Usage: Keeps a record of each discount applied per order for transparency and API responses.

## DiscountRule
Defines configurable discount rules which admins can enable or disable.
-   Fields:
    -   rule_type: Type of discount rule (percentage, flat, category-based).
    -   threshold: Minimum order total for percentage discounts.
    -   percentage: Discount percentage for percentage-based rules.
    -   flat_amount: Fixed discount amount for flat discounts.
    -   category: Reference category for category-based discounts.
    -   min_quantity: Minimum quantity in category for category-based discounts.
    -   active: Whether this rule is currently active.
    -   Timestamps: created_at, updated_at.
-   Usage: Stores business logic for discounts that get applied automatically when conditions are met.

## Serializers Description

## Product Serializer
Serializes Product model data.
-   Fields: id, name, price, category.
-   Usage: Used to represent product details in API responses and validate product input data.

## DiscountSerializer
Serializes Discount model data.
-   Fields: discount_type, description, amount.
-   Usage: Returns information about discounts applied to orders in API responses.

## UserSerializer
Serializes Django's built-in User model data.
-   Fields: id, username.
-   Usage: Used to include basic user information in order responses.

## OrderItemSerializer
Handles serialization of OrderItem objects.
-   Nested Fields:
    -   product: Read-only nested ProductSerializer.
    -   product_id: Write-only field to accept product reference on input.
-   Fields: id, product, product_id, quantity, price_at_purchase.
-   Usage: Used to serialize items within an order and accept item creation data.


## Views and Core Business Logic

### <pre> signup(request) </pre>
Type: <pre>@api_view(['POST'])</pre>
Purpose: Allows users to sign up by providing a unique username and password.
Returns:
-   201 Created on success
-   400 Bad Request if the username is missing, password is missing, or already exists

### OrderViewSet(viewsets.ModelViewSet)
Handles all operations related to orders — listing, creating, and updating — with authentication enforced.

### <pre> get_queryset(self) </pre>
Purpose:
-   Returns orders belonging to the currently authenticated user.
-   Admin users can view all orders.

### <pre> perform_create(self, serializer) </pre>
Purpose:
-   Saves a new order using the serializer.
-   Associates it with the currently authenticated user.
-   Automatically applies any eligible discounts using apply_discounts() after the order is saved.

### <pre> apply_discounts </pre>
Purpose:
-   Applies applicable discounts to a newly created order using business rules defined in DiscountRule.
-   Discount Rules Implemented:
    -   Loyalty Discount (Flat ₹500): For users with ≥5 completed/shipped orders.
    -   Percentage Discount: 10% off if total order value ≥ ₹5000.
    -   Category-Based Discount: 5% off for ≥3 items in
- Persistence: Discounts are bulk-saved to the DB.

### <pre> update_status(self, request, pk=None) </pre>
Route: <pre> PATCH /orders/<id>/update-status/ </pre>
Purpose: 
-   Allows only admins to update the status of any order.
Validations:
-   Must be an admin (is_staff).
-   status must be a valid choice from Order.STATUS_CHOICES.
Response:
-   Success: Status update message
-   Failure: 403 for unauthorized access, 400 for invalid status


# Running the Project

Start the development server:
<pre>python manage.py runserver</pre>
Visit `http://127.0.0.1:8000/` to access the API or admin panel.

## API Endpoints
-   `/api/orders/` - List and create orders
-   `/api/orders/<id>/` - Retrieve, update, or delete an order
-   `/api/products/` - List and create products
-   `/api/discounts/` - List discount rules (admin only)

## API Response Example
<pre>
{
  "id": 1,
  "created_at": "2025-05-23T12:02:32.911365Z",
  "status": "completed",
  "user": {
    "id": 1,
    "username": "riyajha98"
  },
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Smartphone",
        "price": "15000.00",
        "category": "electronics"
      },
      "quantity": 2,
      "price_at_purchase": "15000.00"
    }
  ],
  "total_quantity": 2,
  "discounts": [
    {
      "discount_type": "percentage",
      "description": "10% off orders above ₹5000",
      "amount": "3000.00"
    }
  ],
  "total_price": "30000.00",
  "final_price": "27000.00"
}
</pre>

All functions and classes include detailed docstrings explaining purpose, inputs, and outputs.