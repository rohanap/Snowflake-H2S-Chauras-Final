"""
Shared email dispatch helpers for Insurance 360.
Both Customer 360 and NBA Dashboard import from here.
Sends 2 HTML emails: internal team (full details) + customer (AI script only).
"""


def _send_email(session, recipients: str, subject: str, body: str,
                mime_type: str = "text/html") -> None:
    safe_subject = subject.replace("'", "\\'")
    safe_body = body.replace("'", "\\'")
    if mime_type == "text/plain":
        safe_body = safe_body.replace("\n", "\\n")
    sql = (
        f"CALL SYSTEM$SEND_EMAIL("
        f"'C360_EMAIL_NOTIFY', "
        f"'{recipients}', "
        f"'{safe_subject}', "
        f"'{safe_body}', "
        f"'{mime_type}'"
        f")"
    )
    session.sql(sql).collect()


_LABEL = ("font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:600;"
          "color:#8a8a9a;text-transform:uppercase;letter-spacing:1px;"
          "padding:7px 14px 4px 14px")
_VALUE = ("font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;"
          "color:#1a1a2e;padding:0 14px 10px 14px")


def _kv_row(label: str, value, bg: str = "#ffffff") -> str:
    return (
        f'<tr style="background-color:{bg}">'
        f'<td style="{_LABEL}">{label}</td></tr>'
        f'<tr style="background-color:{bg}">'
        f'<td style="{_VALUE}">{value}</td></tr>'
    )


def _build_internal_html(r: dict, script_body: str) -> str:
    churn_score = round(float(r['CHURN_RISK_SCORE']) * 100, 1)
    upsell = round(float(r['UPSELL_PROBABILITY'] or 0) * 100)
    avg_sent = float(r['AVG_SENTIMENT_SCORE'] or 0)
    pri_color = "#d32f2f" if r['NBA_PRIORITY'] == "Urgent" else (
        "#e65100" if r['NBA_PRIORITY'] == "High" else (
        "#f9a825" if r['NBA_PRIORITY'] == "Medium" else "#4caf50"))
    risk_color = "#d32f2f" if r['CHURN_RISK_LABEL'] == "High" else (
        "#f9a825" if r['CHURN_RISK_LABEL'] == "Medium" else "#4caf50")

    def _metric(label: str, value, color: str = "#1a1a2e") -> str:
        return (
            '<td align="center" style="padding:12px 6px">'
            f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:22px;'
            f'font-weight:800;color:{color};letter-spacing:-0.5px">{value}</div>'
            f'<div style="font-family:Arial,Helvetica,sans-serif;font-size:10px;'
            f'font-weight:600;color:#8a8a9a;text-transform:uppercase;'
            f'letter-spacing:0.8px;margin-top:4px">{label}</div></td>'
        )

    def _signal_row(label: str, value, alert: bool = False) -> str:
        vc = "#d32f2f" if alert else "#1a1a2e"
        return (
            f'<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:12px;'
            f'color:#666;padding:6px 16px;border-bottom:1px solid #f0f0f0">{label}</td>'
            f'<td align="right" style="font-family:Arial,Helvetica,sans-serif;'
            f'font-size:13px;font-weight:700;color:{vc};padding:6px 16px;'
            f'border-bottom:1px solid #f0f0f0">{value}</td></tr>'
        )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#eeeef2;font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eeeef2">
