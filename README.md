# Order Engine
A Django-based order management system with advanced discount engine supporting percentage, flat, and category-based discounts. Features include stackable discounts, admin-configurable discount rules, and detailed API responses.

## Features

-   User login/signup and authentication
-   Create and manage orders and products
-   Complex discount logic with percentage, flat, and category-based discounts
-   Stackable discounts applied in correct order
-   Admin interface to configure discount rules dynamically
-   Clean and detailed API response including discount breakdown and user info
-   Calculation of total quantity, total price, and final price after discounts

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

## Running the Project

Start the development server:
<pre>python manage.py runserver</pre>
Visit `http://127.0.0.1:8000/` to access the API or admin panel.

## API Endpoints
-   `/api/orders/` - List and create orders
-   `/api/orders/<id>/` - Retrieve, update, or delete an order
-   `/api/products/` - List and create products
-   `/api/discounts/` - List discount rules (admin only)

## Discount Logic
-   **Percentage Discount:** Applies a percentage off if conditions met (e.g. 10% off orders over ₹5000). 
-   **Flat Discount:** A fixed amount off the total price.
-   **Category-based Discount:** Discount applied only when buying minimum quantity from specific categories.
-   Discounts are stackable and applied in the order: category-based → percentage → flat.
-   Admin can create, edit, and delete discount rules through the Django admin panel.

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

# Project Structure & Documentation

-   **models.py** — Database models for Orders, Products, Discounts, etc.
-   **serializers.py** — Django REST Framework serializers defining API input/output formats.
-   **views.py** — API views handling request logic.
-   **discounts.py** — Core discount engine applying stacking rules.
-   **utils.py** — Helper functions used across the project.
    

All functions and classes include detailed docstrings explaining purpose, inputs, and outputs.