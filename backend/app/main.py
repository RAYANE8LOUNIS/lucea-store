import os, json, re
import hashlib, hmac, secrets, jwt, io
import cloudinary
import cloudinary.uploader
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, DateTime, Numeric, String, Text, create_engine, select, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

DATABASE_URL=os.getenv("DATABASE_URL")
if DATABASE_URL:
 if DATABASE_URL.startswith("postgres://"): DATABASE_URL=DATABASE_URL.replace("postgres://","postgresql+psycopg://",1)
 elif DATABASE_URL.startswith("postgresql://"): DATABASE_URL=DATABASE_URL.replace("postgresql://","postgresql+psycopg://",1)
engine=create_engine(DATABASE_URL or "sqlite:///./lucea.db", pool_pre_ping=True)
cloudinary.config(cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),api_key=os.getenv("CLOUDINARY_API_KEY"),api_secret=os.getenv("CLOUDINARY_API_SECRET"),secure=True)
class Base(DeclarativeBase): pass
class ProductDB(Base):
    __tablename__="products"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(180)); description:Mapped[str]=mapped_column(Text)
    price:Mapped[Decimal]=mapped_column(Numeric(12,2)); old_price:Mapped[Optional[Decimal]]=mapped_column(Numeric(12,2),nullable=True)
    delivery:Mapped[Decimal]=mapped_column(Numeric(12,2),default=500); delivery_desk:Mapped[Optional[Decimal]]=mapped_column(Numeric(12,2),nullable=True); delivery_home:Mapped[Optional[Decimal]]=mapped_column(Numeric(12,2),nullable=True); image:Mapped[str]=mapped_column(String(500),default="/logo.jpg"); active:Mapped[bool]=mapped_column(Boolean,default=True)
    images_json:Mapped[str]=mapped_column(Text,default="[]"); colors_json:Mapped[str]=mapped_column(Text,default="[]"); sizes_json:Mapped[str]=mapped_column(Text,default="[]")
