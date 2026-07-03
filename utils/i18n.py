"""
utils/i18n.py — Lightweight bilingual (EN / VI) translation helper.

Usage:
    from utils.i18n import t, get_lang, set_lang, render_lang_switcher
    st.write(t("dashboard"))
"""

import streamlit as st

# ── Translation dictionary ─────────────────────────────────────────────────────
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Nav / Auth
        "sign_in": "Sign In",
        "sign_up": "Sign Up",
        "logout": "Logout",
        "dashboard": "Dashboard",
        "cancel": "Cancel",
        "get_started": "🚀 Get Started Free",
        "enter_dashboard": "📈 Enter Study Dashboard",
        "access_portal": "Access your personalized learning portal",
        "start_journey": "Start your adaptive study journey free",
        "username": "Username",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "email_optional": "Email (optional)",
        "email_required": "Email (required)",
        "phone_optional": "Phone number (optional)",
        "email_label": "Email",
        "phone_label": "Phone Number",
        "welcome_email_sent_noti": "🎉 Account created! A welcome email containing study materials and details has been sent to {email}.",
        "cfa_level_focus": "CFA Level Focus",
        "create_account": "Create Account",
        "fill_both_fields": "Please fill in both fields.",
        "invalid_credentials": "Invalid username or password.",
        "password_min": "Password must be at least 6 characters.",
        "passwords_no_match": "Passwords do not match.",
        "username_taken": "Username already taken. Please choose another.",
        "username_required": "Username and password are required.",
        "enter_username": "Enter your username",
        "enter_password": "Enter your password",
        "min_6_chars": "Min 6 characters",

        # Landing page
        "hero_badge": "Next-Gen CFA Prep Platform",
        "hero_title": "CFA Level I Prep That Adapts to You",
        "hero_subtitle": "A unified study ecosystem that maps your weaknesses, builds dynamic schedules based on cognitive spaced repetition, and supports you 24/7 with an expert AI coach.",
        "features_title": "Three Engines. One Exam Pass.",
        "feat1_title": "1. Adaptive Practice",
        "feat1_desc": "Tailored question banks that automatically update difficulty and focus. The algorithm isolates your weakest subtopics and feeds you targeted problem sets to guarantee concept mastery.",
        "feat2_title": "2. 24/7 AI Tutor",
        "feat2_desc": "Deep conversational explanations of all 10 CFA topic areas. Integrated directly with your practice outcomes so it immediately understands your study state and provides targeted formulas.",
        "feat3_title": "3. Smart Scheduler",
        "feat3_desc": "Eliminate study-planning fatigue. Powered by Ebbinghaus spaced repetition, the engine recalculates review dates after each mock test, preparing you perfectly for exam day.",
        "inside_ecosystem": "Inside the Ecosystem",
        "footer_disclaimer": "Disclaimer: CFA Institute does not endorse, promote, or warrant the accuracy or quality of the products or services offered here.",

        # Dashboard
        "welcome_back": "Welcome back",
        "sessions_completed": "Sessions Completed",
        "overall_avg_score": "Overall Avg Score",
        "topics_need_focus": "Topics Need Focus",
        "scheduled_sessions": "Scheduled Sessions",
        "performance_radar": "🕸️ Performance Radar",
        "score_history": "📅 Score History",
        "score_by_topic": "📊 Score by Topic",
        "upcoming_sessions": "📆 Upcoming Sessions",
        "no_sessions_yet": "No sessions yet. Complete your first practice to see your progress!",
        "complete_to_see_scores": "Complete practice sessions to see scores.",
        "no_sessions_scheduled": "No sessions scheduled. Visit the **Schedule** page to generate your study plan.",
        "generate_study_plan": "🗓️ Generate Study Plan",
        "topics_needing_attention": "⚠️ Topics Needing Attention",
        "view_all_sessions": "→ View all sessions",
        "today": "🔥 Today",
        "tomorrow": "⏰ Tomorrow",
        "practice_now": "📚 Practice Now",
        "sessions": "sessions",
        "exam_weight": "exam weight",
        "last_studied": "Last studied",
        "never": "Never",
        "days_ago": "days ago",
        "priority_index": "Priority Index",
        "subtopic_breakdown": "Weakest Sub-topics",
        "questions_answered": "questions answered",
        "no_subtopic_data": "Complete more practice to unlock sub-topic breakdown.",
        "all_looking_good": "✅ All topics looking good! Keep up the great work.",

        # Sidebar
        "logged_in_as": "Logged in as",
        "avg_score": "Avg Score",
        "upcoming": "Upcoming",
        "reset_progress": "🔄 Reset All Progress",
        "reset_warning": "⚠️ This will permanently delete all your scores, sessions, chat history, and schedule. Your account will remain. This cannot be undone.",
        "yes_reset": "✅ Yes, Reset",
        "cancel_reset": "❌ Cancel",
        "all_progress_reset": "All progress has been reset.",
        "sidebar_logout": "🚪 Logout",
    },

    "vi": {
        # Nav / Auth
        "sign_in": "Đăng nhập",
        "sign_up": "Đăng ký",
        "logout": "Đăng xuất",
        "dashboard": "Bảng điều khiển",
        "cancel": "Hủy",
        "get_started": "🚀 Bắt đầu miễn phí",
        "enter_dashboard": "📈 Vào trang học tập",
        "access_portal": "Truy cập cổng học tập cá nhân của bạn",
        "start_journey": "Bắt đầu hành trình học thích ứng miễn phí",
        "username": "Tên đăng nhập",
        "password": "Mật khẩu",
        "confirm_password": "Xác nhận mật khẩu",
        "email_optional": "Email (tùy chọn)",
        "email_required": "Email (bắt buộc)",
        "phone_optional": "Số điện thoại (tùy chọn)",
        "email_label": "Email",
        "phone_label": "Số điện thoại",
        "welcome_email_sent_noti": "🎉 Đăng ký thành công! Một email chào mừng chứa tài liệu học tập và thông tin chi tiết đã được gửi tới {email}.",
        "cfa_level_focus": "Cấp độ CFA",
        "create_account": "Tạo tài khoản",
        "fill_both_fields": "Vui lòng điền đầy đủ cả hai trường.",
        "invalid_credentials": "Tên đăng nhập hoặc mật khẩu không đúng.",
        "password_min": "Mật khẩu phải có ít nhất 6 ký tự.",
        "passwords_no_match": "Mật khẩu xác nhận không khớp.",
        "username_taken": "Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.",
        "username_required": "Tên đăng nhập và mật khẩu là bắt buộc.",
        "enter_username": "Nhập tên đăng nhập",
        "enter_password": "Nhập mật khẩu",
        "min_6_chars": "Tối thiểu 6 ký tự",

        # Landing page
        "hero_badge": "Nền tảng ôn thi CFA thế hệ mới",
        "hero_title": "Ôn thi CFA Level I thích ứng với bạn",
        "hero_subtitle": "Hệ sinh thái học tập toàn diện giúp xác định điểm yếu, xây dựng lịch học động dựa trên lặp lại giãn cách, và hỗ trợ bạn 24/7 với AI gia sư chuyên nghiệp.",
        "features_title": "Ba công cụ. Một kỳ thi chinh phục.",
        "feat1_title": "1. Luyện tập thích ứng",
        "feat1_desc": "Ngân hàng câu hỏi được cá nhân hóa tự động cập nhật độ khó. Thuật toán xác định chủ đề yếu nhất và cung cấp bài tập mục tiêu để đảm bảo nắm vững kiến thức.",
        "feat2_title": "2. Gia sư AI 24/7",
        "feat2_desc": "Giải thích chuyên sâu tất cả 10 lĩnh vực CFA. Tích hợp trực tiếp với kết quả luyện tập của bạn để hiểu ngay trạng thái học tập và cung cấp công thức mục tiêu.",
        "feat3_title": "3. Lịch học thông minh",
        "feat3_desc": "Loại bỏ mệt mỏi khi lập kế hoạch học. Dựa trên lặp lại giãn cách Ebbinghaus, công cụ tái tính ngày ôn tập sau mỗi bài thi thử, chuẩn bị hoàn hảo cho ngày thi.",
        "inside_ecosystem": "Khám phá hệ sinh thái",
        "footer_disclaimer": "Tuyên bố miễn trách: CFA Institute không xác nhận, quảng bá hoặc bảo đảm chất lượng sản phẩm/dịch vụ được cung cấp ở đây.",

        # Dashboard
        "welcome_back": "Chào mừng trở lại",
        "sessions_completed": "Buổi học hoàn thành",
        "overall_avg_score": "Điểm trung bình",
        "topics_need_focus": "Chủ đề cần chú ý",
        "scheduled_sessions": "Buổi học đã lên lịch",
        "performance_radar": "🕸️ Biểu đồ Radar",
        "score_history": "📅 Lịch sử điểm số",
        "score_by_topic": "📊 Điểm theo chủ đề",
        "upcoming_sessions": "📆 Buổi học sắp tới",
        "no_sessions_yet": "Chưa có buổi học nào. Hoàn thành buổi luyện tập đầu tiên để xem tiến trình!",
        "complete_to_see_scores": "Hoàn thành buổi luyện tập để xem điểm số.",
        "no_sessions_scheduled": "Chưa có lịch học nào. Truy cập trang **Lịch học** để tạo kế hoạch ôn tập.",
        "generate_study_plan": "🗓️ Tạo kế hoạch học",
        "topics_needing_attention": "⚠️ Chủ đề cần cải thiện",
        "view_all_sessions": "→ Xem tất cả buổi học",
        "today": "🔥 Hôm nay",
        "tomorrow": "⏰ Ngày mai",
        "practice_now": "📚 Luyện tập ngay",
        "sessions": "buổi học",
        "exam_weight": "trọng số thi",
        "last_studied": "Học lần cuối",
        "never": "Chưa học",
        "days_ago": "ngày trước",
        "priority_index": "Chỉ số ưu tiên",
        "subtopic_breakdown": "Chủ đề phụ yếu nhất",
        "questions_answered": "câu hỏi đã trả lời",
        "no_subtopic_data": "Hoàn thành thêm bài luyện tập để xem phân tích chủ đề phụ.",
        "all_looking_good": "✅ Tất cả chủ đề đều tốt! Tiếp tục phát huy nhé.",

        # Sidebar
        "logged_in_as": "Đăng nhập với tư cách",
        "avg_score": "Điểm TB",
        "upcoming": "Sắp tới",
        "reset_progress": "🔄 Đặt lại toàn bộ tiến trình",
        "reset_warning": "⚠️ Thao tác này sẽ xóa vĩnh viễn toàn bộ điểm số, buổi học, lịch sử chat và lịch học. Tài khoản của bạn sẽ được giữ lại. Không thể hoàn tác.",
        "yes_reset": "✅ Có, đặt lại",
        "cancel_reset": "❌ Hủy",
        "all_progress_reset": "Toàn bộ tiến trình đã được đặt lại.",
        "sidebar_logout": "🚪 Đăng xuất",
    },
}


def get_lang() -> str:
    """Return current language code ('en' or 'vi')."""
    return st.session_state.get("lang", "en")


def set_lang(lang: str) -> None:
    """Set the current language in session state."""
    st.session_state["lang"] = lang


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.
    Falls back to English, then to the key itself if not found.
    Supports simple string formatting: t("hello", name="World") if value contains {name}.
    """
    lang = get_lang()
    value = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key) or key
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return value


def render_lang_switcher() -> None:
    """
    Render a compact EN 🇬🇧 / VI 🇻🇳 language toggle using Streamlit columns.
    Active language button is styled as primary, inactive as secondary.
    Must be called inside a column or container.
    """
    lang = get_lang()
    col_en, col_vi = st.columns(2)
    with col_en:
        btn_type_en = "primary" if lang == "en" else "secondary"
        if st.button("🇬🇧 EN", key="lang_en", use_container_width=True, type=btn_type_en):
            set_lang("en")
            st.rerun()
    with col_vi:
        btn_type_vi = "primary" if lang == "vi" else "secondary"
        if st.button("🇻🇳 VI", key="lang_vi", use_container_width=True, type=btn_type_vi):
            set_lang("vi")
            st.rerun()
