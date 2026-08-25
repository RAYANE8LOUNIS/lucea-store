'use client';

import {useEffect,useState} from 'react';
import {ArrowLeft,ArrowRight,Building2,CheckCircle2,House,Images,ShieldCheck,Truck} from 'lucide-react';

const api='/backend-api';
const wilayas=['أدرار','الشلف','الأغواط','أم البواقي','باتنة','بجاية','بسكرة','بشار','البليدة','البويرة','تمنراست','تبسة','تلمسان','تيارت','تيزي وزو','الجزائر','الجلفة','جيجل','سطيف','سعيدة','سكيكدة','سيدي بلعباس','عنابة','قالمة','قسنطينة','المدية','مستغانم','المسيلة','معسكر','ورقلة','وهران','البيض','إليزي','برج بوعريريج','بومرداس','الطارف','تندوف','تيسمسيلت','الوادي','خنشلة','سوق أهراس','تيبازة','ميلة','عين الدفلى','النعامة','عين تموشنت','غرداية','غليزان','تيميمون','برج باجي مختار','أولاد جلال','بني عباس','عين صالح','عين قزام','تقرت','جانت','المغير','المنيعة'];
const imageUrl=(url:string)=>url?.startsWith('/uploads')?api+url:url||'/logo.jpg';
const initialForm={customer_name:'',phone:'',wilaya:'',commune:'',address:'',quantity:1,selected_color:'',selected_size:'',delivery_method:''};

