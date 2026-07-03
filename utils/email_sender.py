"""
utils/email_sender.py — Welcome email sender for new CFA Assistant registrations.

Uses SMTP credentials from .env (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD).
Sends a bilingual (Vietnamese + English) welcome email to new users.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

logger = logging.getLogger(__name__)

# ── SMTP config from environment ────────────────────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Contact info shown in the email — update these in .env or here
SUPPORT_EMAIL = os.getenv("SMTP_USER", "hnamvu29@gmail.com")
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "+84 983 658 980")
TEAM_NAME     = os.getenv("TEAM_NAME", "CFA Assistant Team")


def _build_welcome_html(username: str) -> str:
    """Build the full bilingual HTML welcome email body."""
    return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chào mừng / Welcome</title>
<style>
  body {{ margin:0; padding:0; background:#0f172a; font-family: 'Segoe UI', Arial, sans-serif; }}
  .wrapper {{ max-width:620px; margin:0 auto; background:#1e293b; border-radius:12px;
              overflow:hidden; border:1px solid #334155; }}
  .header {{ background:linear-gradient(135deg,#6366f1,#06b6d4); padding:2.5rem 2rem;
             text-align:center; }}
  .header h1 {{ margin:0; color:#fff; font-size:1.6rem; font-weight:800; letter-spacing:-0.02em; }}
  .header p  {{ margin:0.5rem 0 0; color:rgba(255,255,255,0.85); font-size:0.95rem; }}
  .body {{ padding:2rem; }}
  .section {{ margin-bottom:1.8rem; }}
  .section h2 {{ font-size:1rem; font-weight:700; color:#818cf8; margin:0 0 0.6rem;
                 text-transform:uppercase; letter-spacing:0.06em; }}
  .section p  {{ margin:0 0 0.8rem; line-height:1.7; color:#cbd5e1; font-size:0.9rem; }}
  .feature {{ background:#0f172a; border-radius:8px; padding:1rem 1.2rem;
               margin-bottom:0.7rem; border-left:3px solid #6366f1; }}
  .feature .emoji {{ font-size:1.4rem; display:inline-block; margin-bottom:0.3rem; }}
  .feature .title {{ font-weight:700; color:#f1f5f9; font-size:0.92rem; margin-bottom:0.2rem; }}
  .feature .desc {{ color:#94a3b8; font-size:0.83rem; line-height:1.6; }}
  .feature.green  {{ border-left-color:#10b981; }}
  .feature.cyan   {{ border-left-color:#06b6d4; }}
  .feature.purple {{ border-left-color:#8b5cf6; }}
  .divider {{ border:none; border-top:1px solid #334155; margin:1.5rem 0; }}
  .contact {{ background:#0f172a; border-radius:8px; padding:1rem 1.2rem;
               color:#94a3b8; font-size:0.85rem; line-height:1.8; }}
  .contact a {{ color:#818cf8; text-decoration:none; }}
  .quote {{ background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(6,182,212,0.1));
             border:1px solid rgba(99,102,241,0.3); border-radius:10px;
             padding:1.2rem 1.5rem; text-align:center; margin:1.5rem 0; }}
  .quote p {{ margin:0; color:#f1f5f9; font-size:0.92rem; font-style:italic; line-height:1.6; }}
  .footer {{ background:#0f172a; padding:1.2rem 2rem; text-align:center;
              color:#475569; font-size:0.78rem; border-top:1px solid #1e293b; }}
  .footer strong {{ color:#64748b; }}
</style>
</head>
<body>
<div class="wrapper">

  <!-- Header -->
  <div class="header">
    <h1>📊 CFA Assistant</h1>
    <p>Chào mừng bạn đến với hành trình chinh phục CFA Level I! 🎯<br>
       Welcome to Your CFA Level I Success Journey! 🎯</p>
  </div>

  <!-- Body -->
  <div class="body">

    <!-- Section 1: Greeting -->
    <div class="section">
      <h2>1. Lời chào mừng · Welcome</h2>
      <p>
        Xin chào <strong style="color:#818cf8">{username}</strong>,<br>
        Cảm ơn bạn đã đăng ký cùng hệ thống học tập tích hợp AI của chúng tôi! Chúng tôi rất vui mừng
        được đồng hành cùng bạn trên chặng đường ôn luyện quan trọng này. Với sự kết hợp giữa công nghệ AI
        hiện đại và phương pháp học tập khoa học, chúng tôi tin rằng bạn sẽ có một hành trình ôn thi
        hiệu quả và tự tin hơn bao giờ hết.
      </p>
      <p>
        Hello <strong style="color:#06b6d4">{username}</strong>,<br>
        Thank you for registering for our CFA Level I course, powered by our integrated AI learning system!
        We're thrilled to accompany you on this important exam preparation journey. By combining cutting-edge
        AI technology with proven learning science, we're confident you'll experience a more effective and
        confident path to exam success.
      </p>
    </div>

    <hr class="divider">

    <!-- Section 2: Features -->
    <div class="section">
      <h2>2. Những lợi ích bạn sẽ nhận được · Benefits</h2>
      <p style="color:#64748b; font-size:0.82rem;">
        Hệ thống của chúng tôi vận hành trên 3 công cụ cốt lõi · Our system runs on 3 core engines:
      </p>

      <div class="feature green">
        <div class="emoji">🎯</div>
        <div class="title">Luyện tập thích ứng · Adaptive Practice</div>
        <div class="desc">
          Ngân hàng câu hỏi được cá nhân hóa, tự động điều chỉnh độ khó và trọng tâm theo năng lực của bạn.
          Thuật toán xác định những chủ đề bạn còn yếu và cung cấp bộ câu hỏi nhắm đúng vào đó.<br>
          <em>Tailored question banks that automatically update difficulty based on your performance.
          The algorithm identifies your weakest subtopics and feeds you targeted problem sets.</em>
        </div>
      </div>

      <div class="feature cyan">
        <div class="emoji">🤖</div>
        <div class="title">Gia sư AI 24/7 · 24/7 AI Tutor</div>
        <div class="desc">
          Giải thích chuyên sâu cho toàn bộ 10 chủ đề CFA. Gia sư AI tích hợp trực tiếp với kết quả
          luyện tập của bạn, hiểu ngay tình trạng học tập và cung cấp công thức đúng trọng tâm bạn cần.<br>
          <em>Deep, conversational explanations across all 10 CFA topic areas. Integrated directly with your
          practice outcomes, delivering the exact formulas and explanations you need.</em>
        </div>
      </div>

      <div class="feature purple">
        <div class="emoji">📅</div>
        <div class="title">Lịch trình thông minh · Smart Scheduler</div>
        <div class="desc">
          Xóa bỏ nỗi lo lập kế hoạch học tập. Dựa trên nguyên lý lặp lại ngắt quãng Ebbinghaus, hệ
          thống tự động tính toán lại lịch ôn tập sau mỗi bài kiểm tra thử.<br>
          <em>Eliminate study-planning fatigue. Powered by Ebbinghaus spaced repetition, the engine
          recalculates your review schedule after every mock test.</em>
        </div>
      </div>
    </div>

    <hr class="divider">

    <!-- Section 3: Contact -->
    <div class="section">
      <h2>3. Thông tin liên hệ · Contact</h2>
      <p style="color:#94a3b8; font-size:0.85rem;">
        Nếu bạn cần hỗ trợ trong quá trình sử dụng hệ thống, vui lòng liên hệ:<br>
        If you need any support while using the system, please reach out:
      </p>
      <div class="contact">
        📧 Email: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a><br>
        📞 Điện thoại / Phone: {SUPPORT_PHONE}
      </div>
    </div>

    <!-- Quote -->
    <div class="quote">
      <p>
        "Chúng tôi tin ở bạn, bạn tin chúng tôi sẽ giúp bạn."<br>
        <span style="color:#94a3b8; font-size:0.85rem;">
          "We trust you, you trust us — together we'll help you succeed."
        </span>
      </p>
    </div>

    <p style="color:#94a3b8; font-size:0.88rem; text-align:center; margin:0;">
      Chúc bạn ôn tập hiệu quả và đạt kết quả như mong đợi!<br>
      <em>Wishing you an effective study journey and the results you deserve!</em><br><br>
      Trân trọng / Best regards,<br>
      <strong style="color:#818cf8">{TEAM_NAME}</strong>
    </p>

  </div><!-- /body -->

  <!-- Footer -->
  <div class="footer">
    <strong>CFA Learning Assistant</strong> · Empowered by Advanced AI<br>
    CFA Institute does not endorse, promote, or warrant the accuracy or quality of this product.
  </div>

</div>
</body>
</html>
"""


