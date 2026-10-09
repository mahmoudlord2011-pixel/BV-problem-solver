import streamlit as st
import pandas as pd
import random
from supabase import create_client, Client

# ضبط إعدادات الصفحة
st.set_page_config(page_title="صوت المدرسة - School Voice", page_icon="🏫", layout="wide")

# ---------------------------------------------------------
# الاتصال بـ Supabase من خلال Secrets
# ---------------------------------------------------------
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ---------------------------------------------------------
# 🛡️ فلتر الألفاظ الممنوعة والنصوص المسيئة
# ---------------------------------------------------------
FORBIDDEN_WORDS = [
    # يمكن إضافة أي كلمات غير لائقة هنا
    "شتيمة", "احمق", "غبي", "كلب", "حمار", "زفت"
]

def contains_bad_words(text: str) -> bool:
    """فحص إذا كان النص يحتوي على أي كلمة غير لائقة"""
    text_lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

# ---------------------------------------------------------
# وظائف قراءة وتحديث قاعدة البيانات السحابية
# ---------------------------------------------------------
def load_data(include_pending: bool = False):
    """جلب البلاغات من السحابة (مع إمكانية تصفية البلاغات غير المعتمَدة)"""
    if include_pending:
        response = supabase.table("school_issues").select("*").execute()
    else:
        # للطلاب: عرض البلاغات المعتمدة فقط (تجاهل Pending)
        response = supabase.table("school_issues").select("*").neq("status", "Pending").execute()
        
    data = response.data
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame(columns=[
        "ticket_id", "title", "description", "location", 
        "priority", "is_anonymous", "student_name", 
        "upvotes", "status", "admin_reply"
    ])

def is_system_locked():
    response = supabase.table("system_config").select("kill_switch").eq("id", 1).execute()
    if response.data:
        return response.data[0]["kill_switch"]
    return False

def set_system_lock(status: bool):
    supabase.table("system_config").update({"kill_switch": status}).eq("id", 1).execute()

def reset_database():
    supabase.table("school_issues").delete().neq("ticket_id", "NONE").execute()

# ---------------------------------------------------------
# إدارة الجلسة والتسجيل (Session State)
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None

# 🛑 فحص Kill Switch الشامل
if is_system_locked():
    if st.session_state.user_role != "master":
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        
        st.error("⛔ النظام متوقف حالياً للصيانة أو بواسطة الإدارة العليا (Kill Switch Active).")
        st.info("لا يمكن لأي طالب أو مدير الوصول للنظام في الوقت الحالي.")
        st.write("---")
        
        with st.expander("👑 تسجيل دخول المالك الأعظم (Master Oody) للتحكم"):
            master_user = st.text_input("Master Username:")
            master_pass = st.text_input("Master Password:", type="password")
            if st.button("فك الحظر وتشغيل النظام 🔓"):
                if master_user == "oody" and master_pass == "Mahmoud@2011":
                    set_system_lock(False)
                    st.session_state.logged_in = True
                    st.session_state.user_role = "master"
                    st.session_state.username = "Master Oody 👑"
                    st.success("تم إيقاف الـ Kill Switch وبدء تشغيل النظام!")
                    st.rerun()
                else:
                    st.error("بيانات الماستر غير صحيحة!")
        st.stop()

# شاشة تسجيل الدخول
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #1E88E5;'>🔐 تسجيل الدخول إلى نظام صوت المدرسة</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("اسم المستخدم (Username):")
        password = st.text_input("كلمة السر (Password):", type="password")
        login_btn = st.button("تسجيل الدخول 🚀", use_container_width=True)

        if login_btn:
            if username == "student" and password == "student123":
                st.session_state.logged_in = True
                st.session_state.user_role = "student"
                st.session_state.username = "طالب / ولي أمر"
                st.rerun()
            elif username == "admin" and password == "Dr.RagabBV842":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "المدير (Dr. Ragab)"
                st.rerun()
            elif username == "oody" and password == "Mahmoud@2011":
                st.session_state.logged_in = True
                st.session_state.user_role = "master"
                st.session_state.username = "Master Oody 👑"
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة!")
    st.stop()

# ---------------------------------------------------------
# القائمة الجانبية
# ---------------------------------------------------------
st.sidebar.title(f"👤 {st.session_state.username}")
st.sidebar.caption(f"الصلاحية: `{st.session_state.user_role.upper()}`")

if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()

st.sidebar.write("---")

if st.session_state.user_role == "student":
    available_pages = ["🏠 الصفحة الرئيسية والتقديم", "🔔 متابعة مشكلة برقم البلاغ", "🏆 ماذا تغير؟ (What Changed?)"]
elif st.session_state.user_role == "admin":
    available_pages = ["👨‍💼 لوحة تحكم المدير (Dashboard)", "🏆 ماذا تغير؟ (What Changed?)"]
