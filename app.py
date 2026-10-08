import streamlit as st
import pandas as pd
import os
import random

# ضبط إعدادات الصفحة
st.set_page_config(page_title="صوت المدرسة - School Voice", page_icon="🏫", layout="wide")

DB_FILE = "school_issues.csv"
CONFIG_FILE = "system_config.csv"

# ---------------------------------------------------------
# 1. إدارة البيانات والداتابيز (ضمان التصفير والحفظ)
# ---------------------------------------------------------
def init_db():
    # إعادة إنشاء ملف CSV فارغ تماماً إذا لم يكن موجوداً
    if not os.path.exists(DB_FILE):
        reset_database()
    
    if not os.path.exists(CONFIG_FILE):
        config_df = pd.DataFrame([{"kill_switch": False}])
        config_df.to_csv(CONFIG_FILE, index=False)

def reset_database():
    """إنشاء قاعدة بيانات فارغة تماماً بدون أي إحصائيات أو أرقام وهمية"""
    df = pd.DataFrame(columns=[
        "ticket_id", "title", "description", "location", 
        "priority", "is_anonymous", "student_name", 
        "upvotes", "status", "admin_reply"
    ])
    df.to_csv(DB_FILE, index=False)

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=[
        "ticket_id", "title", "description", "location", 
        "priority", "is_anonymous", "student_name", 
        "upvotes", "status", "admin_reply"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def is_system_locked():
    if os.path.exists(CONFIG_FILE):
        config_df = pd.read_csv(CONFIG_FILE)
        return bool(config_df.iloc[0]["kill_switch"])
    return False

def set_system_lock(status: bool):
    config_df = pd.DataFrame([{"kill_switch": status}])
    config_df.to_csv(CONFIG_FILE, index=False)

init_db()

# ---------------------------------------------------------
# 2. إدارة الجلسة والتسجيل (Session State)
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None

# 🛑 فحص زر القتل (Kill Switch) الشامل والصارم
if is_system_locked():
    # إذا كان المستخدم الحالي ليس الماستر أودي، يتم طرده فوراً وحظر الوصول
    if st.session_state.user_role != "master":
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        
        st.error("⛔ النظام متوقف حالياً للصيانة أو بواسطة الإدارة العليا (Kill Switch Active).")
        st.info("لا يمكن لأي طالب أو مدير الوصول للنظام في الوقت الحالي.")
        st.write("---")
        
        # نموذج دخول مخصص للمالك الأعظم فقط لإلغاء القفل
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

# شاشة تسجيل الدخول العادية (عندما يكون النظام شغال)
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #1E88E5;'>🔐 تسجيل الدخول إلى نظام صوت المدرسة</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("اسم المستخدم (Username):")
        password = st.text_input("كلمة السر (Password):", type="password")
        login_btn = st.button("تسجيل الدخول 🚀", use_container_width=True)

        if login_btn:
            # حساب الطالب
            if username == "student" and password == "student123":
                st.session_state.logged_in = True
                st.session_state.user_role = "student"
                st.session_state.username = "طالب / ولي أمر"
                st.success("تم تسجيل الدخول بنجاح كـ طالب!")
                st.rerun()
            # حساب المدير
            elif username == "admin" and password == "Dr.RagabBV842":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "المدير (Dr. Ragab)"
                st.success("تم تسجيل الدخول بنجاح كـ مدير!")
                st.rerun()
            # حساب المالك الأعظم (Master Oody)
            elif username == "oody" and password == "Mahmoud@2011":
                st.session_state.logged_in = True
                st.session_state.user_role = "master"
                st.session_state.username = "Master Oody 👑"
                st.success("أهلاً بك يا ماستر أودي 👑!")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة!")
    st.stop()

# ---------------------------------------------------------
# 3. القائمة الجانبية للتنقل
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
    available_pages = [
        "🏠 الصفحة الرئيسية والتقديم", 
        "🔔 متابعة مشكلة برقم البلاغ",
        "🏆 ماذا تغير؟ (What Changed?)"
    ]
elif st.session_state.user_role == "admin":
    available_pages = [
        "👨‍💼 لوحة تحكم المدير (Dashboard)",
        "🏆 ماذا تغير؟ (What Changed?)"
    ]
elif st.session_state.user_role == "master":
    available_pages = ["⚡ Kill Switch Control Panel"]

page = st.sidebar.radio("اختر الصفحة:", available_pages)

# ---------------------------------------------------------
# 4. صفحات الطلاب (Student Views)
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
            location = st.text_input("مكان المشكلة 📍 (مثلاً: الفصل، الملعب، الكانتين)")
            priority = st.selectbox("درجة الأهمية ⚠️", ["عادية", "مهمة", "عاجلة"])
            
            anonymous = st.checkbox("🕶️ إخفاء الاسم (Anonymous Mode)")
            student_name = "مجهول"
            if not anonymous:
                student_name = st.text_input("اسمك (اختياري)", value="طالب/ولي أمر")

            submitted = st.form_submit_button("إرسال البلاغ 🚀")

            if submitted:
                if not title or not description:
                    st.error("يرجى ملء عنوان وشرح المشكلة!")
                else:
                    df = load_data()
                    ticket_id = f"TCK-{random.randint(1000, 9999)}"
                    new_row = {
                        "ticket_id": ticket_id,
                        "title": title,
                        "description": description,
                        "location": location,
                        "priority": priority,
                        "is_anonymous": "نعم" if anonymous else "لا",
                        "student_name": student_name,
                        "upvotes": 1,
                        "status": "New",
                        "admin_reply": ""
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success(f"تم إرسال بلاغك بنجاح! 🎉 رقم المتابعة الخاص بك هو: **{ticket_id}**")

    with col2:
        st.subheader("🔥 المشاكل الأكثر دعماً")
        df = load_data()
        if not df.empty:
            sorted_df = df.sort_values(by="upvotes", ascending=False)
            for idx, row in sorted_df.head(5).iterrows():
                with st.container():
                    st.markdown(f"**{row['title']}** ({row['priority']})")
                    st.caption(f"📍 المكان: {row['location']} | الحالة: `{row['status']}`")
                    c1, c2 = st.columns([1, 1])
                    c1.write(f"🔥 {row['upvotes']} دعم")
                    if c2.button("دعم 👍", key=f"upvote_{row['ticket_id']}"):
                        df.loc[df['ticket_id'] == row['ticket_id'], 'upvotes'] += 1
                        save_data(df)
                        st.rerun()
                    st.divider()
        else:
            st.info("لا توجد مشاكل مسجلة حالياً.")

elif page == "🔔 متابعة مشكلة برقم البلاغ":
    st.title("🔔 متابعة حالة البلاغ")
    search_id = st.text_input("أدخل رقم البلاغ (مثال: TCK-1001):")

    if search_id:
        df = load_data()
        if not df.empty:
            issue = df[df['ticket_id'].astype(str).str.upper() == search_id.strip().upper()]

            if not issue.empty:
                row = issue.iloc[0]
                st.subheader(f"📌 المشكلة: {row['title']}")
                st.write(f"**الوصف:** {row['description']}")
                st.write(f"**المكان:** {row['location']}")
                
                status = row['status']
                st.markdown("### 📊 مسار حالة الطلب:")
                
                s1 = "✅" if status in ["New", "Reviewing", "In Progress", "Solved"] else "⚪"
                s2 = "👀" if status in ["Reviewing", "In Progress", "Solved"] else "⚪"
                s3 = "🔧" if status in ["In Progress", "Solved"] else "⚪"
                s4 = "🎉" if status == "Solved" else "⚪"

                st.write(f"{s1} **تم الاستلام**")
                st.write("↓")
                st.write(f"{s2} **الإدارة بتراجعها (Reviewing)**")
                st.write("↓")
                st.write(f"{s3} **جاري الحل (In Progress)**")
                st.write("↓")
                st.write(f"{s4} **تم الحل (Solved)**")

                if pd.notna(row['admin_reply']) and str(row['admin_reply']).strip() != "":
                    st.info(f"💬 **رد المدير/الإدارة:** {row['admin_reply']}")
            else:
                st.error("رقم البلاغ غير موجود، اتأكد من الكود صح!")
        else:
            st.error("لا توجد بلاغات بالسيستم حتى الآن.")

# ---------------------------------------------------------
# 5. صفحة الإنجازات (What Changed)
# ---------------------------------------------------------
elif page == "🏆 ماذا تغير؟ (What Changed?)":
    st.title("🏆 What Changed?")
    st.write("صفحة تعرض للطلاب الإنجازات والتغييرات الحقيقية في المدرسة!")

    df = load_data()
    solved_count = len(df[df['status'] == 'Solved']) if not df.empty else 0
    total_upvotes = int(df['upvotes'].sum()) if not df.empty else 0
    
    st.markdown("### 🎉 الإحصائيات الحالية الحقيقية:")
    m1, m2, m3 = st.columns(3)
    m1.metric("تم إصلاحها", f"{solved_count} مشكلة ✅")
    m2.metric("تم تنفيذها", "0 اقتراحات 💡")
    m3.metric("المشاركين / الأصوات", f"{total_upvotes} طالب 👥")

    st.write("---")

# ---------------------------------------------------------
# 6. لوحة تحكم المدير (Dashboard)
# ---------------------------------------------------------
elif page == "👨‍💼 لوحة تحكم المدير (Dashboard)":
    st.title("👨‍💼 لوحة تحكم المدير (Dashboard)")
    
    df = load_data()
    if not df.empty:
        sorted_df = df.sort_values(by="upvotes", ascending=False)

        st.subheader("📋 قائمة الطلبات والمشاكل (مرتبة حسب الأعلى دعماً)")

        status_map = {
            "New": "جديد",
            "Reviewing": "قيد المراجعة",
            "In Progress": "قيد الحل",
            "Solved": "تم الحل"
        }

        display_df = sorted_df[["status", "upvotes", "title", "ticket_id"]].copy()
        display_df['status'] = display_df['status'].map(status_map)
        display_df.columns = ["الحالة", "الدعم 🔥", "المشكلة", "رقم البلاغ"]
        
        st.dataframe(display_df, use_container_width=True)

        st.write("---")
        st.subheader("🛠️ إدارة وتحديث حالة مشكلة")

        ticket_ids = sorted_df['ticket_id'].tolist()
        selected_ticket = st.selectbox("اختر رقم البلاغ للتعديل:", ticket_ids)

        if selected_ticket:
            current_row = df[df['ticket_id'] == selected_ticket].iloc[0]
            
            st.write(f"**المشكلة:** {current_row['title']} | **شرح:** {current_row['description']}")
            
            new_status = st.selectbox(
                "تغيير الحالة:", 
                ["New", "Reviewing", "In Progress", "Solved"],
                index=["New", "Reviewing", "In Progress", "Solved"].index(current_row['status'])
            )

            initial_reply = str(current_row['admin_reply']) if pd.notna(current_row['admin_reply']) else ""
            admin_reply = st.text_input("رد المدير للطالب (سيظهر للطالب عند المتابعة):", value=initial_reply)

            if st.button("حفظ التغييرات 💾"):
                df.loc[df['ticket_id'] == selected_ticket, 'status'] = new_status
                df.loc[df['ticket_id'] == selected_ticket, 'admin_reply'] = admin_reply
                save_data(df)
                st.success("تم تحديث حالة المشكلة بنجاح!")
                st.rerun()
    else:
        st.info("لا توجد بلاغات مسجلة حتى الآن لتعديلها.")

# ---------------------------------------------------------
# 7. لوحة تحكم ماستر أودي (Master Oody & Kill Switch)
# ---------------------------------------------------------
elif page == "⚡ Kill Switch Control Panel":
    st.title("👑 لوحة تحكم الماستر - أودي")
    st.write("أهلاً بك يا أودي! من هنا يمكنك التحكم الكامل في حالة عمل الموقع للجميع.")

    is_locked = is_system_locked()

    st.subheader("⚠️ وضع زر القتل (Kill Switch Status)")
    if is_locked:
        st.error("🔴 النظام حالياً: مُغلق بالكامل على الطلاب والمدير (OFFLINE).")
        if st.button("🟢 إيقاف زر القتل وتشغيل الويبسايت الآن (Enable System)"):
            set_system_lock(False)
            st.success("تم إعادة تشغيل الويبسايت للجميع بنجاح!")
            st.rerun()
    else:
        st.success("🟢 النظام حالياً: يعمل بشكل طبيعي للجميع (ONLINE).")
        if st.button("🔴 تفعيل الـ Kill Switch وإيقاف الويبسايت بالكامل (Shutdown System)"):
            set_system_lock(True)
            st.warning("تم إيقاف الويبسايت بالكامل ومنع الجميع من الدخول!")
            st.rerun()

    st.write("---")
    st.subheader("🗑️ خيار إعادة التصفير الشامل للبيانات")
    if st.button("⚠️ تصفير جميع البلاغات والإحصائيات نهائياً (Reset All Data)"):
        reset_database()
        st.success("تم تصفير كل البيانات والبلاغات بالكامل بنجاح!")
        st.rerun()