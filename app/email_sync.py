import re
import os
import email
import imaplib
from email.header import decode_header
from datetime import datetime
import tracker
from chain import Chain

def decode_mime_header(header_value: str | None) -> str:
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(encoding or "utf-8", errors="ignore"))
            except Exception:
                result.append(part.decode("latin1", errors="ignore"))
        else:
            result.append(str(part))
    return "".join(result).strip()

def clean_reply_body(raw_text_or_html: str) -> str:
    """
    Cleans incoming email text by stripping out historical quoted reply chains,
    email headers, and standard email signatures.
    """
    if not raw_text_or_html:
        return ""
    
    text = raw_text_or_html

    # Strip HTML tags if HTML is present
    if "<html" in text.lower() or "<div" in text.lower() or "<p" in text.lower():
        text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)

    lines = text.splitlines()
    cleaned_lines = []
    
    # Common quote break patterns
    quote_break_patterns = [
        r'^\s*-{2,}\s*Original Message\s*-{2,}',
        r'^\s*On\s+.*?wrote:\s*$',
        r'^\s*From:\s+.*?\s+Sent:\s+',
        r'^\s*_{10,}',
        r'^\s*Begin forwarded message:',
    ]

    for line in lines:
        stripped = line.strip()
        
        # Check for quote break triggers
        if any(re.search(pat, stripped, re.IGNORECASE) for pat in quote_break_patterns):
            break

        # Check for lines starting with >
        if stripped.startswith(">"):
            continue

        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines).strip()
    
    # Normalize multiple whitespace/newlines
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text if cleaned_text else raw_text_or_html.strip()

def extract_email_address(header_val: str) -> str:
    if not header_val:
        return ""
    match = re.search(r'<([^>]+)>', header_val)
    if match:
        return match.group(1).strip().lower()
    match2 = re.search(r'[\w\.-]+@[\w\.-]+', header_val)
    if match2:
        return match2.group(0).strip().lower()
    return header_val.strip().lower()

def parse_mime_message(raw_bytes: bytes) -> dict:
    """
    Parses raw RFC822 bytes into a structured dictionary of headers and text body.
    """
    msg = email.message_from_bytes(raw_bytes)

    subject = decode_mime_header(msg.get("Subject", ""))
    sender = decode_mime_header(msg.get("From", ""))
    recipient = decode_mime_header(msg.get("To", ""))
    message_id = decode_mime_header(msg.get("Message-ID", ""))
    in_reply_to = decode_mime_header(msg.get("In-Reply-To", ""))
    references = decode_mime_header(msg.get("References", ""))
    thread_id = decode_mime_header(msg.get("X-GM-THRID", "") or msg.get("Thread-Topic", "") or msg.get("Thread-Index", ""))
    date_str = decode_mime_header(msg.get("Date", ""))

    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition", ""))
            if "attachment" not in content_disp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        decoded_body = payload.decode(charset, errors="ignore")
                    except Exception:
                        decoded_body = payload.decode("latin1", errors="ignore")

                    if content_type == "text/plain":
                        body_text = decoded_body
                        break
                    elif content_type == "text/html" and not body_text:
                        body_text = decoded_body
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                body_text = payload.decode(charset, errors="ignore")
            except Exception:
                body_text = payload.decode("latin1", errors="ignore")

    return {
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,
        "thread_id": thread_id,
        "sender": extract_email_address(sender),
        "sender_raw": sender,
        "recipient": extract_email_address(recipient),
        "subject": subject,
        "body_text": body_text,
        "date_str": date_str
    }

