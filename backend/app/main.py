import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, DateTime, Numeric, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

DATABASE_URL=os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"): DATABASE_URL=DATABASE_URL.replace("postgres://","postgresql+psycopg://",1)
engine=create_engine(DATABASE_URL or "sqlite:///./lucea.db", pool_pre_ping=True)
class Base(DeclarativeBase): pass
class ProductDB(Base):
    __tablename__="products"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(180)); description:Mapped[str]=mapped_column(Text)
    price:Mapped[Decimal]=mapped_column(Numeric(12,2)); old_price:Mapped[Optional[Decimal]]=mapped_column(Numeric(12,2),nullable=True)
    delivery:Mapped[Decimal]=mapped_column(Numeric(12,2),default=500); image:Mapped[str]=mapped_column(String(500),default="/logo.jpg"); active:Mapped[bool]=mapped_column(Boolean,default=True)
class OrderDB(Base):
    __tablename__="orders"
    id:Mapped[int]=mapped_column(primary_key=True); order_number:Mapped[str]=mapped_column(String(40),unique=True)
    product_id:Mapped[int]; product_name:Mapped[str]=mapped_column(String(180)); unit_price:Mapped[Decimal]=mapped_column(Numeric(12,2)); customer_name:Mapped[str]=mapped_column(String(100)); phone:Mapped[str]=mapped_column(String(20)); wilaya:Mapped[str]=mapped_column(String(80)); commune:Mapped[str]=mapped_column(String(100)); address:Mapped[str]=mapped_column(Text); quantity:Mapped[int]; total_price:Mapped[Decimal]=mapped_column(Numeric(12,2)); status:Mapped[str]=mapped_column(String(30),default="جديد"); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
Base.metadata.create_all(engine)

app=FastAPI(title="Lucea API")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000","https://lucea-store-bice.vercel.app","https://lucea-store-qbuunapyt-rayane6.vercel.app"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
WILAYAS=["أدرار","الشلف","الأغواط","أم البواقي","باتنة","بجاية","بسكرة","بشار","البليدة","البويرة","تمنراست","تبسة","تلمسان","تيارت","تيزي وزو","الجزائر","الجلفة","جيجل","سطيف","سعيدة","سكيكدة","سيدي بلعباس","عنابة","قالمة","قسنطينة","المدية","مستغانم","المسيلة","معسكر","ورقلة","وهران","البيض","إليزي","برج بوعريريج","بومرداس","الطارف","تندوف","تيسمسيلت","الوادي","خنشلة","سوق أهراس","تيبازة","ميلة","عين الدفلى","النعامة","عين تموشنت","غرداية","غليزان","تيميمون","برج باجي مختار","أولاد جلال","بني عباس","عين صالح","عين قزام","تقرت","جانت","المغير","المنيعة"]
class ProductIn(BaseModel): id:int; name:str; description:str; price:float; old_price:Optional[float]=None; delivery:float=500; image:str="/logo.jpg"; active:bool=True
class OrderIn(BaseModel):
 product_id:int; product_name:str; unit_price:float; customer_name:str=Field(min_length=3); phone:str; wilaya:str; commune:str=Field(min_length=2); address:str=Field(min_length=5); quantity:int=Field(ge=1,le=20)
 @field_validator("phone")
 @classmethod
 def phone_ok(cls,v):
  d=v.replace(" ","").replace("-","")
  if len(d)!=10 or d[:2] not in ["05","06","07"]: raise ValueError("رقم الهاتف غير صحيح")
  return d
def product_out(p): return {"id":p.id,"name":p.name,"description":p.description,"price":float(p.price),"old_price":float(p.old_price) if p.old_price is not None else None,"delivery":float(p.delivery),"image":p.image,"active":p.active}
def order_out(o): return {"id":o.id,"order_number":o.order_number,"product_id":o.product_id,"product_name":o.product_name,"unit_price":float(o.unit_price),"customer_name":o.customer_name,"phone":o.phone,"wilaya":o.wilaya,"commune":o.commune,"address":o.address,"quantity":o.quantity,"total_price":float(o.total_price),"status":o.status,"created_at":o.created_at.isoformat()}
@app.get("/api/wilayas")
def wilayas(): return WILAYAS
@app.get("/api/products")
def products():
 with Session(engine) as s: return [product_out(p) for p in s.scalars(select(ProductDB).where(ProductDB.active==True)).all()]
@app.post("/api/products")
def create_product(p:ProductIn):
 with Session(engine) as s:
  db=ProductDB(**p.model_dump());s.add(db);s.commit();s.refresh(db);return product_out(db)
@app.put("/api/products/{pid}")
def update_product(pid:int,p:ProductIn):
 with Session(engine) as s:
  db=s.get(ProductDB,pid)
  if not db: raise HTTPException(404,"المنتج غير موجود")
  for k,v in p.model_dump().items(): setattr(db,k,v)
  s.commit();s.refresh(db);return product_out(db)
@app.post("/api/orders",status_code=201)
def create_order(o:OrderIn):
 with Session(engine) as s:
  p=s.get(ProductDB,o.product_id)
  if not p or not p.active: raise HTTPException(404,"المنتج غير متوفر")
  if o.wilaya not in WILAYAS: raise HTTPException(422,"الولاية غير صحيحة")
  db=OrderDB(order_number=f"LC-{datetime.now():%Y%m%d}-{(s.query(OrderDB).count()+1):03d}",**o.model_dump(),total_price=Decimal(str(o.unit_price))*o.quantity)
  s.add(db);s.commit();s.refresh(db);return order_out(db)
@app.get("/api/orders")
def get_orders():
 with Session(engine) as s:return [order_out(o) for o in s.scalars(select(OrderDB).order_by(OrderDB.created_at.desc())).all()]
@app.patch("/api/orders/{oid}")
def update_order(oid:int,status:str):
 if status not in ["جديد","مؤكد","قيد التحضير","تم الشحن","تم التوصيل","ملغي"]: raise HTTPException(422,"حالة غير صحيحة")
 with Session(engine) as s:
  o=s.get(OrderDB,oid)
  if not o: raise HTTPException(404,"الطلب غير موجود")
  o.status=status;s.commit();return order_out(o)
@app.post("/api/uploads")
async def upload(file:UploadFile=File(...)):
 if file.content_type not in ["image/jpeg","image/png","image/webp"]: raise HTTPException(400,"صيغة الصورة غير مدعومة")
 folder=Path("uploads");folder.mkdir(exist_ok=True);target=folder/file.filename;target.write_bytes(await file.read());return {"url":f"/uploads/{file.filename}"}