class OrderDB(Base):
    __tablename__="orders"
    id:Mapped[int]=mapped_column(primary_key=True); order_number:Mapped[str]=mapped_column(String(40),unique=True)
    product_id:Mapped[int]; product_name:Mapped[str]=mapped_column(String(180)); unit_price:Mapped[Decimal]=mapped_column(Numeric(12,2)); customer_name:Mapped[str]=mapped_column(String(100)); phone:Mapped[str]=mapped_column(String(20)); wilaya:Mapped[str]=mapped_column(String(80)); commune:Mapped[str]=mapped_column(String(100)); address:Mapped[str]=mapped_column(Text); quantity:Mapped[int]; total_price:Mapped[Decimal]=mapped_column(Numeric(12,2)); delivery_method:Mapped[Optional[str]]=mapped_column(String(20),nullable=True); delivery_price:Mapped[Optional[Decimal]]=mapped_column(Numeric(12,2),nullable=True); selected_color:Mapped[Optional[str]]=mapped_column(String(80),nullable=True); selected_size:Mapped[Optional[str]]=mapped_column(String(80),nullable=True); status:Mapped[str]=mapped_column(String(30),default="جديد"); archived_at:Mapped[Optional[datetime]]=mapped_column(DateTime,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
Base.metadata.create_all(engine)
def ensure_columns():
 additions={"products":{"images_json":"TEXT DEFAULT '[]' NOT NULL","colors_json":"TEXT DEFAULT '[]' NOT NULL","sizes_json":"TEXT DEFAULT '[]' NOT NULL","delivery_desk":"NUMERIC(12,2)","delivery_home":"NUMERIC(12,2)"},"orders":{"selected_color":"VARCHAR(80)","selected_size":"VARCHAR(80)","delivery_method":"VARCHAR(20)","delivery_price":"NUMERIC(12,2)","archived_at":"TIMESTAMP"}}
 with engine.begin() as connection:
  for table_name,columns in additions.items():
   existing={c["name"] for c in inspect(engine).get_columns(table_name)}
   for column_name,definition in columns.items():
    if column_name not in existing: connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"))
  connection.execute(text("UPDATE products SET delivery_desk = delivery WHERE delivery_desk IS NULL"))
  connection.execute(text("UPDATE products SET delivery_home = delivery WHERE delivery_home IS NULL"))
ensure_columns()

app=FastAPI(title="Lucea API")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000","https://lucea-store-bice.vercel.app","https://lucea-store-qbuunapyt-rayane6.vercel.app"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
WILAYAS=["أدرار","الشلف","الأغواط","أم البواقي","باتنة","بجاية","بسكرة","بشار","البليدة","البويرة","تمنراست","تبسة","تلمسان","تيارت","تيزي وزو","الجزائر","الجلفة","جيجل","سطيف","سعيدة","سكيكدة","سيدي بلعباس","عنابة","قالمة","قسنطينة","المدية","مستغانم","المسيلة","معسكر","ورقلة","وهران","البيض","إليزي","برج بوعريريج","بومرداس","الطارف","تندوف","تيسمسيلت","الوادي","خنشلة","سوق أهراس","تيبازة","ميلة","عين الدفلى","النعامة","عين تموشنت","غرداية","غليزان","تيميمون","برج باجي مختار","أولاد جلال","بني عباس","عين صالح","عين قزام","تقرت","جانت","المغير","المنيعة"]
class ProductIn(BaseModel): id:Optional[int]=None; name:str; description:str; price:float=Field(ge=0); old_price:Optional[float]=Field(default=None,ge=0); delivery:float=Field(default=500,ge=0); delivery_desk:Optional[float]=Field(default=None,ge=0); delivery_home:Optional[float]=Field(default=None,ge=0); image:str="/logo.jpg"; images:list[str]=Field(default_factory=list); colors:list[str]=Field(default_factory=list); sizes:list[str]=Field(default_factory=list); active:bool=True
class OrderIn(BaseModel):
 product_id:int; product_name:Optional[str]=None; unit_price:Optional[float]=None; customer_name:str=Field(min_length=3); phone:str; wilaya:str; commune:str=Field(min_length=2); address:str=""; quantity:int=Field(ge=1,le=20); delivery_method:str="home"; selected_color:Optional[str]=None; selected_size:Optional[str]=None
 @field_validator("phone")
 @classmethod
 def phone_ok(cls,v):
  d=v.replace(" ","").replace("-","")
  if len(d)!=10 or d[:2] not in ["05","06","07"]: raise ValueError("رقم الهاتف غير صحيح")
  return d
class LoginIn(BaseModel): email:str; password:str
SECRET_KEY=os.getenv("SECRET_KEY")
ADMIN_EMAIL=os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD")
if not SECRET_KEY or not ADMIN_EMAIL or not ADMIN_PASSWORD: raise RuntimeError("SECRET_KEY, ADMIN_EMAIL and ADMIN_PASSWORD must be configured")
def password_hash(value): return hashlib.pbkdf2_hmac("sha256",value.encode(),SECRET_KEY.encode(),180000).hex()
ADMIN_PASSWORD_HASH=os.getenv("ADMIN_PASSWORD_HASH",password_hash(ADMIN_PASSWORD))
def require_admin(request:Request):
 token=request.cookies.get("lucea_session")
 if not token: raise HTTPException(401,"تسجيل الدخول مطلوب")
 try: jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
 except jwt.PyJWTError: raise HTTPException(401,"جلسة الدخول غير صالحة")
 return True
def json_list(value):
 try: return json.loads(value or "[]")
 except (TypeError,json.JSONDecodeError): return []
def normalize_sizes(values):
 result=[]
 for value in values:
  result.extend(part.strip().upper() for part in re.split(r"[،,./\s]+",value) if part.strip())
 return list(dict.fromkeys(result))
def normalize_colors(values):
 result=[]
 for value in values:
  result.extend(part.strip() for part in re.split(r"[،,./;\n]+",value) if part.strip())
 return list(dict.fromkeys(result))
def product_out(p):
 images=json_list(p.images_json) or ([p.image] if p.image else [])
 desk=p.delivery_desk if p.delivery_desk is not None else p.delivery
 home=p.delivery_home if p.delivery_home is not None else p.delivery
 return {"id":p.id,"name":p.name,"description":p.description,"price":float(p.price),"old_price":float(p.old_price) if p.old_price is not None else None,"delivery":float(home),"delivery_desk":float(desk),"delivery_home":float(home),"image":images[0] if images else p.image,"images":images,"colors":normalize_colors(json_list(p.colors_json)),"sizes":normalize_sizes(json_list(p.sizes_json)),"active":p.active}
def order_out(o): return {"id":o.id,"order_number":o.order_number,"product_id":o.product_id,"product_name":o.product_name,"unit_price":float(o.unit_price),"customer_name":o.customer_name,"phone":o.phone,"wilaya":o.wilaya,"commune":o.commune,"address":o.address,"quantity":o.quantity,"delivery_method":o.delivery_method or "home","delivery_price":float(o.delivery_price or 0),"total_price":float(o.total_price),"selected_color":o.selected_color,"selected_size":o.selected_size,"status":o.status,"archived_at":o.archived_at.isoformat() if o.archived_at else None,"created_at":o.created_at.isoformat(),"updated_at":o.updated_at.isoformat() if o.updated_at else None}
def product_data(p):
 data=p.model_dump(exclude={"id","images","colors","sizes"});images=[x for x in p.images if x]
 data["delivery_desk"]=p.delivery_desk if p.delivery_desk is not None else p.delivery
 data["delivery_home"]=p.delivery_home if p.delivery_home is not None else p.delivery
 data["delivery"]=data["delivery_home"]
 data["image"]=images[0] if images else p.image;data["images_json"]=json.dumps(images,ensure_ascii=False);data["colors_json"]=json.dumps(normalize_colors(p.colors),ensure_ascii=False);data["sizes_json"]=json.dumps(normalize_sizes(p.sizes),ensure_ascii=False)
 return data
@app.get("/api/wilayas")
def wilayas(): return WILAYAS
@app.post("/api/auth/login")
def login(data:LoginIn,response:Response):
 if not hmac.compare_digest(data.email,ADMIN_EMAIL) or not hmac.compare_digest(password_hash(data.password),ADMIN_PASSWORD_HASH): raise HTTPException(401,"بيانات الدخول غير صحيحة")
 token=jwt.encode({"sub":ADMIN_EMAIL,"exp":datetime.utcnow().timestamp()+60*60*24*7},SECRET_KEY,algorithm="HS256")
 production=os.getenv("ENVIRONMENT","development")=="production"
 response.set_cookie("lucea_session",token,httponly=True,secure=production,samesite="none" if production else "lax",max_age=60*60*24*7)
 return {"ok":True}
@app.post("/api/auth/logout")
def logout(response:Response): response.delete_cookie("lucea_session"); return {"ok":True}
@app.get("/api/auth/me")
def current_admin(_=Depends(require_admin)): return {"ok":True,"email":ADMIN_EMAIL}
@app.get("/api/products")
def products():
 with Session(engine) as s: return [product_out(p) for p in s.scalars(select(ProductDB).where(ProductDB.active==True)).all()]
@app.post("/api/products")
def create_product(p:ProductIn,_=Depends(require_admin)):
 with Session(engine) as s:
  data=product_data(p)
  db=ProductDB(**data);s.add(db);s.commit();s.refresh(db);return product_out(db)
@app.put("/api/products/{pid}")
def update_product(pid:int,p:ProductIn,_=Depends(require_admin)):
 with Session(engine) as s:
  db=s.get(ProductDB,pid)
  if not db: raise HTTPException(404,"المنتج غير موجود")
  for k,v in product_data(p).items(): setattr(db,k,v)
  s.commit();s.refresh(db);return product_out(db)
@app.delete("/api/products/{pid}")
def delete_product(pid:int,_=Depends(require_admin)):
 with Session(engine) as s:
  db=s.get(ProductDB,pid)
  if not db: raise HTTPException(404,"المنتج غير موجود")
  s.delete(db);s.commit();return {"ok":True}
@app.post("/api/orders",status_code=201)
def create_order(o:OrderIn):
 with Session(engine) as s:
  p=s.get(ProductDB,o.product_id)
  if not p or not p.active: raise HTTPException(404,"المنتج غير متوفر")
  if o.wilaya not in WILAYAS: raise HTTPException(422,"الولاية غير صحيحة")
  colors=normalize_colors(json_list(p.colors_json));sizes=normalize_sizes(json_list(p.sizes_json))
  if colors and o.selected_color not in colors: raise HTTPException(422,"يرجى اختيار اللون")
  if sizes and o.selected_size not in sizes: raise HTTPException(422,"يرجى اختيار المقاس")
  if o.delivery_method not in ["desk","home"]: raise HTTPException(422,"يرجى اختيار طريقة التوصيل")
  if o.delivery_method=="home" and len(o.address.strip())<5: raise HTTPException(422,"يرجى إدخال عنوان التوصيل الكامل")
  delivery_price=p.delivery_desk if o.delivery_method=="desk" else p.delivery_home
  if delivery_price is None: delivery_price=p.delivery
  unit_price=Decimal(str(p.price));delivery_price=Decimal(str(delivery_price or 0))
  db=OrderDB(order_number=f"LC-{datetime.now():%Y%m%d}-{(s.query(OrderDB).count()+1):03d}",product_id=p.id,product_name=p.name,unit_price=unit_price,customer_name=o.customer_name,phone=o.phone,wilaya=o.wilaya,commune=o.commune,address=o.address.strip() or "الاستلام من مكتب التوصيل",quantity=o.quantity,delivery_method=o.delivery_method,delivery_price=delivery_price,total_price=unit_price*o.quantity+delivery_price,selected_color=o.selected_color,selected_size=o.selected_size)
  s.add(db);s.commit();s.refresh(db);return order_out(db)
@app.get("/api/orders")
def get_orders(_=Depends(require_admin)):
 with Session(engine) as s:return [order_out(o) for o in s.scalars(select(OrderDB).order_by(OrderDB.created_at.desc())).all()]
@app.post("/api/orders/archive-finished")
def archive_finished_orders(_=Depends(require_admin)):
 with Session(engine) as s:
  orders=s.scalars(select(OrderDB).where(OrderDB.archived_at.is_(None),OrderDB.status.in_(["تم التوصيل","ملغي"]))).all()
  archived_at=datetime.utcnow()
  for order in orders: order.archived_at=archived_at
  s.commit();return {"ok":True,"count":len(orders)}
@app.patch("/api/orders/{oid}/archive")
def archive_order(oid:int,archived:bool=True,_=Depends(require_admin)):
 with Session(engine) as s:
  order=s.get(OrderDB,oid)
  if not order: raise HTTPException(404,"الطلب غير موجود")
  order.archived_at=datetime.utcnow() if archived else None
  s.commit();s.refresh(order);return order_out(order)
@app.patch("/api/orders/{oid}")
def update_order(oid:int,status:str,_=Depends(require_admin)):
 if status not in ["جديد","مؤكد","قيد التحضير","تم الشحن","تم التوصيل","ملغي"]: raise HTTPException(422,"حالة غير صحيحة")
 with Session(engine) as s:
  o=s.get(OrderDB,oid)
  if not o: raise HTTPException(404,"الطلب غير موجود")
  o.status=status;s.commit();return order_out(o)
@app.post("/api/uploads")
async def upload(file:UploadFile=File(...),_=Depends(require_admin)):
 if file.content_type not in ["image/jpeg","image/png","image/webp"]: raise HTTPException(400,"صيغة الصورة غير مدعومة")
 content=await file.read()
 if len(content)>5*1024*1024: raise HTTPException(400,"حجم الصورة يجب ألا يتجاوز 5 ميغابايت")
 if not all([os.getenv("CLOUDINARY_CLOUD_NAME"),os.getenv("CLOUDINARY_API_KEY"),os.getenv("CLOUDINARY_API_SECRET")]): raise HTTPException(503,"خدمة رفع الصور غير مهيأة")
 try:
  stream=io.BytesIO(content);stream.name=file.filename or "product-image"
  result=cloudinary.uploader.upload(stream,folder="lucea/products",resource_type="image",allowed_formats=["jpg","jpeg","png","webp"],transformation=[{"width":1400,"height":1400,"crop":"limit","quality":"auto","fetch_format":"auto"}])
  return {"url":result["secure_url"],"public_id":result["public_id"]}
 except Exception: raise HTTPException(502,"تعذر رفع الصورة، حاولي مرة أخرى")
