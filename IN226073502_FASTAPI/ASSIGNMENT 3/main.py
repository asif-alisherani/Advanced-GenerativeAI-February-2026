from fastapi import FastAPI, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

#**************************
#******ASSIGNMENT - 1******
#**************************


products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "USB Cable", "price": 799, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "Notebook", "price": 89, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": False},
    # Q1: Added 3 new products
    # {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    # {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    # {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
]

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI E-commerce Store!"}

# Get all products
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

# Get product by ID
# @app.get("/products/{product_id}")
# def get_product(product_id: int):
#     for product in products:
#         if product["id"] == product_id:
#             return product
#     return {"error": "Product not found"}

# Q2: Filter products by category
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": result, "total": len(result)}

# Q3: Get only in-stock products
@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"] == True]
    return {"in_stock_products": available, "count": len(available)}

# Q4: Store Summary
@app.get('/store/summary')
def store_summary():
    in_stock = len([p for p in products if p["in_stock"]])
    out_stock = len([p for p in products if p["in_stock"]==False])
    categories = list(set([p["category"] for p in products]))
    return{
        "store_name":"My E-commerce Store",
        "total_products":len(products),
        "in_stock":in_stock,
        "out_of_stock":out_stock,
        "categories": categories,
    }

# Q5: Search products by keyword (case-insensitive)
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]
    if not results:
        return {"message": "No products matched your search"}
    return {"keyword": keyword, "results": results, "total_matches": len(results)}

# BONUS: Get cheapest and most expensive products
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {
        "best_deal": cheapest,
        "premium_pick": expensive,
    }

#**************************
#******ASSIGNMENT - 2******
#**************************

feedback = []
orders = []
order_counter = 1

# Q1: Filter Products with min_pric
@app.get("/products/filter")
def filter_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_price: Optional[int] = Query(None, description="Minimum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock status")
):
    result = products.copy()
    
    if category:
        result = [p for p in result if p["category"] == category]
    
    if max_price:
        result = [p for p in result if p["price"] <= max_price]
    
    if min_price:
        result = [p for p in result if p["price"] >= min_price]
    
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]
    
    return {
        "filters_applied": {
            "category": category,
            "max_price": max_price,
            "min_price": min_price,
            "in_stock": in_stock
        },
        "products": result,
        "total": len(result)
    }

# Q2: Get Only Price of a Product
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }
    return {"error": "Product not found"}

# Q3: Accept Customer Feedback

# CustomerFeedback Model
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    product_id: int = Field(..., gt=0, description="Product ID must be positive")
    rating: int = Field(..., ge=1, le=5, description="Rating between 1-5")
    comment: Optional[str] = Field(None, max_length=300, description="Optional comment")

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.model_dump())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data.model_dump(),
        "total_feedback": len(feedback)
    }

# Q4. Product Summary Dashboard
@app.get("/products/summary")
def product_summary():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]
    
    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    
    categories = list(set(p["category"] for p in products))
    
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }


# Q5: Bulk Order Models
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    
    for item in order.items:
        # Find product
        product = next((p for p in products if p["id"] == item.product_id), None)
        
        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })
    
    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# Bonus: Order Request Model (from Day 2 class)
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=10)

@app.post("/orders")
def place_order(order: OrderRequest):
    global order_counter
    
    # Find product
    product = next((p for p in products if p["id"] == order.product_id), None)
    
    if not product:
        return {"error": "Product not found"}
    
    if not product["in_stock"]:
        return {"error": f"{product['name']} is out of stock"}
    
    total = product["price"] * order.quantity
    
    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "product": product["name"],
        "quantity": order.quantity,
        "total": total,
        "status": "pending"  # Changed from "confirmed"
    }
    
    orders.append(new_order)
    order_counter += 1
    
    return {
        "message": "Order placed successfully",
        "order": new_order
    }

# BONUS: PATCH to confirm order
@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }
    return {"error": "Order not found"}

# # Get all orders 
# @app.get("/orders")
# def get_all_orders():
#     return {"orders": orders, "total": len(orders)}

# # Get all feedback
# @app.get("/feedback")
# def get_all_feedback():
#     return {"feedback": feedback, "total": len(feedback)}

#**************************
#******ASSIGNMENT - 3******
#**************************

# BONUS: Apply a Category-Wide Discount
@app.put("/products/discount")
def bulk_discount(
    category: str = Query(..., description="Category to discount"),
    discount_percent: int = Query(..., ge=1, le=99, description="Discount percentage (1-99)")
):
    updated = []
    
    for p in products:
        if p["category"] == category:
            old_price = p["price"]
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append({
                "name": p["name"],
                "old_price": old_price,
                "new_price": p["price"]
            })
    
    if not updated:
        return {"message": f"No products found in category: {category}"}
    
    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated),
        "updated_products": updated
    }

# Q1. Add new product
class NewProduct(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    in_stock: bool = Field(True)

@app.post("/products", status_code=status.HTTP_201_CREATED)
def add_product(product: NewProduct, response: Response):
    for p in products:
        if p["name"].lower() == product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": f"Product '{product.name}' already exists"}
    
    # Generate new ID
    if products:
        next_id = max(p["id"] for p in products) + 1
    else:
        next_id = 1
    
    # Create new product
    new_product = {
        "id": next_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }
    
    products.append(new_product)
    
    return {
        "message": "Product added",
        "product": new_product
    }

# Q2. Update Product
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    response: Response,
    name: Optional[str] = Query(None, min_length=1),
    price: Optional[int] = Query(None, gt=0),
    category: Optional[str] = Query(None, min_length=1),
    in_stock: Optional[bool] = Query(None)
):
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    
    if name is not None:
        product["name"] = name
    if price is not None:
        product["price"] = price
    if category is not None:
        product["category"] = category
    if in_stock is not None: 
        product["in_stock"] = in_stock
    
    return {
        "message": "Product updated",
        "product": product
    }

# Q3: Delete a Product and Handle Missing IDs
@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": "Product not found"}
    
    product_name = product["name"]
    products.remove(product)
    
    return {"message": f"Product '{product_name}' deleted"}

# # Q4. Full CRUD Sequence — One Complete Workflow
# 1️⃣
# POST /products — add Smart Watch: price 3999, category Electronics, in_stock false

# 2️⃣
# GET /products — note the auto-generated ID given to Smart Watch (it will be 5 or 6 depending on Q1)

# 3️⃣
# PUT /products/{id}?price=3499 — pricing error, correct it to 3499

# 4️⃣
# GET /products/{id} — confirm price is now 3499

# 5️⃣
# DELETE /products/{id} — launch cancelled, remove it

# 6️⃣
# GET /products — Smart Watch must be completely gone, total back to what it was before step 1



# Q5. Build GET /products/audit — Inventory Summary  
@app.get("/products/audit")
def product_audit():
    """Q5: Get inventory summary"""
    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]
    stock_value = sum(p["price"] * 10 for p in in_stock_list)
    
    if products:
        priciest = max(products, key=lambda p: p["price"])
        most_expensive = {"name": priciest["name"], "price": priciest["price"]}
    else:
        most_expensive = None
    
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p["name"] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": most_expensive
    }



#**************************
#******ASSIGNMENT - 4******
#**************************