elif st.session_state.user_role == "master":
    available_pages = ["⚡ Kill Switch Control Panel"]

page = st.sidebar.radio("اختر الصفحة:", available_pages)

# ---------------------------------------------------------
# الصفحات
# ---------------------------------------------------------
if page == "🏠 الصفحة الرئيسية والتقديم":
    st.markdown("<h1 style='text-align: center; color: #1E88E5;'>📣 صوتك ممكن يغيّر مدرستك</h1>", unsafe_allow_html=True)
    st.write("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 تقديم مشكلة / اقتراح جديد")
        with st.form("issue_form", clear_on_submit=True):
            title = st.text_input("عنوان المشكلة / الاقتراح *")
            description = st.text_area("شرح التفاصيل *")
            location = st.text_input("مكان المشكلة 📍")
            priority = st.selectbox("درجة الأهمية ⚠️", ["عادية", "مهمة", "عاجلة"])
            anonymous = st.checkbox("🕶️ إخفاء الاسم")
            student_name = "مجهول" if anonymous else st.text_input("اسمك (اختياري)", value="طالب/ولي أمر")

            submitted = st.form_submit_button("إرسال البلاغ 🚀")

            if submitted:
                if not title or not description:
                    st.error("يرجى ملء عنوان وشرح المشكلة!")
                # 🛡️ تفعيل الفلترة التلقائية قبل الحفظ
                elif contains_bad_words(title) or contains_bad_words(description):
                    st.error("⚠️ عفواً، يحتوي البلاغ على كلمات غير لائقة تخالف القواعد. يرجى تعديل الصياغة.")
                else:
                    ticket_id = f"TCK-{random.randint(1000, 9999)}"
                    new_issue = {
                        "ticket_id": ticket_id,
                        "title": title,
                        "description": description,
                        "location": location,
                        "priority": priority,
                        "is_anonymous": "نعم" if anonymous else "لا",
                        "student_name": student_name,
                        "upvotes": 1,
                        "status": "Pending",  # 🛡️ تدخل مرحلة المراجعة أولاً قبل النشر
                        "admin_reply": ""
                    }
                    supabase.table("school_issues").insert(new_issue).execute()
                    st.success(f"تم إرسال بلاغك بنجاح! 🎉 رقم المتابعة: **{ticket_id}**")
                    st.info("💡 ملاحظة: سيعرض البلاغ للطلاب بعد مراجعة الإدارة له.")

    with col2:
        st.subheader("🔥 المشاكل الأكثر دعماً")
        df = load_data(include_pending=False) # عرض المعتمدة فقط
        if not df.empty:
            sorted_df = df.sort_values(by="upvotes", ascending=False)
            for idx, row in sorted_df.head(5).iterrows():
                with st.container():
                    st.markdown(f"**{row['title']}** ({row['priority']})")
                    st.caption(f"📍 المكان: {row['location']} | الحالة: `{row['status']}`")
                    c1, c2 = st.columns([1, 1])
                    c1.write(f"🔥 {row['upvotes']} دعم")
                    if c2.button("دعم 👍", key=f"upvote_{row['ticket_id']}"):
                        supabase.table("school_issues").update({"upvotes": int(row['upvotes']) + 1}).eq("ticket_id", row['ticket_id']).execute()
                        st.rerun()
                    st.divider()
        else:
            st.info("لا توجد مشاكل معتمدة حالياً.")

elif page == "🔔 متابعة مشكلة برقم البلاغ":
    st.title("🔔 متابعة حالة البلاغ")
    search_id = st.text_input("أدخل رقم البلاغ (مثال: TCK-1001):")

    if search_id:
        df = load_data(include_pending=True) # الطالب يقدر يتابع بلاغه حتى لو Pending
        if not df.empty:
            issue = df[df['ticket_id'].astype(str).str.upper() == search_id.strip().upper()]
            if not issue.empty:
                row = issue.iloc[0]
                st.subheader(f"📌 المشكلة: {row['title']}")
                st.write(f"**الوصف:** {row['description']}")
                st.write(f"**المكان:** {row['location']}")
                
                status = row['status']
                st.markdown("### 📊 مسار حالة الطلب:")
                if status == "Pending":
                    st.warning("⏳ البلاغ حالياً قيد المراجعة بواسطة المدير.")
                else:
                    s1 = "✅" if status in ["New", "Reviewing", "In Progress", "Solved"] else "⚪"
                    s2 = "👀" if status in ["Reviewing", "In Progress", "Solved"] else "⚪"
                    s3 = "🔧" if status in ["In Progress", "Solved"] else "⚪"
                    s4 = "🎉" if status == "Solved" else "⚪"

                    st.write(f"{s1} **تم الاستلام** -> {s2} **مراجعة** -> {s3} **جاري الحل** -> {s4} **تم الحل**")

                if pd.notna(row['admin_reply']) and str(row['admin_reply']).strip() != "":
                    st.info(f"💬 **رد المدير:** {row['admin_reply']}")
            else:
                st.error("رقم البلاغ غير موجود!")
        else:
            st.error("لا توجد بلاغات حالياً.")