def send_welcome_email(to_email: str, username: str) -> tuple[bool, str]:
    """
    Send the bilingual welcome email to `to_email`.

    Returns:
        (success: bool, message: str)
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return False, "SMTP credentials not configured (SMTP_USER / SMTP_PASSWORD missing in .env)."

    subject_vi = "Chào mừng bạn đến với hành trình chinh phục CFA Level I! 🎯"
    subject_en = "Welcome to Your CFA Level I Success Journey! 🎯"
    subject    = f"{subject_vi} | {subject_en}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"CFA Assistant <{SMTP_USER}>"
    msg["To"]      = to_email

    # Plain-text fallback
    plain_text = (
        f"Xin chào / Hello {username},\n\n"
        f"Cảm ơn bạn đã đăng ký CFA Learning Assistant!\n"
        f"Thank you for registering with CFA Learning Assistant!\n\n"
        f"Liên hệ / Contact: {SUPPORT_EMAIL} | {SUPPORT_PHONE}\n\n"
        f"Trân trọng / Best regards,\n{TEAM_NAME}"
    )

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(_build_welcome_html(username), "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True, f"✅ Welcome email sent to {to_email}"
    except smtplib.SMTPAuthenticationError:
        logger.warning("SMTP auth failed — check SMTP_USER / SMTP_PASSWORD in .env")
        return False, "Email auth failed. Check SMTP credentials in .env."
    except smtplib.SMTPException as e:
        logger.warning(f"SMTP error: {e}")
        return False, f"Could not send email: {e}"
    except Exception as e:
        logger.warning(f"Email send error: {e}")
        return False, f"Email error: {e}"
