from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Lucea API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://lucea-store.vercel.app"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

WILAYAS = ["أدرار","الشلف","الأغواط","أم البواقي","باتنة","بجاية","بسكرة","بشار","البليدة","البويرة","تمنراست","تبسة","تلمسان","تيارت","تيزي وزو","الجزائر","الجلفة","جيجل","سطيف","سعيدة","سكيكدة","سيدي بلعباس","عنابة","قالمة","قسنطينة","المدية","مستغانم","المسيلة","معسكر","ورقلة","وهران","البيض","إليزي","برج بوعريريج","بومرداس","الطارف","تندوف","تيسمسيلت","الوادي","خنشلة","سوق أهراس","تيبازة","ميلة","عين الدفلى","النعامة","عين تموشنت","غرداية","غليزان","تيميمون","برج باجي مختار","أولاد جلال","بني عباس","عين صالح","عين قزام","تقرت","جانت","المغير","المنيعة"]

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    old_price: Optional[float] = None
    image: str = ""
    active: bool = True
    delivery: float = 500

class OrderIn(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    customer_name: str = Field(min_length=3, max_length=100)
    phone: str
    wilaya: str
    commune: str = Field(min_length=2)
    address: str = Field(min_length=5)
    quantity: int = Field(ge=1, le=20)
    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        digits = v.replace(" ", "").replace("-", "")
        if not (digits.startswith("05") or digits.startswith("06") or digits.startswith("07")) or len(digits) != 10:
            raise ValueError("رقم الهاتف الجزائري غير صحيح")
        return digits

products = [Product(id=1, name="مجموعة العناية الوردية", description="منتجات مختارة بعناية لإطلالة يومية ناعمة ومشرقة.", price=2490, old_price=2990, image="/logo.jpg")]
ORDERS_FILE = Path("orders.json")
orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8")) if ORDERS_FILE.exists() else []

@app.get("/api/wilayas")
def wilayas(): return WILAYAS

@app.get("/api/products")
def get_products(): return [p for p in products if p.active]

@app.post("/api/products")
def create_product(product: Product):
    products.append(product); return product

@app.put("/api/products/{product_id}")
def update_product(product_id: int, product: Product):
    for i, current in enumerate(products):
        if current.id == product_id:
            products[i] = product; return product
    raise HTTPException(404, "المنتج غير موجود")

@app.post("/api/orders", status_code=201)
def create_order(order: OrderIn):
    product = next((p for p in products if p.id == order.product_id and p.active), None)
    if not product: raise HTTPException(404, "المنتج غير متوفر")
    if order.wilaya not in WILAYAS: raise HTTPException(422, "الولاية غير صحيحة")
    item = {"id": len(orders)+1, "order_number": f"LC-{datetime.now():%Y%m%d}-{len(orders)+1:03d}", **order.model_dump(), "total_price": order.unit_price * order.quantity, "status":"جديد", "created_at":datetime.now().isoformat()}
    orders.append(item); ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False), encoding="utf-8"); return item

@app.get("/api/orders")
def get_orders():
    return list(reversed(orders))

@app.patch("/api/orders/{order_id}")
def update_order(order_id: int, status: str):
    allowed = ["جديد", "مؤكد", "قيد التحضير", "تم الشحن", "تم التوصيل", "ملغي"]
    if status not in allowed: raise HTTPException(422, "حالة الطلب غير صحيحة")
    for order in orders:
        if order["id"] == order_id:
            order["status"] = status
            order["updated_at"] = datetime.now().isoformat()
            ORDERS_FILE.write_text(json.dumps(orders, ensure_ascii=False), encoding="utf-8")
            return order
    raise HTTPException(404, "الطلب غير موجود")

@app.post("/api/uploads")
async def upload(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg","image/png","image/webp"]: raise HTTPException(400,"صيغة الصورة غير مدعومة")
    folder=Path("uploads"); folder.mkdir(exist_ok=True); target=folder / file.filename
    target.write_bytes(await file.read()); return {"url":f"/uploads/{file.filename}"}

