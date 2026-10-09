import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, time
import extra_streamlit_components as stx

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Bright Vision - نظام الكانتين الذكي",
    page_icon="🍔",
    layout="wide"
)

# ---------------------------------------------------------
# Custom CSS for Video-Matched UI, Animations & Dynamic Theme
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Direction and Font */
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Keyframe Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 10px rgba(107, 17, 176, 0.4); }
        50% { box-shadow: 0 0 22px rgba(168, 85, 247, 0.8); }
        100% { box-shadow: 0 0 10px rgba(107, 17, 176, 0.4); }
    }

    .stAppViewContainer {
        animation: fadeIn 0.6s ease-out;
    }

    .sovereign-header {
        background: linear-gradient(135deg, #2b004a 0%, #150027 50%, #3b0764 100%);
        color: #facc15;
        padding: 18px 28px;
        border-radius: 16px;
        border: 2px solid #9333ea;
        animation: pulseGlow 3s infinite alternate;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(10px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #0f172a;
        padding: 10px;
        border-radius: 14px;
        border: 1px solid #1e293b;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #1e293b;
        border-radius: 10px;
        color: #cbd5e1;
        font-weight: bold;
        padding: 0px 22px;
        border: 1px solid #334155;
        transition: all 0.3s ease-in-out;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #334155;
        color: #ffffff;
        transform: translateY(-2px);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%) !important;
        color: #ffffff !important;
        border: 1px solid #f87171 !important;
        box-shadow: 0px 4px 15px rgba(239, 68, 68, 0.5);
    }

    .order-card {
        border: 2px solid #334155;
        border-radius: 16px;
        padding: 18px;
        background: linear-gradient(145deg, #1e293b, #0f172a);
        margin-bottom: 18px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .order-card:hover {
        transform: translateY(-4px);
        border-color: #a855f7;
    }

    .change-box {
        background: linear-gradient(90deg, #15803d 0%, #166534 100%);
        color: #ffffff;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        text-align: center;
        margin: 12px 0;
        box-shadow: 0px 2px 8px rgba(22, 101, 52, 0.4);
    }

    .stButton>button {
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: all 0.25s ease-in-out !important;
    }

    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 4px 14px rgba(255, 255, 255, 0.15);
    }

    .stButton>button[kind="primary"] {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: none !important;
    }

    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
        box-shadow: 0px 4px 18px rgba(37, 99, 235, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# Cookie Manager Initialization
cookie_manager = stx.CookieManager()

# Audio Bell Function for New Orders
def trigger_notification_bell():
    bell_html = """
    <audio autoplay style="display:none;">
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    st.components.v1.html(bell_html, height=0)

# ⏰ دالة فحص المواعيد وأيام عمل الكانتين للطلاب والزوار
def check_canteen_working_hours():
    now = datetime.now()
    
    # 1. التحقق من أيام العطلة (الجمعة = 4، السبت = 5)
    if now.weekday() in [4, 5]:
        return False, "الكانتين مغلق اليوم (عطلة نهاية الأسبوع: الجمعة والسبت) 🔴"
    
    # 2. التحقق من الوقت (من 8:00 صباحاً حتى 2:15 ظهراً)
    start_time = time(8, 0)
    end_time = time(14, 15)
    current_time = now.time()
    
    if not (start_time <= current_time <= end_time):
        return False, f"الكانتين مغلق حالياً 🔴\nالوقت الحالي: {now.strftime('%I:%M %p')}\nمواعيد الطلب الرسمية للطلاب والزوار من 8:00 صباحاً حتى 2:15 ظهراً."
        
    return True, "الكانتين مفتوح للطلب 🟢"

# ---------------------------------------------------------
# Supabase REST API Configuration
# ---------------------------------------------------------
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def db_get(table):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=*", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception:
        pass
    return pd.DataFrame()

def db_insert(table, data):
    try:
        res = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, json=data, timeout=5)
        return res.status_code in [200, 201]
    except Exception:
        return False

def db_update(table, match_col, match_val, data):
    try:
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?{match_col}=eq.{match_val}", headers=HEADERS, json=data, timeout=5)
        return res.status_code in [200, 204]
    except Exception:
        return False

# ---------------------------------------------------------
# Session Memory Initialization
# ---------------------------------------------------------
# 💥 تم تفريغ المنيو الافتراضي بالكامل
if "demo_products" not in st.session_state:
    st.session_state.demo_products = pd.DataFrame(columns=[
        "id", "name", "category", "cost_price", "selling_price", "stock"
    ])

if "demo_sales" not in st.session_state:
    st.session_state.demo_sales = pd.DataFrame(columns=[
        "id", "student_name", "student_class", "items_str", "order_notes",
        "total_price", "paid_amount", "profit", "status", "created_at"
    ])

if "cart_items" not in st.session_state:
    st.session_state.cart_items = []

if "system_locked" not in st.session_state:
    st.session_state.system_locked = False

if "play_bell" not in st.session_state:
    st.session_state.play_bell = False

# Helper Functions
def get_products():
    df = db_get("products")
    if not df.empty and "stock" in df.columns:
        return df
    return st.session_state.demo_products

def get_sales():
    df = db_get("sales")
    if not df.empty and "total_price" in df.columns:
        return df
    return st.session_state.demo_sales

def check_system_lock():
    df = db_get("system_config")
    if not df.empty and "key" in df.columns and "value" in df.columns:
        row = df[df["key"] == "is_locked"]
        if not row.empty:
            return str(row.iloc[0]["value"]).lower() == "true"
    return st.session_state.system_locked

def toggle_system_lock(locked_state: bool):
    st.session_state.system_locked = locked_state
    db_update("system_config", "key", "is_locked", {"value": "true" if locked_state else "false"})

# ---------------------------------------------------------
# User Accounts Definition
# ---------------------------------------------------------
ACCOUNTS = {
    "oody": {"pass": "Mahmoud@2011", "role": "master", "name": "الملك الأعلى للنظام | MASTER OODY مرحباً بك يا 👑"},
    "admin": {"pass": "Dr.RagabBV842", "role": "admin", "name": "مدير النظام | Dr. Ragab"},
    "canteen": {"pass": "canteen 842", "role": "canteen", "name": "حساب الكانتين والمطبخ 🍔"},
    "student": {"pass": "student123", "role": "student", "name": "حساب الطلاب والزوار 🎓"}
}

GUEST_DEMO_ACCOUNT = {
    "role": "student",
    "name": "زائر الديمو التجريبي 🎓"
}

# Persistent Auto-Login via Cookies
saved_user = cookie_manager.get("auth_user")

if "current_user" not in st.session_state:
    if saved_user in ACCOUNTS:
        st.session_state.current_user = ACCOUNTS[saved_user]
    elif saved_user == "guest":
        st.session_state.current_user = GUEST_DEMO_ACCOUNT
    else:
        st.session_state.current_user = None

if st.session_state.play_bell:
    trigger_notification_bell()
    st.session_state.play_bell = False

# ---------------------------------------------------------
# 1. Login Screen
# ---------------------------------------------------------
if st.session_state.current_user is None:
    st.title("🍔 نظام الكانتين الذكي - تسجيل الدخول")
    st.divider()
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        u_name = st.text_input("اسم المستخدم (Username):")
        u_pass = st.text_input("كلمة المرور (Password):", type="password")
        remember_me = st.checkbox("تذكرني على هذا الجهاز 💾", value=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔑 تسجيل الدخول", type="primary", use_container_width=True):
                if u_name in ACCOUNTS and ACCOUNTS[u_name]["pass"] == u_pass:
                    st.session_state.current_user = ACCOUNTS[u_name]
                    if remember_me:
                        cookie_manager.set("auth_user", u_name, key="set_user_cookie")
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة!")
        with col_btn2:
            if st.button("🚀 دخول سريع بنظام الديمو (Guest Demo)", use_container_width=True):
                st.session_state.current_user = GUEST_DEMO_ACCOUNT
                if remember_me:
                    cookie_manager.set("auth_user", "guest", key="set_guest_cookie")
                st.rerun()
                
    st.stop()

# ---------------------------------------------------------
# Header & Master Dashboard Info
# ---------------------------------------------------------
user = st.session_state.current_user
user_role = user["role"]

col_header, col_logout = st.columns([5, 1])
with col_header:
    st.markdown(f"<div class='sovereign-header'><h3>{user['name']}</h3></div>", unsafe_allow_html=True)
with col_logout:
    if st.button("تسجيل الخروج 🚪", use_container_width=True):
        st.session_state.current_user = None
        cookie_manager.delete("auth_user", key="delete_user_cookie")
        st.rerun()

# --- Master Control Panel (خصيصاً لـ MASTER OODY) ---
if user_role == "master":
    st.markdown("### ⚡ لوحة التحكم المطلقة (Master Control)")
    c_status, c_switch = st.columns([2, 2])
    
    is_locked = check_system_lock()
    
    with c_status:
        if is_locked:
            st.error("حالة النظام الحالية: النظام متوقف بالكامل 🔴")
        else:
            st.success("حالة النظام الحالية: يعمل بالكامل 🟢")
            
    with c_switch:
        if is_locked:
            if st.button("🔓 إيقاف قفل النظام (تشغيل)", type="primary", use_container_width=True):
                toggle_system_lock(False)
                st.rerun()
        else:
            if st.button("🚨 (Kill Switch) إيقاف النظام بالكامل", type="primary", use_container_width=True):
                toggle_system_lock(True)
                st.rerun()

st.divider()
st.title("🍔 Bright Vision - نظام الكانتين الذكي")

# 🔴 1. فحص القفل الطارئ المباشر للنظام
if check_system_lock() and user_role not in ["master"]:
    st.error("🔒 النظام مغلق حالياً بقرار من إدارة المدرسة.")
    st.warning("الرجاء التواصل مع الإدارة لإعادة التفعيل.")
    st.stop()

# 🔴 2. القفل الفوري والمباشر لحسابات الطلاب والزوار خارج المواعيد
if user_role == "student":
    is_open, open_msg = check_canteen_working_hours()
    if not is_open:
        st.error(f"🔒 {open_msg}")
        st.info("💡 يمكن للطلاب والزوار تقديم الطلبات فقط خلال مواعيد العمل الرسمية (من 8:00 صباحاً حتى 2:15 ظهراً - من الأحد إلى الخميس).")
        st.stop()

# ---------------------------------------------------------
# Main Navigation Tabs Layout
# ---------------------------------------------------------
if user_role in ["master", "admin"]:
    tabs = st.tabs(["تسجيل طلب جديد 🛒", "الأوردرات 👨‍🍳", "إدارة المنتجات ⚙️", "المبيعات والتقارير 📊"])
    tab_sales, tab_orders, tab_products, tab_reports = tabs[0], tabs[1], tabs[2], tabs[3]
elif user_role == "canteen":
    tabs = st.tabs(["الأوردرات 👨‍🍳", "إدارة المنتجات ⚙"])
    tab_orders, tab_products = tabs[0], tabs[1]
    tab_sales, tab_reports = None, None
else:  # Student / Guest
    tabs = st.tabs(["تسجيل طلب جديد 🛒"])
    tab_sales = tabs[0]
    tab_orders, tab_products, tab_reports = None, None, None

# --- TAB: STUDENT NEW ORDER (شاشة الطلب للطلاب) ---
if tab_sales is not None:
    with tab_sales:
        st.subheader("🛒 قائمة الطلبات المتاحة")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            student_name = st.text_input("اسم الطالب: (مثال: محمود مصطفى)", placeholder="محمود مصطفى", key="std_name_input")
        with col_s2:
            student_class = st.text_input("الفصل الدراسي: (مثال: 10-A)", placeholder="10-A", key="std_class_input")
            
        prods = get_products()
        if prods.empty or "stock" not in prods.columns:
            st.info("لا توجد منتجات مسجلة في المنيو حالياً. يرجى الانتظار حتى يقوم الكانتين بإضافة الاصناف المتاحة.")
        else:
            avail_prods = prods[prods["stock"] > 0]
            if avail_prods.empty:
                st.info("المنتجات الحالية غير متوفرة بالمخزن حالياً.")
            else:
                st.markdown("---")
                for idx, item in avail_prods.iterrows():
                    col_i1, col_i2, col_i3 = st.columns([3, 2, 1])
                    with col_i1:
                        st.markdown(f"**{item['name']}**")
                    with col_i2:
                        st.markdown(f"🏷️ **{item['selling_price']} ج.م**")
                    with col_i3:
                        if st.button("إضافة ➕", key=f"add_{item['name']}_{idx}", use_container_width=True):
                            st.session_state.cart_items.append(item.to_dict())
                            st.rerun()
            
            st.markdown("---")
            st.subheader("🛒 سلة الطلبات الحالية")
            
            if not st.session_state.cart_items:
                st.info("السلة فارغة حالياً. قم بإضافة أصناف من الأعلى.")
            else:
                total_sum = 0.0
                for item in st.session_state.cart_items:
                    st.markdown(f"• **{item['name']}** ({item['selling_price']} ج.م)")
                    total_sum += float(item['selling_price'])
                
                st.markdown(f"### **الإجمالي: <span style='color:#00ff66;'>{total_sum:.0f} ج.م</span>**", unsafe_allow_html=True)
                
                paid_amount = st.number_input("المبلغ المدفوع (معاك كام؟):", min_value=0.0, step=5.0, value=total_sum)
                
                # 📝 إضافة خانة الملاحظات للطلب (Order Notes)
                order_notes = st.text_area("📝 ملاحظات إضافية على الطلب (اختياري):", placeholder="مثال: من غير كاتشب / العيش محمص / بدون مخلل...", key="std_order_notes")

                col_btn_del1, col_btn_del2 = st.columns(2)
                with col_btn_del1:
                    if st.button("حذف ➖ (آخر منتج)", use_container_width=True):
                        if st.session_state.cart_items:
                            st.session_state.cart_items.pop()
                            st.rerun()
                with col_btn_del2:
                    if st.button("حذف السلة 🗑️", use_container_width=True):
                        st.session_state.cart_items = []
                        st.rerun()
                
                if st.button("🚀 اطلب من الكانتين", type="primary", use_container_width=True):
                    if not student_name or not student_class:
                        st.error("❌ يرجى كتابة اسم الطالب والفصل الدراسي أولاً!")
                    elif paid_amount < total_sum:
                        st.error(f"❌ المبلغ المدفوع ({paid_amount} ج.م) أقل من إجمالي الطلب ({total_sum} ج.م)!")
                    else:
                        items_str = ", ".join([f"{i['name']} ({i['selling_price']} ج.م)" for i in st.session_state.cart_items])
                        sale_record = {
                            "student_name": student_name,
                            "student_class": student_class,
                            "items_str": items_str,
                            "order_notes": order_notes.strip() if order_notes else "لا يوجد",
                            "total_price": total_sum,
                            "paid_amount": paid_amount,
                            "profit": total_sum * 0.2,
                            "status": "قيد الانتظار ⏳",
                            "created_at": datetime.now().strftime("%I:%M %p")
                        }
                        
                        db_insert("sales", sale_record)
                        st.session_state.demo_sales = pd.concat([st.session_state.demo_sales, pd.DataFrame([sale_record])], ignore_index=True)
                        
                        st.session_state.cart_items = []
                        st.session_state.play_bell = True
                        st.success("🔔 تم إرسال طلبك للكانتين بنجاح!")
                        st.rerun()

# --- TAB: KITCHEN / CANTEEN ORDERS (شاشة المطبخ والطلبات) ---
if tab_orders is not None:
    with tab_orders:
        st.subheader("👨‍🍳 شاشة المطبخ والطلبات")
        sales_df = get_sales()
        
        if sales_df.empty:
            st.info("لا توجد طلبات جديدة حالياً.")
        else:
            active_orders = sales_df[sales_df.get("status", "قيد الانتظار ⏳") == "قيد الانتظار ⏳"] if "status" in sales_df.columns else sales_df
            
            if active_orders.empty:
                st.success("✨ جميع الطلبات تم تقديمها بنجاح!")
            else:
                for idx, row in active_orders.iterrows():
                    notes_display = row.get('order_notes', 'لا يوجد')
                    if not notes_display or str(notes_display).strip() == "":
                        notes_display = "لا يوجد"

                    st.markdown(f"""
                    <div class="order-card">
                        <h3>طلب: {row.get('student_name', 'طالب')} ({row.get('student_class', 'عام')})</h3>
                        <p><b>الأصناف:</b> {row.get('items_str', 'منتجات متنوعة')}</p>
                        <p><b>📝 ملاحظات الطلب:</b> <span style="color: #facc15;">{notes_display}</span></p>
                        <p><b>الحساب:</b> {row.get('total_price', 0)} ج.م | <b>المدفوع:</b> {row.get('paid_amount', 0)} ج.م</p>
                        <div class="change-box">
                            🟡 الباقي للطالب: {float(row.get('paid_amount', 0)) - float(row.get('total_price', 0)):.0f} ج.م
                        </div>
                        <p>⏰ <b>الوقت:</b> {row.get('created_at', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"✅ إتمام تقديم الطلب #{idx+1}", key=f"complete_{idx}", type="primary"):
                        if "status" in st.session_state.demo_sales.columns:
                            st.session_state.demo_sales.at[idx, "status"] = "تم التقديم ✅"
                        st.success("تم إتمام الطلب!")
                        st.rerun()

# --- TAB 2: PRODUCTS MANAGEMENT ---
if tab_products is not None:
    with tab_products:
        st.subheader("⚙ إضافة منتج جديد للمنيو")
        with st.form("add_product_form"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                prod_name = st.text_input("اسم المنتج:")
                prod_cat = st.selectbox("القسم:", ["ساندوتشات", "مشروبات", "مخبوزات", "وجبات", "أخرى"])
            with col_p2:
                cost_p = st.number_input("سعر التكلفة (ج.م):", min_value=0.0, value=10.0, step=1.0)
                sell_p = st.number_input("سعر البيع (ج.م):", min_value=0.0, value=15.0, step=1.0)
                stock_q = st.number_input("الكمية الأولية بالمخزن:", min_value=1, value=20, step=1)
                
            if st.form_submit_button("➕ إضافة المنتج", use_container_width=True):
                if prod_name:
                    new_item = {
                        "name": prod_name,
                        "category": prod_cat,
                        "cost_price": cost_p,
                        "selling_price": sell_p,
                        "stock": stock_q
                    }
                    db_insert("products", new_item)
                    st.session_state.demo_products = pd.concat([st.session_state.demo_products, pd.DataFrame([new_item])], ignore_index=True)
                    st.success(f"تمت إضافة ({prod_name}) بنجاح إلى المنيو!")
                    st.rerun()

        st.divider()
        st.subheader("📋 قائمة المنتجات والمخزون الحالي")
        st.dataframe(get_products(), use_container_width=True)

# --- TAB 3: REPORTS & ANALYTICS ---
if tab_reports is not None:
    with tab_reports:
        st.subheader("📊 إحصائيات وتقارير المبيعات المحفوظة")
        
        if user_role in ["master", "admin"]:
            with st.expander("⚠️ منطقة التحكم الإداري (إعادة ضبط الإحصائيات)"):
                st.warning("تنبيه: مسح الإحصائيات سيقوم بتصفير كافة المبيعات والتقارير الحالية!")
                if st.button("🔄 إعادة ضبط وتصفير جميع الإحصائيات", type="primary", use_container_width=True):
                    st.session_state.demo_sales = pd.DataFrame(columns=[
                        "id", "student_name", "student_class", "items_str", "order_notes",
                        "total_price", "paid_amount", "profit", "status", "created_at"
                    ])
                    try:
                        requests.delete(f"{SUPABASE_URL}/rest/v1/sales?id=gt.0", headers=HEADERS)
                    except Exception:
                        pass
                    st.success("✅ تم إعادة ضبط وتصفير جميع الإحصائيات بنجاح!")
                    st.rerun()
            st.markdown("---")

        sales_df = get_sales()
        
        if sales_df.empty:
            st.info("لا توجد مبيعات مسجلة حتى الآن.")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("إجمالي المبيعات", f"{sales_df['total_price'].sum():.2f} ج.م")
            m2.metric("إجمالي الأرباح", f"{sales_df['profit'].sum():.2f} ج.م")
            m3.metric("عدد العمليات", f"{len(sales_df)}")
            
            st.divider()
            if "product_name" in sales_df.columns:
                fig = px.bar(sales_df, x="product_name", y="total_price", color="product_name", title="📈 توزيع المبيعات حسب المنتج")
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📜 سجل العمليات التفصيلي")
            st.dataframe(sales_df, use_container_width=True)