def rule_based_fallback_analysis(reply_text: str, job_context: dict | None = None) -> dict:
    """
    Heuristic rule-based entity extractor and classifier used when LLM is offline or uninitialized.
    """
    ctx = job_context or {}
    role = ctx.get("role", "Application")
    company = ctx.get("company", "Company")
    lower = reply_text.lower()

    # Link extraction
    links = re.findall(r'https?://[^\s<>"]+(?:zoom\.us|meet\.google\.com|teams\.microsoft\.com|calendly\.com)[^\s<>"]*', reply_text)
    meeting_link = links[0] if links else ""
    if not meeting_link:
        all_links = re.findall(r'https?://[^\s<>"\']+', reply_text)
        meeting_link = all_links[0] if all_links else ""

    # Date extraction heuristic
    date_match = re.search(r'(?:on\s+)?(?:(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]+)?(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{4})?', reply_text, re.IGNORECASE)
    interview_date = date_match.group(0).strip() if date_match else ""

    # Time extraction
    time_match = re.search(r'\b\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\s*(?:[A-Z]{3,4}|GMT|UTC)?\b', reply_text)
    interview_time = time_match.group(0).strip() if time_match else ""

    # Category classification
    if any(k in lower for k in ["interview", "invitation", "schedule a call", "speak with", "chat with you", "video call"]):
        cat = "Interview Invitation"
        status = "Interview Scheduled"
        action = f"Confirm availability and prepare for interview with {company}."
    elif any(k in lower for k in ["assessment", "coding test", "take-home", "hackerrank", "codility"]):
        cat = "Assessment / Test Invitation"
        status = "Assessment / Test"
        action = "Complete the technical assessment before the requested deadline."
    elif any(k in lower for k in ["offer", "pleased to offer", "formal offer", "compensation"]):
        cat = "Offer"
        status = "Offer"
        action = f"Review offer terms from {company} and reply with your decision."
    elif any(k in lower for k in ["unfortunately", "not moving forward", "other candidates", "regret to inform", "declined"]):
        cat = "Rejection"
        status = "Rejected"
        action = "Application closed by company. Update job search pipeline."
    elif any(k in lower for k in ["under review", "reviewing your application", "received your application"]):
        cat = "Application Under Review"
        status = "Under Review"
        action = "No immediate action needed. Application is actively being evaluated."
    else:
        cat = "General Company Response"
        status = "Reply Received"
        action = "Review incoming message from recruiter and follow up accordingly."

    return {
        "category": cat,
        "confidence_level": "MEDIUM",
        "interview_date": interview_date,
        "interview_time": interview_time,
        "interview_type": "Video Call" if "meet" in meeting_link or "zoom" in meeting_link else "Direct Communication",
        "meeting_link": meeting_link,
        "location": "Remote",
        "recruiter_contact": "",
        "requested_documents": "",
        "deadline": "",
        "required_action": action,
        "important_notes": f"Detected reply regarding {role} at {company}.",
        "suggested_pipeline_status": status
    }

def process_single_incoming_email(user_id: int, email_data: dict, chain_instance: Chain | None = None) -> dict:
    """
    Core deterministic reply processing engine:
    1. Idempotency check: Skip already processed message IDs.
    2. Deterministic matching against sent applications.
    3. Save incoming record.
    4. Clean reply text.
    5. AI classification & entity extraction.
    6. Update application status and database records.
    """
    message_id = email_data.get("message_id") or f"<msg_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}@mail.local>"
    
    # 1. Idempotency Check
    if tracker.is_reply_already_processed(message_id):
        return {
            "status": "SKIPPED_ALREADY_PROCESSED",
            "message_id": message_id,
            "matched": False
        }

    in_reply_to = email_data.get("in_reply_to", "")
    references = email_data.get("references", "")
    thread_id = email_data.get("thread_id", "")
    sender_email = email_data.get("sender", "")
    recipient_email = email_data.get("recipient", "")
    subject = email_data.get("subject", "")
    body_text = email_data.get("body_text", "")
    received_at = email_data.get("date_str")

    # 2. Deterministic Matching
    matched_app, confidence = tracker.find_application_by_headers_or_subject(
        user_id=user_id,
        thread_id=thread_id,
        in_reply_to=in_reply_to,
        references_hdr=references,
        subject=subject,
        sender_email=sender_email
    )

    cleaned_body = clean_reply_body(body_text)
    app_id = matched_app["id"] if matched_app else None

    # 3. Save incoming message
    tracker.record_incoming_reply(
        app_id=app_id,
        user_id=user_id,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references_hdr=references,
        thread_id=thread_id,
        sender_email=sender_email,
        recipient_email=recipient_email,
        subject=subject,
        body_text=body_text,
        cleaned_body=cleaned_body,
        confidence=confidence,
        received_at=received_at
    )

    # 4. AI Analysis & Pipeline Update (if matched)
    analysis = None
    if matched_app:
        job_context = {
            "role": matched_app.get("role", "Target Role"),
            "company": matched_app.get("company", "Target Company")
        }
        if chain_instance is not None:
            try:
                analysis = chain_instance.analyze_reply(
                    reply_text=cleaned_body or body_text,
                    original_job_context=job_context
                )
            except Exception as e:
                analysis = rule_based_fallback_analysis(cleaned_body or body_text, job_context)
        else:
            analysis = rule_based_fallback_analysis(cleaned_body or body_text, job_context)

        if analysis:
            # Save structured analysis
            tracker.save_reply_analysis(app_id=app_id, message_id=message_id, analysis=analysis)

            # Update application status
            suggested_status = analysis.get("suggested_pipeline_status", "Reply Received")
            interview_date = analysis.get("interview_date", "")
            meeting_link = analysis.get("meeting_link", "")
            action = analysis.get("required_action", "")
            existing_notes = matched_app.get("notes", "") or ""
            updated_notes = f"{existing_notes}\n[AI Reply Update ({datetime.now().strftime('%Y-%m-%d')}): {analysis.get('category')} - {action}]".strip()

            tracker.update_application_status(
                app_id=app_id,
                new_status=suggested_status,
                notes=updated_notes,
                reply_status=analysis.get("category", "Reply Received"),
                interview_date=interview_date,
                meeting_link=meeting_link
            )

    return {
        "status": "SUCCESS",
        "message_id": message_id,
        "matched": matched_app is not None,
        "confidence": confidence,
        "application_id": app_id,
        "company": matched_app.get("company") if matched_app else None,
        "analysis": analysis
    }