<tr><td align="center" style="padding:28px 10px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0"
       style="background-color:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 2px 16px rgba(0,0,0,0.06)">

  <!-- ===== HEADER ===== -->
  <tr>
    <td style="background-color:#1a1a2e;padding:24px 32px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.4px;
                     font-family:Arial,Helvetica,sans-serif">
            Insurance 360</td>
          <td align="right">
            <span style="display:inline-block;background-color:{pri_color};color:#fff;
                         font-size:11px;font-weight:700;padding:5px 14px;border-radius:20px;
                         text-transform:uppercase;letter-spacing:1px;
                         font-family:Arial,Helvetica,sans-serif">
              {r['NBA_PRIORITY']} Priority</span></td>
        </tr>
      </table>
    </td>
  </tr>
  <tr><td style="background:linear-gradient(90deg,#f7c948,#f5b731);height:4px;
                 font-size:0;line-height:0">&nbsp;</td></tr>

  <!-- ===== INTERNAL TAG ===== -->
  <tr>
    <td style="padding:20px 32px 0 32px">
      <table role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td style="background-color:#fff3e0;border:1px solid #ffe0b2;border-radius:6px;
                     padding:6px 14px;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                     font-weight:700;color:#e65100;text-transform:uppercase;letter-spacing:1.2px">
            Internal Team Copy &mdash; Do Not Forward to Customer</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ===== CUSTOMER IDENTITY ===== -->
  <tr>
    <td style="padding:24px 32px 0 32px">
      <p style="margin:0 0 2px 0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                font-weight:600;color:#8a8a9a;text-transform:uppercase;letter-spacing:1.2px">
        Customer Profile</p>
      <p style="margin:0 0 4px 0;font-family:Arial,Helvetica,sans-serif;font-size:26px;
                font-weight:900;color:#1a1a2e;letter-spacing:-0.8px">{r['NAME']}</p>
      <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:13px;
                color:#666">{r['CUSTOMER_ID']} &bull; {r['CITY']}, {r['STATE']}
                &bull; {r['SEGMENT']}</p>
    </td>
  </tr>

  <!-- ===== KEY METRICS ROW ===== -->
  <tr>
    <td style="padding:20px 32px 0 32px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background-color:#f7f7fa;border-radius:10px;border:1px solid #e8e8ee">
        <tr>
          {_metric("Churn Risk", f"{churn_score}%", risk_color)}
          {_metric("Upsell", f"{upsell}%")}
          {_metric("LTV", f"&#8377;{r['LIFETIME_VALUE']:,.0f}")}
          {_metric("Sentiment", f"{avg_sent:+.2f}",
                   "#d32f2f" if avg_sent < -0.3 else "#1a1a2e")}
        </tr>
      </table>
    </td>
  </tr>

  <!-- ===== CUSTOMER DETAILS TABLE ===== -->
  <tr>
    <td style="padding:22px 32px 0 32px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #e8e8ee;border-radius:8px;overflow:hidden">
        {_kv_row("Email", r.get('EMAIL', 'N/A'), "#f9f9fc")}
        {_kv_row("Income Band", r['INCOME_BAND'])}
        {_kv_row("Age", f"{r['AGE']} ({r['AGE_GROUP']})", "#f9f9fc")}
        {_kv_row("Tenure", f"{int(r['TENURE_DAYS'])} days")}
        {_kv_row("Customer Since", str(r['CUSTOMER_SINCE'])[:10], "#f9f9fc")}
        {_kv_row("Primary Channel", r['PRIMARY_CHANNEL'])}
      </table>
    </td>
  </tr>

  <!-- ===== SIGNAL BREAKDOWN ===== -->
  <tr>
    <td style="padding:22px 32px 0 32px">
      <p style="margin:0 0 10px 0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                font-weight:700;color:#8a8a9a;text-transform:uppercase;letter-spacing:1.2px">
        Signal Decomposition</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #e8e8ee;border-radius:8px;overflow:hidden">
        {_signal_row("Active Policies",
                     f"{int(r['ACTIVE_POLICY_COUNT'])} ({int(r['ACTIVE_POLICY_TYPE_COUNT'])} types)")}
        {_signal_row("Total Premium", f"&#8377;{float(r['TOTAL_ACTIVE_PREMIUM']):,.0f}")}
        {_signal_row("Lapsed / Cancelled", int(r['LAPSED_CANCELLED_COUNT']),
                     int(r['LAPSED_CANCELLED_COUNT']) > 0)}
        {_signal_row("Total Claims",
                     f"{int(r['TOTAL_CLAIMS'])} (Open: {int(r['OPEN_CLAIMS'])})",
                     int(r['OPEN_CLAIMS']) > 0)}
        {_signal_row("Failed Payments", int(r['FAILED_PAYMENT_COUNT']),
                     int(r['FAILED_PAYMENT_COUNT']) > 0)}
        {_signal_row("Complaints", int(r['COMPLAINT_COUNT']),
                     int(r['COMPLAINT_COUNT']) > 0)}
        {_signal_row("Avg Sentiment", f"{avg_sent:+.3f}", avg_sent < -0.3)}
      </table>
    </td>
  </tr>

  <!-- ===== NBA ACTION CARD ===== -->
  <tr>
    <td style="padding:22px 32px 0 32px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background-color:#fffde7;border:2px solid #1a1a2e;border-radius:10px;
                    overflow:hidden">
        <tr>
          <td style="background-color:#1a1a2e;padding:12px 20px">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                           font-weight:700;color:#f7c948;text-transform:uppercase;
                           letter-spacing:1.5px">Next Best Action</td>
                <td align="right" style="font-family:Arial,Helvetica,sans-serif;
                                         font-size:11px;font-weight:600;color:#a0a0c0;
                                         letter-spacing:1px;text-transform:uppercase">
                  {r['NBA_CHANNEL']}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:18px 20px">
            <p style="margin:0 0 6px 0;font-family:Arial,Helvetica,sans-serif;font-size:20px;
                      font-weight:900;color:#1a1a2e;letter-spacing:-0.5px">
              {r['NBA_ACTION']}</p>
            <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;
                      color:#555;line-height:1.5">{r['NBA_REASON']}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ===== AI SCRIPT PREVIEW ===== -->
  <tr>
    <td style="padding:22px 32px 0 32px">
      <p style="margin:0 0 10px 0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                font-weight:700;color:#8a8a9a;text-transform:uppercase;letter-spacing:1.2px">
        AI-Generated Script &mdash; Sent to Customer</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background-color:#f5f5f0;border-left:4px solid #f7c948;border-radius:8px">
        <tr>
          <td style="padding:20px 24px">
            <p style="margin:0;font-family:Georgia,Times,serif;font-size:15px;
                      line-height:1.75;color:#2c2c2c;font-style:italic">
              {script_body}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ===== FOOTER ===== -->
  <tr>
    <td style="padding:28px 32px 24px 32px;border-top:1px solid #e8e8ee;margin-top:20px">
      <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                color:#aaa;letter-spacing:0.4px">
        Insurance 360 &bull; Dispatched from NBA Dashboard
        &bull; Powered by Snowflake Cortex</p>
    </td>
  </tr>

