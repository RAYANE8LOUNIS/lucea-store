# Lucea — متجر جزائري بالدفع عند الاستلام

نسخة أولى عربية بالكامل وباتجاه RTL. تحتوي على واجهة عامة، نموذج طلب COD، ولوحة إدارة للمنتجات والطلبات.

## التشغيل السريع

### الواجهة
```bash
cd frontend
npm install
npm run dev
```

### الخادم
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

تعمل الواجهة افتراضياً على `http://localhost:3000` والخادم على `http://localhost:8000`.

بيانات الدخول التجريبية: `admin@lucea.dz` / `Lucea2026!`، ويجب تغييرها عبر متغيرات البيئة قبل الإنتاج.
