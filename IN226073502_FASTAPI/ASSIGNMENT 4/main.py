from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List

app = FastAPI(title="Shopping Cart System - Day 5")

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

cart = []
orders = []
order_counter = 1

# ===== PYDANTIC MODELS =====

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    delivery_address: str = Field(..., min_length=10, max_length=200)

# ===== HELPER FUNCTIONS =====

def find_product(product_id: int):
    """Find product by ID"""
    for product in products:
        if product["id"] == product_id:
            return product
    return None

def calculate_total(product: dict, quantity: int) -> int:
    """Calculate subtotal for a cart item"""
    return product["price"] * quantity

def find_cart_item(product_id: int):
    """Find item in cart by product_id"""
    for item in cart:
        if item["product_id"] == product_id:
            return item
    return None

# ===== ENDPOINTS =====

@app.get("/")
def root():
    return {
        "message": "Shopping Cart System - Day 5",
        "endpoints": {
            "cart": "/cart",
            "add_to_cart": "/cart/add",
            "remove_from_cart": "/cart/{product_id}",
            "checkout": "/cart/checkout",
            "orders": "/orders"
        }
    }

# ===== CART ENDPOINTS =====

@app.get("/cart")
def view_cart():
    """Q2: View cart contents"""
    if not cart:
        return {"message": "Cart is empty"}
    
    grand_total = sum(item["subtotal"] for item in cart)
    
    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }

@app.post("/cart/add")
def add_to_cart(
    product_id: int = Query(..., gt=0),
    quantity: int = Query(1, gt=0, le=10)
):
    """Q1, Q3, Q4: Add item to cart or update quantity"""
    
    # Find product
    product = find_product(product_id)
    
    # Q3: Product not found
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Q3: Check if in stock
    if not product["in_stock"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{product['name']} is out of stock"
        )
    
    # Q4: Check if product already in cart (update quantity)
    existing_item = find_cart_item(product_id)
    
    if existing_item:
        # Update existing item
        existing_item["quantity"] += quantity
        existing_item["subtotal"] = calculate_total(product, existing_item["quantity"])
        
        return {
            "message": "Cart updated",
            "cart_item": existing_item
        }
    
    # Q1: Add new item to cart
    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_total(product, quantity)
    }
    
    cart.append(cart_item)
    
    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    """Q5: Remove item from cart"""
    
    item = find_cart_item(product_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    cart.remove(item)
    
    return {
        "message": f"{item['product_name']} removed from cart",
        "removed_item": item
    }

@app.post("/cart/checkout")
def checkout(request: CheckoutRequest):
    """Q5, Q6, BONUS: Checkout cart and create orders"""
    global order_counter
    
    # BONUS: Check if cart is empty
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty — add items first"
        )
    
    # Calculate grand total
    grand_total = sum(item["subtotal"] for item in cart)
    
    # Create orders (one per cart item)
    orders_placed = []
    
    for item in cart:
        order = {
            "order_id": order_counter,
            "customer_name": request.customer_name,
            "delivery_address": request.delivery_address,
            "product_id": item["product_id"],
            "product": item["product_name"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": item["subtotal"],
            "status": "pending"
        }
        
        orders.append(order)
        orders_placed.append(order)
        order_counter += 1
    
    # Clear cart after checkout
    cart.clear()
    
    return {
        "message": "Checkout successful",
        "orders_placed": orders_placed,
        "grand_total": grand_total
    }

# ===== ORDER ENDPOINTS =====

@app.get("/orders")
def get_all_orders():
    """Q5, Q6: View all orders"""
    if not orders:
        return {"message": "No orders yet"}
    
    return {
        "orders": orders,
        "total_orders": len(orders)
    }

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    """Get single order by ID"""
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Order not found"
    )

# ===== PRODUCTS ENDPOINTS (for reference) =====

@app.get("/products")
def get_all_products():
    """View all products"""
    return {"products": products, "total": len(products)}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Get single product"""
    product = find_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product