export default function Home(){
 const[products,setProducts]=useState<any[]>([]);
 const[selected,setSelected]=useState<any>(null);
 const[activeImage,setActiveImage]=useState(0);
 const[done,setDone]=useState(false);
 const[busy,setBusy]=useState(false);
 const[form,setForm]=useState<any>(initialForm);

 useEffect(()=>{fetch(api+'/api/products').then(r=>r.json()).then(setProducts).catch(()=>{})},[]);

 function choose(product:any){
  setSelected(product);
  setActiveImage(0);
  setDone(false);
  setForm({...initialForm});
 }

 function deliveryFee(){
  if(!selected||!form.delivery_method)return 0;
  return Number(form.delivery_method==='desk'?selected.delivery_desk:selected.delivery_home)||0;
 }

 async function submit(e:React.FormEvent){
  e.preventDefault();
  if(busy)return;
  setBusy(true);
  try{
   const response=await fetch(api+'/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...form,product_id:selected.id})});
   if(!response.ok)throw Error();
   setDone(true);
  }catch{
   alert('تحققي من المعلومات وخيارات المنتج وطريقة التوصيل ثم حاولي مرة أخرى');
  }finally{
   setBusy(false);
  }
 }

 return <main>
  <header className="nav"><div className="brand"><img src="/logo.jpg" alt="شعار Lucea"/><span>Lucea</span></div><a href="#products">المنتجات <ArrowLeft size={16}/></a></header>
  <section className="hero"><div><p className="eyebrow">عناية يومية بإحساس Lucea</p><h1>جمالك يبدأ<br/><em>من لحظتك.</em></h1><p className="lead">منتجات مختارة بعناية، مع توصيل إلى كل الولايات والدفع عند الاستلام.</p><a className="primary" href="#products">اكتشفي المنتجات <ArrowLeft size={18}/></a><div className="trust"><span><Truck/> توصيل للـ 69 ولاية</span><span><ShieldCheck/> الدفع عند الاستلام</span></div></div><div className="hero-art"><div className="orb"><img src="/logo.jpg" alt="Lucea"/></div></div></section>
  <section className="product-section" id="products"><div className="section-title"><p className="eyebrow">اختاري ما يناسبك</p><h2>منتجات Lucea</h2></div><div className="products-grid">{products.length?products.map(p=><article className="product-card-single" key={p.id}><div className="product-photo"><img src={imageUrl(p.images?.[0]||p.image)} alt={p.name}/>{p.marketing_badge&&<span className="marketing-badge">{p.marketing_badge}</span>}{p.images?.length>1&&<span className="gallery-count"><Images aria-hidden="true" size={14}/> {p.images.length} صور</span>}</div><div className="product-info"><h3>{p.name}</h3><p>{p.description}</p><VariantSummary product={p}/><div className="price"><strong>{Number(p.price).toLocaleString('ar-DZ')} دج</strong>{p.old_price&&<del>{Number(p.old_price).toLocaleString('ar-DZ')} دج</del>}</div>{p.urgency_text&&<div className="urgency-message"><i aria-hidden="true"/>{p.urgency_text}</div>}<button className="primary wide" onClick={()=>choose(p)}>اختيار وطلب <ArrowLeft aria-hidden="true" size={18}/></button><div className="delivery-summary"><span>مكتب التوصيل: {Number(p.delivery_desk||0).toLocaleString('ar-DZ')} دج</span><span>توصيل للمنزل: {Number(p.delivery_home||0).toLocaleString('ar-DZ')} دج</span></div></div></article>):<div className="empty"><h2>لا توجد منتجات متاحة حالياً</h2></div>}</div></section>
  <footer>© 2026 Lucea · صُنع بعناية لروتينك اليومي</footer>
  {selected&&<div className="modal-backdrop"><div className="modal product-order-modal">{done?<div className="success"><CheckCircle2 aria-hidden="true" size={48}/><h2>تم تسجيل طلبك بنجاح</h2><p>سنتصل بك قريباً لتأكيد تفاصيل المنتج والتوصيل.</p><button className="primary" onClick={()=>setSelected(null)}><ArrowRight aria-hidden="true"/> العودة إلى المنتجات</button></div>:<><button className="close" aria-label="إغلاق" onClick={()=>setSelected(null)}>×</button><button type="button" className="order-back" onClick={()=>setSelected(null)}><ArrowRight aria-hidden="true"/> العودة إلى المنتجات</button><div className="order-product-gallery"><img className="order-main-image" src={imageUrl((selected.images?.length?selected.images:[selected.image])[activeImage])} alt={selected.name}/>{(selected.images||[]).length>1&&<div className="gallery-thumbs">{selected.images.map((url:string,i:number)=><button type="button" aria-label={`عرض الصورة ${i+1}`} className={i===activeImage?'selected':''} key={url} onClick={()=>setActiveImage(i)}><img src={imageUrl(url)} alt=""/></button>)}</div>}</div><p className="eyebrow">طلب {selected.name}</p><h2>أكملي اختيارك</h2>{selected.urgency_text&&<div className="modal-urgency"><i aria-hidden="true"/>{selected.urgency_text}</div>}<form onSubmit={submit}>{selected.colors?.length>0&&<label>اللون<select required value={form.selected_color} onChange={e=>setForm({...form,selected_color:e.target.value})}><option value="">اختاري اللون</option>{selected.colors.map((v:string)=><option key={v}>{v}</option>)}</select></label>}{selected.sizes?.length>0&&<label>المقاس<select required value={form.selected_size} onChange={e=>setForm({...form,selected_size:e.target.value})}><option value="">اختاري المقاس</option>{selected.sizes.map((v:string)=><option key={v}>{v}</option>)}</select></label>}<label>الاسم الكامل<input required value={form.customer_name} onChange={e=>setForm({...form,customer_name:e.target.value})}/></label><label>رقم الهاتف<input required inputMode="tel" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/></label><div className="grid"><label>الولاية<select required value={form.wilaya} onChange={e=>setForm({...form,wilaya:e.target.value})}><option value="">اختاري الولاية</option>{wilayas.map(w=><option key={w}>{w}</option>)}</select></label><label>البلدية<input required value={form.commune} onChange={e=>setForm({...form,commune:e.target.value})}/></label></div><DeliveryChoices product={selected} value={form.delivery_method} onChange={(delivery_method:string)=>setForm({...form,delivery_method})}/>{form.delivery_method==='home'&&<label>العنوان الكامل<textarea required minLength={5} value={form.address} onChange={e=>setForm({...form,address:e.target.value})}/></label>}<label>الكمية<input type="number" min="1" max="20" value={form.quantity} onChange={e=>setForm({...form,quantity:Number(e.target.value)})}/></label><div className="total"><div><span>{selected.name}{form.selected_color&&` · ${form.selected_color}`}{form.selected_size&&` · ${form.selected_size}`}</span>{form.delivery_method&&<small>{form.delivery_method==='desk'?'الاستلام من مكتب التوصيل':'التوصيل إلى المنزل'} · {deliveryFee().toLocaleString('ar-DZ')} دج</small>}</div><strong>{(selected.price*form.quantity+deliveryFee()).toLocaleString('ar-DZ')} دج</strong></div><button className="primary wide" disabled={busy}>{busy?'جارٍ التسجيل...':'تأكيد الطلب'}</button></form></>}</div></div>}
 </main>;
}

function DeliveryChoices({product,value,onChange}:{product:any,value:string,onChange:(value:string)=>void}){
 return <fieldset className="delivery-methods"><legend>طريقة التوصيل</legend><label className={value==='desk'?'selected':''}><input type="radio" name="delivery_method" value="desk" required checked={value==='desk'} onChange={()=>onChange('desk')}/><Building2/><span><b>الاستلام من مكتب التوصيل</b><small>تستلمين طلبك من أقرب مكتب</small></span><strong>{Number(product.delivery_desk||0).toLocaleString('ar-DZ')} دج</strong></label><label className={value==='home'?'selected':''}><input type="radio" name="delivery_method" value="home" required checked={value==='home'} onChange={()=>onChange('home')}/><House/><span><b>التوصيل إلى المنزل</b><small>يصل الطلب إلى عنوانك</small></span><strong>{Number(product.delivery_home||0).toLocaleString('ar-DZ')} دج</strong></label></fieldset>;
}

function VariantSummary({product}:{product:any}){return <div className="variant-summary">{product.colors?.length>0&&<span>الألوان: {product.colors.join('، ')}</span>}{product.sizes?.length>0&&<span>المقاسات: {product.sizes.join('، ')}</span>}</div>}