elif page == "🏆 ماذا تغير؟ (What Changed?)":
    st.title("🏆 What Changed?")
    df = load_data(include_pending=False)
    solved_count = len(df[df['status'] == 'Solved']) if not df.empty else 0
    total_upvotes = int(df['upvotes'].sum()) if not df.empty else 0
    
    st.markdown("### 🎉 الإحصائيات الحالية:")
    m1, m2, m3 = st.columns(3)
    m1.metric("تم إصلاحها", f"{solved_count} مشكلة ✅")
    m2.metric("تم تنفيذها", "0 اقتراحات 💡")
    m3.metric("الأصوات والدعم", f"{total_upvotes} صوت 👥")

elif page == "👨‍💼 لوحة تحكم المدير (Dashboard)":
    st.title("👨‍💼 لوحة تحكم المدير")
    df = load_data(include_pending=True) # المدير يشوف كل حاجة بما فيها المعلقة
    
    if not df.empty:
        # قسم البلاغات الجديدة المعلقة
        pending_df = df[df['status'] == 'Pending']
        if not pending_df.empty:
            st.warning(f"📩 لديك ({len(pending_df)}) بلاغ جديد ينتظر المراجعة والموافقة!")
            for idx, row in pending_df.iterrows():
                with st.expander(f"🔍 بلاغ: {row['title']} (من: {row['student_name']})"):
                    st.write(f"**الشرح:** {row['description']}")
                    st.write(f"**المكان:** {row['location']} | **الأهمية:** {row['priority']}")
                    col_acc, col_rej = st.columns(2)
                    if col_acc.button("موافقة ونشر البلاغ ✅", key=f"app_{row['ticket_id']}"):
                        supabase.table("school_issues").update({"status": "New"}).eq("ticket_id", row['ticket_id']).execute()
                        st.success("تمت الموافقة بنجاح وأصبح البلاغ ظاهراً للجميع!")
                        st.rerun()
                    if col_rej.button("حذف البلاغ (مسيء/وهمي) 🗑️", key=f"del_{row['ticket_id']}"):
                        supabase.table("school_issues").delete().eq("ticket_id", row['ticket_id']).execute()
                        st.warning("تم حذف البلاغ المسيء!")
                        st.rerun()
            st.write("---")

        st.subheader("📋 قائمة المشاكل المعتمدة (مرتبة بالأعلى دعماً)")
        active_df = df[df['status'] != 'Pending'].sort_values(by="upvotes", ascending=False)
        if not active_df.empty:
            st.dataframe(active_df[["status", "upvotes", "title", "ticket_id"]], use_container_width=True)

            selected_ticket = st.selectbox("اختر رقم البلاغ للتعديل:", active_df['ticket_id'].tolist())
            if selected_ticket:
                current_row = df[df['ticket_id'] == selected_ticket].iloc[0]
                new_status = st.selectbox("تغيير الحالة:", ["New", "Reviewing", "In Progress", "Solved"], index=["New", "Reviewing", "In Progress", "Solved"].index(current_row['status']))
                admin_reply = st.text_input("رد المدير للطالب:", value=str(current_row['admin_reply']) if pd.notna(current_row['admin_reply']) else "")

                if st.button("حفظ التغييرات 💾"):
                    supabase.table("school_issues").update({"status": new_status, "admin_reply": admin_reply}).eq("ticket_id", selected_ticket).execute()
                    st.success("تم التحديث!")
                    st.rerun()
        else:
            st.info("لا توجد مشاكل معتمدة حالياً.")
    else:
        st.info("لا توجد بلاغات بالسيستم.")

elif page == "⚡ Kill Switch Control Panel":
    st.title("👑 لوحة تحكم الماستر - أودي")
    is_locked = is_system_locked()

    if is_locked:
        st.error("🔴 النظام حالياً: مُغلق بالكامل (OFFLINE).")
        if st.button("🟢 تشغيل الويبسايت للجميع (Enable System)"):
            set_system_lock(False)
            st.rerun()
    else:
        st.success("🟢 النظام حالياً: يعمل بشكل طبيعي (ONLINE).")
        if st.button("🔴 تفعيل ה-Kill Switch (Shutdown System)"):
            set_system_lock(True)
            st.rerun()

    st.write("---")
    if st.button("⚠️ تصفير جميع البلاغات والإحصائيات نهائياً"):
        reset_database()
        st.success("تم تصفير الداتابيز بالكامل!")
        st.rerun()
