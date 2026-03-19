from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI(title="Search, Sort & Pagination - Day 6")

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

orders = []
order_counter = 1

# ===== PYDANTIC MODELS =====

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=10)

# ===== HELPER FUNCTIONS =====

def find_product(product_id: int):
    """Find product by ID"""
    for product in products:
        if product["id"] == product_id:
            return product
    return None

# ===== ENDPOINTS =====

@app.get("/")
def root():
    return {
        "message": "Day 6 - Search, Sort & Pagination",
        "endpoints": {
            "search": "/products/search",
            "sort": "/products/sort",
            "paginate": "/products/page",
            "browse": "/products/browse",
            "orders_search": "/orders/search",
            "orders_page": "/orders/page"
        }
    }

# ===== Q1: SEARCH PRODUCTS =====

@app.get("/products/search")
def search_products(keyword: str = Query(..., min_length=1)):
    
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]
    
    if not results:
        return {
            "message": f"No products found for: {keyword}",
            "keyword": keyword,
            "total_found": 0
        }
    
    return {
        "keyword": keyword,
        "total_found": len(results),
        "products": results
    }

# ===== Q2: SORT PRODUCTS =====

@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price", description="Field to sort by: 'price' or 'name'"),
    order: str = Query("asc", description="Order: 'asc' or 'desc'")
):
    
    if sort_by not in ["price", "name"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_by must be 'price' or 'name'"
        )
    
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order must be 'asc' or 'desc'"
        )
    
    reverse = (order == "desc")
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)
    
    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_products),
        "products": sorted_products
    }

# ===== Q3: PAGINATE PRODUCTS =====

@app.get("/products/page")
def paginate_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(2, ge=1, le=20, description="Items per page")
):
    
    total = len(products)
    total_pages = -(-total // limit)  # Ceiling division
    
    start = (page - 1) * limit
    end = start + limit
    
    paged_products = products[start:end]
    
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "products": paged_products
    }

# ===== Q4: SEARCH ORDERS =====

@app.get("/orders/search")
def search_orders(customer_name: str = Query(..., min_length=1)):
    
    results = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]
    
    if not results:
        return {
            "message": f"No orders found for: {customer_name}",
            "customer_name": customer_name,
            "total_found": 0
        }
    
    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }

# ===== Q5: SORT BY CATEGORY THEN PRICE =====

@app.get("/products/sort-by-category")
def sort_by_category():
    
    sorted_products = sorted(products, key=lambda p: (p["category"], p["price"]))
    
    return {
        "message": "Products sorted by category (A-Z), then by price (low to high)",
        "total": len(sorted_products),
        "products": sorted_products
    }

# ===== Q6: BROWSE (SEARCH + SORT + PAGINATE) =====

@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    sort_by: str = Query("price", description="Sort by: 'price' or 'name'"),
    order: str = Query("asc", description="Order: 'asc' or 'desc'"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(4, ge=1, le=20, description="Items per page")
):
    
    result = products
    if keyword:
        result = [
            p for p in result
            if keyword.lower() in p["name"].lower()
        ]
    
    if sort_by in ["price", "name"]:
        reverse = (order == "desc")
        result = sorted(result, key=lambda p: p[sort_by], reverse=reverse)
    
    total = len(result)
    total_pages = -(-total // limit) if total > 0 else 0
    
    start = (page - 1) * limit
    end = start + limit
    paged = result[start:end]
    
    return {
        "filters": {
            "keyword": keyword,
            "sort_by": sort_by,
            "order": order
        },
        "pagination": {
            "page": page,
            "limit": limit,
            "total_found": total,
            "total_pages": total_pages
        },
        "products": paged
    }

# ===== BONUS: PAGINATE ORDERS =====

@app.get("/orders/page")
def paginate_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(3, ge=1, le=20, description="Orders per page")
):
    
    total = len(orders)
    total_pages = -(-total // limit) if total > 0 else 0
    
    start = (page - 1) * limit
    end = start + limit
    
    paged_orders = orders[start:end]
    
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "orders": paged_orders
    }

# ===== GET ALL PRODUCTS & ORDERS =====

@app.get("/products")
def get_all_products():
    """Get all products"""
    return {"products": products, "total": len(products)}

@app.get("/orders")
def get_all_orders():
    """Get all orders"""
    return {"orders": orders, "total": len(orders)}

# ===== POST ORDER =====

@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderRequest):
    """Create a new order"""
    global order_counter
    
    product = find_product(order.product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product["in_stock"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{product['name']} is out of stock"
        )
    
    total_price = product["price"] * order.quantity
    
    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "product_id": order.product_id,
        "product_name": product["name"],
        "quantity": order.quantity,
        "unit_price": product["price"],
        "total_price": total_price,
        "status": "pending"
    }
    
    orders.append(new_order)
    order_counter += 1
    
    return {
        "message": "Order created successfully",
        "order": new_order
    }

# ===== DYNAMIC ROUTES =====

@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Get single product by ID"""
    product = find_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product