def sync_user_mailbox(user_id: int, chain_instance: Chain | None = None) -> dict:
    """
    Connects to the user's IMAP mailbox, performs incremental sync for new emails,
    matches replies deterministically, and runs AI analysis.
    """
    config = tracker.get_user_mail_config(user_id)
    host = config.get("imap_host", "imap.gmail.com")
    port = config.get("imap_port", 993)
    user_email = config.get("email_address", "")
    app_pwd = config.get("app_password", "")
    last_uid = config.get("last_synced_uid", 0)

    if not user_email or not app_pwd:
        return {
            "success": False,
            "error": "Mailbox credentials not configured. Please add your email App Password in Settings.",
            "synced_count": 0,
            "matched_count": 0,
            "results": []
        }

    results = []
    matched_count = 0
    synced_count = 0
    highest_uid = last_uid

    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user_email, app_pwd)
        mail.select("INBOX", readonly=True)

        # Search for messages newer than last_uid, or last 20 messages if initial sync
        if last_uid > 0:
            search_crit = f"UID {last_uid + 1}:*"
        else:
            search_crit = "ALL"

        status, data = mail.uid("SEARCH", None, search_crit)
        if status != "OK" or not data or not data[0]:
            mail.logout()
            return {
                "success": True,
                "synced_count": 0,
                "matched_count": 0,
                "message": "Inbox is already up to date.",
                "results": []
            }

        uid_list = [int(u) for u in data[0].split() if u.isdigit()]
        # Filter out <= last_uid
        uid_list = [u for u in uid_list if u > last_uid]
        
        # Limit to 30 most recent messages per sync to prevent timeouts
        if len(uid_list) > 30:
            uid_list = uid_list[-30:]

        for uid in uid_list:
            if uid > highest_uid:
                highest_uid = uid

            try:
                res_status, msg_data = mail.uid("FETCH", str(uid), "(RFC822)")
                if res_status != "OK" or not msg_data:
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_email = response_part[1]
                        parsed = parse_mime_message(raw_email)
                        
                        proc_res = process_single_incoming_email(
                            user_id=user_id,
                            email_data=parsed,
                            chain_instance=chain_instance
                        )
                        synced_count += 1
                        if proc_res.get("matched"):
                            matched_count += 1
                        results.append(proc_res)

            except Exception as e:
                # Per-message error isolation
                results.append({"status": "ERROR", "uid": uid, "error": str(e)})

        # Update last synced UID
        if highest_uid > last_uid:
            tracker.update_last_synced_uid(user_id=user_id, last_uid=highest_uid)

        mail.logout()
        return {
            "success": True,
            "synced_count": synced_count,
            "matched_count": matched_count,
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"IMAP Sync failed: {str(e)}",
            "synced_count": synced_count,
            "matched_count": matched_count,
            "results": results
        }

def simulate_incoming_reply(user_id: int, app_id: int, raw_reply_text: str, subject: str = "", sender_email: str = "", chain_instance: Chain | None = None) -> dict:
    """
    Simulates an incoming email reply for an application for instant testing in UI.
    """
    app = tracker.get_application_by_id(app_id)
    if not app:
        return {"status": "ERROR", "error": f"Application id {app_id} not found."}

    orig_msg_id = app.get("last_message_id") or f"<outreach_{app_id}_{int(datetime.now().timestamp())}@outreachai.local>"
    sim_msg_id = f"<reply_{app_id}_{int(datetime.now().timestamp())}@recruiter.company.com>"
    sim_sender = sender_email or app.get("recipient_email") or f"recruiting@{app.get('company', 'company').lower().replace(' ', '')}.com"
    sim_subject = subject or f"Re: {app.get('subject_line', 'Application for ' + app.get('role', 'Role'))}"

    email_data = {
        "message_id": sim_msg_id,
        "in_reply_to": orig_msg_id,
        "references": orig_msg_id,
        "thread_id": app.get("thread_id") or f"thread_{app_id}",
        "sender": sim_sender,
        "recipient": app.get("recipient_email", ""),
        "subject": sim_subject,
        "body_text": raw_reply_text,
        "date_str": datetime.now().isoformat()
    }

    return process_single_incoming_email(
        user_id=user_id,
        email_data=email_data,
        chain_instance=chain_instance
    )