</table>
</td></tr></table>
</body>
</html>"""


def _build_customer_html(customer_row: dict, script_body: str) -> str:
    first_name = customer_row['NAME'].split()[0]
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4">
<tr><td align="center" style="padding:30px 10px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0"
       style="background-color:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 4px 24px rgba(0,0,0,0.08)">

  <!-- Header bar -->
  <tr>
    <td style="background-color:#1a1a2e;padding:28px 40px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-family:Arial,Helvetica,sans-serif;font-size:22px;
                     font-weight:700;color:#ffffff;letter-spacing:-0.5px">
            Insurance 360
          </td>
          <td align="right" style="font-family:Arial,Helvetica,sans-serif;
                                   font-size:11px;font-weight:600;color:#a0a0c0;
                                   letter-spacing:1.5px;text-transform:uppercase">
            Personalized for you
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Accent stripe -->
  <tr><td style="background:linear-gradient(90deg,#f7c948 0%,#f5b731 100%);height:4px;font-size:0;line-height:0">&nbsp;</td></tr>

  <!-- Greeting -->
  <tr>
    <td style="padding:36px 40px 0 40px">
      <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:15px;
                color:#666;font-weight:600;text-transform:uppercase;letter-spacing:1.2px">
        Hello, {first_name}
      </p>
    </td>
  </tr>

  <!-- AI message card -->
  <tr>
    <td style="padding:20px 40px 0 40px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background-color:#fafaf5;border-left:4px solid #f7c948;border-radius:8px">
        <tr>
          <td style="padding:24px 28px">
            <p style="margin:0;font-family:Georgia,Times,serif;font-size:17px;
                      line-height:1.7;color:#2c2c2c">
              {script_body}
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- CTA button -->
  <tr>
    <td align="center" style="padding:32px 40px 0 40px">
      <table role="presentation" cellpadding="0" cellspacing="0">
        <tr>
          <td style="background-color:#1a1a2e;border-radius:8px;padding:14px 36px">
            <span style="font-family:Arial,Helvetica,sans-serif;font-size:14px;
                         font-weight:700;color:#ffffff;text-transform:uppercase;
                         letter-spacing:1px">
              Contact Your Advisor
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Divider -->
  <tr>
    <td style="padding:32px 40px 0 40px">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="border-top:1px solid #e8e8e8;font-size:0;line-height:0">&nbsp;</td></tr>
      </table>
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:20px 40px 32px 40px">
      <p style="margin:0 0 8px 0;font-family:Arial,Helvetica,sans-serif;font-size:12px;
                color:#999;line-height:1.6">
        This message was generated by our AI advisor based on your profile.
        Your data is handled in accordance with our privacy policy.
      </p>
      <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                color:#bbb;letter-spacing:0.5px">
        Insurance 360 &bull; Powered by Snowflake Cortex
      </p>
    </td>
  </tr>

</table>
</td></tr></table>
</body>
</html>"""


def dispatch_emails(customer_row: dict, script_body: str, session) -> tuple:
    """Send two HTML emails: internal team (full details) + customer (AI script only).

    The caller MUST pass the Snowpark session it already holds (from
    ``data_loader.get_session()``).  Obtaining a session inside this module
    would create a second Snowpark Session when the module-reload guard in
    ``_reload.py`` has refreshed ``data_loader``, triggering Snowpark error 1409.
    """
    cust_name = customer_row['NAME']
    cust_id = customer_row['CUSTOMER_ID']

    # --- Email 1: Internal team — full details (rich HTML) ---
    internal_recipients = "nilesh.patil@merkle.com"
    internal_subject = (
        f"[Insurance 360 - Internal] NBA Dispatch: {customer_row['NBA_ACTION']} "
        f"// {cust_id} - {cust_name}"
    )
    internal_html = _build_internal_html(customer_row, script_body)
    _send_email(session, internal_recipients, internal_subject, internal_html,
                "text/html")

    # --- Email 2: Customer — rich HTML with AI script ---
    customer_email = str(customer_row.get('EMAIL') or '').strip()
    if not customer_email:
        return internal_recipients, "(no customer email on file)"

    customer_subject = "A message from your insurance advisor"
    customer_html = _build_customer_html(customer_row, script_body)
    _send_email(session, customer_email, customer_subject, customer_html,
                "text/html")

    return internal_recipients, customer_email
