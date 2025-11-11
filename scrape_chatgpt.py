#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import random
import time
from contextlib import suppress
from seleniumbase import SB

# ====================== Utilities ======================

def sleep_dbg(sb, secs=None, a=None, b=None, label=""):
    if secs is None:
        secs = random.randint(a, b)
    print(f"[SLEEP] {label} sleeping {secs:.1f}s")
    sb.sleep(secs)
    return secs

def short_sleep_dbg(sb, label=""):
    secs = random.randint(8, 15) / 10.0  # 0.8–1.5s
    print(f"[SLEEP] {label} short sleep {secs:.1f}s")
    sb.sleep(secs)
    return secs

def visible(sb, sel):
    try:
        return sb.cdp.is_element_visible(sel)
    except Exception:
        return False

def click_first(sb, selectors, label=""):
    for sel in selectors:
        try:
            if sb.cdp.is_element_visible(sel):
                sb.cdp.click(sel)
                short_sleep_dbg(sb, label=f"after click {label or sel}")
                print(f"[CLICK] {label or sel}")
                return sel
        except Exception as e:
            print(f"[WARN] click fail {sel}: {e}")
    return None

def save_ss(sb, name):
    path = f"screenshots/{name}_{int(time.time())}.png"
    with suppress(Exception):
        sb.save_screenshot(path)
        print(f"[SCREENSHOT] {path}")
    return path

def sanitize_prompt(p):
    """
    Normalize a raw prompt string and strip any leading control keywords.
    - Removes zero-width spaces and brackets.
    - Drops any chain of leading 'prompt'/'delete'/'query' with optional punctuation,
      even if fused (e.g., 'Deleteprompt', 'prompt:prompt-', '[Query]  -  Delete  :  ...').
    - Collapses whitespace.
    """
    if p is None:
        return ""

    s = str(p).replace("\u200b", "")
    s = s.replace("[", "").replace("]", "").strip()

    # Remove any number of leading occurrences (fused or spaced) of the control words.
    # The trick: allow an optional non-alpha boundary between repeats or nothing at all.
    # We'll do this by looping until no change OR do it in one regex with a "+" group.
    before = None
    pattern = re.compile(r'^\s*((?:prompt|delete|query)\s*[:\-]?\s*)+', flags=re.I)
    while s != before:
        before = s
        s = pattern.sub("", s, count=1).strip()

    # If a fused form remains like "deleteprompthello" (unlikely), do one more guard:
    s = re.sub(r'^(prompt|delete|query)+', '', s, flags=re.I).strip()

    # Normalize spaces
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _env_int(name, default):
    try:
        v = os.environ.get(name, "")
        return int(v) if str(v).strip() else default
    except Exception:
        return default

# ====================== Accounts ======================

ACCOUNTS = [
    {"email": "pfu1uont0dm@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "ad9cbnnws29x@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "dsirtrganwfqljx@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "zhvc0ex05l@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "c3v4ebrqk28es2a@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "rq1gyi1tlibvk@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "yi58k4kx@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "tamw4cosq8wd4@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "qy1pzdl8w9wp@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "lpqghfgiclhwuri@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "cr7rvnfqpay@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "eynt5jmzwo6@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "aq1v22k6chc53@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "op4cvlfbzgazi6l@no.vsmailpro.com", "password": "Katana@23033"},
    {"email": "oxmedcxg5of@no.vsmailpro.com", "password": "Katana@23033"},
]

# ====================== Env / Batching ======================

batch_number   = _env_int("BATCH_NUMBER", 1)
total_batches  = _env_int("TOTAL_BATCHES", 2)
MAX_PROMPTS    = _env_int("MAX_PROMPTS", 50)
ACC            = ACCOUNTS[(batch_number - 1) % len(ACCOUNTS)]
cookies_verification=None
with open("merlinAi.json", "r", encoding="utf-8") as f:
    data = json.load(f)
all_prompts = [sanitize_prompt(q.get("text", "")) for q in data.get("queries", [])]

prompts_per_batch = max(1, len(all_prompts) // max(1, total_batches))
start_idx = (batch_number - 1) * prompts_per_batch
end_idx   = len(all_prompts) if batch_number == total_batches else min(len(all_prompts), start_idx + prompts_per_batch)
batch_prompts = all_prompts[start_idx:end_idx][:MAX_PROMPTS]

os.makedirs("screenshots", exist_ok=True)

print("\n" + "=" * 80)
print(f"BATCH {batch_number}/{total_batches}")
print(f"Processing prompts {start_idx} to {start_idx + len(batch_prompts) - 1} ({len(batch_prompts)} total)")
print("=" * 80 + "\n")

# ====================== Textarea Helpers ======================

TEXTAREA_SELECTORS = [
    "#prompt-textarea",
    "textarea#prompt-textarea",
    'textarea[placeholder*="Message" i]',
]

def wait_for_textarea(sb, timeout=40):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for sel in TEXTAREA_SELECTORS:
            if visible(sb, sel):
                return sel
        sb.sleep(0.5)
    return None

def login_page_visible(sb):
    indicators = [
        'h1:contains("Log in or sign up")',
        'text="Log in or sign up"',
        'button[data-testid="login-button"]',
        'button[data-testid="log-in-button"]',
        'button:contains("Log in")',
        'div[role="dialog"]',
        'input#email',
        'input[name="email"]',
        'input[type="email"]',
        'input[placeholder="Email address"]',
        'input[aria-label="Email address"]',
    ]
    for sel in indicators:
        if visible(sb, sel):
            return True
    return False

# ====================== Verification (OTP) Detect ======================

VERIFICATION_PAGE_SELECTORS = [
    'h1:contains("Check your inbox")',
    'text="Check your inbox"',
    'input[name="code"]',
    'input[autocomplete="one-time-code"]',
    'input[id*="code"]',
    'input[placeholder*="Code" i]',
    'button:contains("Resend email")',
]

def verification_page_visible(sb, timeout=12, screenshot_name="verification_code_page"):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for sel in VERIFICATION_PAGE_SELECTORS:
            try:
                if visible(sb, sel):
                    print("[2FA] Email verification page detected")
                    save_ss(sb, screenshot_name)
                    return True
            except Exception:
                pass
        sb.sleep(random.uniform(0.4, 1.2))
    return False

# ====================== Login Flow ======================

def ensure_chat_ready_after_password(sb):
    # Try current page first
    sel = wait_for_textarea(sb, timeout=12)
    if sel:
        print(f"[LOGIN] Textarea found ({sel}) without redirect")
        return True

    print("[LOGIN] Opening https://chatgpt.com/ after password Continue")
    with suppress(Exception):
        sb.open("https://chatgpt.com/")
    sleep_dbg(sb, a=6, b=10, label="after chatgpt.com open")

    sel = wait_for_textarea(sb, timeout=15)
    if sel:
        print(f"[LOGIN] Textarea found ({sel}) after chatgpt.com open")
        return True

    print("[LOGIN] Opening https://chatgpt.com/?oai-dm=1 as fallback")
    with suppress(Exception):
        sb.open("https://chatgpt.com/?oai-dm=1")
    sleep_dbg(sb, a=6, b=10, label="after dm fallback")

    sel = wait_for_textarea(sb, timeout=15)
    if sel:
        print(f"[LOGIN] Textarea found ({sel}) after dm fallback")
        return True

    save_ss(sb, "login_after_password_failed")
    return False

# ====================== Cloudflare Turnstile Helper ======================

def pass_turnstile_if_present(sb, timeout=25):
    """
    Use SeleniumBase helpers to solve Cloudflare Turnstile.
    1) Try sb.solve_captcha() (UC/CDP helper).
    2) If still present, attempt a GUI click on the parent above the shadow-root.
    3) Confirm success by waiting for 'Verified'/'Success' text or the widget to disappear.
    Docs/examples: SeleniumBase CDP Mode + raw_cdp_turnstile.  (See notes above.)
    """
    print("[Turnstile] Checking for Turnstile...")
    turnstile_locs = [
        'iframe[src*="turnstile"]',
        'div[class*="cf-turnstile"]',
        'div:contains("Verify you are human")',
        'div[aria-label*="Verify you are human" i]',
    ]

    detected = False
    with suppress(Exception):
        for sel in turnstile_locs:
            if sb.is_element_present(sel):
                detected = True
                break

    if not detected:
        print("[Turnstile] Not detected.")
        return True

    # 1) Built-in solver
    try:
        print("[Turnstile] Trying SeleniumBase solver: solve_captcha()")
        sb.solve_captcha()  # per docs; no args needed
        short_sleep_dbg(sb, "after solve_captcha()")
    except Exception as e:
        print(f"[Turnstile][WARN] solve_captcha() failed: {e}")

    # 2) If still there, try GUI click on parents often used by CF widgets
    still_there = False
    with suppress(Exception):
        still_there = sb.is_element_present('iframe[src*="turnstile"]')

    if still_there:
        print("[Turnstile] Still present, attempting GUI click on widget parent")
        parents = [
            '#turnstile-widget div',
            'div[id*="turnstile"] div',
            'div[aria-label*="Verify you are human" i]',
        ]
        for sel in parents:
            with suppress(Exception):
                sb.cdp.gui_click_element(sel)
                short_sleep_dbg(sb, f"gui-click {sel}")
                break

    # 3) Success check
    ok = False
    with suppress(Exception):
        sb.wait_for_text("Verified", timeout=timeout)
        ok = True
    if not ok:
        with suppress(Exception):
            sb.wait_for_text("Success", timeout=timeout)
            ok = True
    if not ok:
        # Or the iframe becomes absent (token accepted)
        with suppress(Exception):
            sb.wait_for_element_absent('iframe[src*="turnstile"]', timeout=timeout)
            ok = True

    if ok:
        print("[Turnstile] Challenge cleared.")
        return True

    print("Error: [Turnstile][ERROR] Could not confirm Turnstile success")
    save_ss(sb, "boomlify_turnstile")
    return False

# ====================== Boomlify OTP Fetcher (second tab) ======================

def fetch_chatgpt_code_from_boomlify(
    sb,
    search_email,
    login_email="staywhizzy2023@gmail.com",
    login_password="Katana@23033",
    tab_should_close=True,
    total_timeout=60,
):
    """
    Opens Boomlify in a new tab, logs in, searches for the given email address,
    finds "Your ChatGPT code is NNNNNN", returns the 6-digit code (str) or None.
    Leaves you back on the original tab; closes the Boomlify tab by default.
    """
    print("[OTP] Opening Boomlify in a new tab to fetch verification code")
    try:
        orig_tab_index = 0
    except Exception:
        orig_tab_index = 0

    try:
        sb.open_new_tab()        
        url = "https://boomlify.com/en/login"
        sb.open(url)
        short_sleep_dbg(sb, "boomlify login page")
        sb.sleep(3)
        # Fill login form
        sb.cdp.wait_for_element_visible('input[type="email"]', timeout=20)
        sb.cdp.click('input[type="email"]')
        sb.cdp.type('input[type="email"]', login_email)
        save_ss(sb, "boomlify_email_filled")
        short_sleep_dbg(sb, "typed login email")

        sb.cdp.wait_for_element_visible('input[type="password"]', timeout=20)
        sb.cdp.click('input[type="password"]')
        sb.cdp.type('input[type="password"]', login_password)
        save_ss(sb, "boomlify_password_filled")
        short_sleep_dbg(sb, "typed login password")
        sb.sleep(2)
        sb.solve_captcha()
        sb.wait_for_element_absent("input[disabled]")
        sb.sleep(10)
        sb.scroll_down(30)
        sb.sleep(8)
        # # Solve Turnstile if present
        # if not pass_turnstile_if_present(sb, timeout=25):
        #     print("Error: [OTP][Turnstile] Failed to solve challenge on Boomlify login")
        #     return None

        # Submit login
        click_first(
            sb,
            [
                'button:contains("Access Your Secure Inbox")',
                'button[type="submit"]',
            ],
            label="boomlify-login-submit",
        )
        print("[OTP] Access your inbox button clicked")
        sleep_dbg(sb, a=3, b=5, label="after submit login")

        # Make sure we're actually logged in (not Guest)
        with suppress(Exception):
            if not re.search(r"/dashboard", sb.get_current_url() or "", re.I):
                sb.open("https://boomlify.com/en/dashboard")
                sleep_dbg(sb, a=2, b=4, label="ensure dashboard")

        save_ss(sb, "boomlify_dashboard_check")

        page = ""
        with suppress(Exception):
            page = sb.get_page_source()

        # if re.search(r"Guest User", page, re.I) or re.search(r"\bLogin\b", page, re.I):
        #     print("Error: [OTP][ERROR] Boomlify login verification failed (still guest?)")
        #     return None

        # Search the email
        search_selectors = [
            'input[placeholder*="Search" i]',
            'input[type="search"]',
            'input[aria-label*="Search" i]',
        ]
        ssel = click_first(sb, search_selectors, label="boomlify-search")
        if not ssel:
            print("[OTP][ERROR] Search input not found on Boomlify dashboard")
            save_ss(sb, "boomlify_search_missing")
            return None

        sb.cdp.select_all(ssel)
        sb.cdp.type(ssel, search_email)
        short_sleep_dbg(sb, "after typing search email")

        # Scrape the 6-digit code (refresh text a few times)
        code = None
        t0 = time.time()
        while time.time() - t0 < total_timeout:
            try:
                html = sb.get_page_source()
                m = re.search(r"Your\s+ChatGPT\s+code\s+is\s+(\d{6})", html, re.I)
                if m:
                    code = m.group(1)
                    break
            except Exception:
                pass
            sb.sleep(1.0)

        if not code:
            print(f"Error: [OTP][ERROR] Could not find ChatGPT code for {search_email}")
            save_ss(sb, "boomlify_code_not_found")
            return None

        print(f"[OTP][SUCCESS] Found verification code: {code}")
        save_ss(sb, f"boomlify_code_{code}")
        return code

    finally:
        # Use official example approach - just switch tab, let context manager cleanup
        try:
            sb.open_new_tab("https://auth.openai.com/email-verification")
            sb.cdp.set_all_cookies(cookies_verification)
            print("[OTP] Switched back to original tab")
            sb.sleep(8)
            save_ss(sb, f"Switched back to original tab")
            sb.sleep(10)
            
            page_html = sb.get_page_source()
            if len(page_html) < 1000:
                print("[OTP] Page HTML is very short - likely blank")
                print(f"HTML: {page_html[:500]}")
            else:
                print(f"[OTP] Page HTML length: {len(page_html)}")

            # Check for redirects
            current_url = sb.get_current_url()
            if "login" in current_url.lower():
                print("[OTP] Redirected to login - authentication required")
            elif "error" in current_url.lower():
                print("[OTP] Error page detected")  

        except Exception as e:
            print(f"[OTP][WARN] Could not switch tabs: {str(e)[:100]}")
            save_ss(sb, f"Could not switch tabs")



# ====================== Submit OTP on ChatGPT page ======================

def submit_chatgpt_verification_code(sb, code):
    code_selectors = [
        'input[name="code"]',
        'input[autocomplete="one-time-code"]',
        'input[id*="code"]',
        'input[placeholder*="Code" i]',
    ]
    sel = None
    for s in code_selectors:
        if visible(sb, s):
            sel = s
            break
    if not sel:
        print("[OTP][ERROR] Code input not visible on ChatGPT page")
        save_ss(sb, "otp_input_missing")
        return False

    sb.cdp.click(sel)
    sb.cdp.type(sel, str(code))
    short_sleep_dbg(sb, "after typing OTP")

    if not click_first(sb, ['button:contains("Continue")', 'button[type="submit"]'], label="otp-continue"):
        print("[OTP][WARN] Continue button not found; trying Enter")
        with suppress(Exception):
            sb.cdp.press_keys(sel, "Enter")
            short_sleep_dbg(sb, "after Enter on OTP")

    if wait_for_textarea(sb, timeout=20):
        print("[OTP][INFO] OTP accepted; chat textarea visible")
        return True

    print("[OTP][WARN] OTP submission did not reveal textarea yet")
    save_ss(sb, "otp_submit_unclear")
    return False

def handle_login(sb, email, password):
    print("[LOGIN] Navigating to https://chatgpt.com/auth/login")
    try:
        sb.open("https://chatgpt.com/auth/login")
    except Exception as e:
        print("[LOGIN][ERROR] Could not open /auth/login:", str(e)[:200])
        save_ss(sb, "login_open_error")
        return "reopen"

    sleep_dbg(sb, a=8, b=15, label="after /auth/login open")
    save_ss(sb, "login_page")

    login_button_selectors = [
        'button[data-testid="login-button"]',
        'button[data-testid="log-in-button"]',
        'button:has(span:contains("Log in"))',
        'button:contains("Log in")',
    ]
    clicked_login_btn = click_first(sb, login_button_selectors, label="login button")
    if clicked_login_btn:
        print(f"[LOGIN] Clicked login button: {clicked_login_btn}")
        sleep_dbg(sb, a=1, b=3, label="post login-button click")
        save_ss(sb, "after_login_btn")

    email_selectors = [
        'div[role="dialog"] input#email',
        'div[role="dialog"] input[name="email"]',
        'div[role="dialog"] input[type="email"]',
        'div[role="dialog"] input[placeholder="Email address"]',
        'div[role="dialog"] input[aria-label="Email address"]',
        'input#email',
        'input[name="email"]',
        'input[type="email"]',
        'input[placeholder="Email address"]',
        'input[aria-label="Email address"]',
    ]
    email_input = None
    for _ in range(30):
        for sel in email_selectors:
            if visible(sb, sel):
                email_input = sel
                break
        if email_input:
            break
        sb.sleep(0.5)

    if not email_input:
        print("[ERROR]: [ERROR] Email input not found in login dialog")
        save_ss(sb, "email_input_not_found")
        return "reopen"

    print(f"[LOGIN] Email input found: {email_input}")
    try:
        sb.cdp.click(email_input)
        short_sleep_dbg(sb, label="before typing email")
        sb.cdp.type(email_input, email)
        short_sleep_dbg(sb, label="after typing email")
        save_ss(sb, "email_typed")
    except Exception as e:
        print("[LOGIN][ERROR] Typing email failed:", str(e)[:200])
        save_ss(sb, "email_type_error")
        return "reopen"

    continue_btn_selectors = [
        'div[role="dialog"] button[type="submit"]',
        'div[role="dialog"] button:contains("Continue")',
        'button[type="submit"]',
        'button:contains("Continue")',
    ]
    cont_sel = click_first(sb, continue_btn_selectors, label="continue-after-email")
    if not cont_sel:
        print("[LOGIN][ERROR] Continue button after email not found/clickable")
        save_ss(sb, "continue_button_missing")
        return "reopen"

    sleep_dbg(sb, a=8, b=15, label="after Continue (email)")

    # If email verification page appears here, report and stop login flow
    if verification_page_visible(sb, timeout=8, screenshot_name="verification_after_email"):
        print("[LOGIN][INFO] Verification code required after email step")
        return "verification"

    # Password input on auth.openai.com
    pwd_selectors = [
        'input[type="password"]',
        'input[autocomplete="current-password"]',
        'input[id*="current-password"]',
        'input[name="password"]',
        'input[placeholder*="Password" i]',
    ]
    pwd_input = None
    for _ in range(40):
        for sel in pwd_selectors:
            if visible(sb, sel):
                pwd_input = sel
                break
        if pwd_input:
            break
        sb.sleep(0.5)

    if not pwd_input:
        print("[LOGIN][ERROR] Password input not found")
        save_ss(sb, "password_input_not_found")
        return "reopen"

    print(f"[LOGIN] Password input found: {pwd_input}")
    try:
        sb.cdp.click(pwd_input)
        short_sleep_dbg(sb, label="before typing password")
        sb.cdp.type(pwd_input, password)
        short_sleep_dbg(sb, label="after typing password")
        save_ss(sb, "password_typed")
    except Exception as e:
        print("[LOGIN][ERROR] Typing password failed:", str(e)[:200])
        save_ss(sb, "password_type_error")
        return "reopen"

    pw_continue_selectors = [
        'button[type="submit"]',
        'button:contains("Continue")',
    ]
    pw_sel = click_first(sb, pw_continue_selectors, label="password-continue")
    if not pw_sel:
        print("[LOGIN][ERROR] Password submit button not found/clickable")
        save_ss(sb, "password_continue_missing")
        return "reopen"

    sleep_dbg(sb, a=8, b=15, label="after Continue (password)")
    save_ss(sb, "after_password_continue")
    try:
        cookies_verification = sb.get()  # ✅ Correct
        print(f"[LOGIN] Saved {len(cookies_verification)} cookies")
    except Exception as e:
        print(f"[LOGIN] Error saving cookies: {e}")
    
    # If verification page appears after password, report and stop login flow
    if verification_page_visible(sb, timeout=8, screenshot_name="verification_after_password"):
        print("[LOGIN][INFO] Verification code required after password step")
        return "verification"
    
    
    if ensure_chat_ready_after_password(sb):
        save_ss(sb, "chat_ui_ready")
        print("[LOGIN] Login successful, chat UI visible")
        return True

    print("[LOGIN][ERROR] After login, #prompt-textarea not visible")
    return "reopen"

# ====================== Send Helpers ======================

SEND_SELECTORS = [
    'button[data-testid="send-button"]',
    'button[aria-label="Send message"]',
    'button[aria-label="Send"]',
    'button:has(svg[aria-label="Send"])',
]

def try_send(sb):
    for sel in SEND_SELECTORS:
        try:
            sb.cdp.wait_for_element_visible(sel, timeout=7)
            sb.scroll_into_view(sel)
            short_sleep_dbg(sb, label=f"after scroll to {sel}")
            sb.cdp.click(sel)
            short_sleep_dbg(sb, label=f"after click {sel}")
            print(f"[DEBUG] Send clicked via {sel}")
            return True
        except Exception as e:
            print(f"[SEND][WARN] {sel} not clickable/visible yet: {e}")

    # Fallback: Enter
    try:
        sb.cdp.click("#prompt-textarea")
        short_sleep_dbg(sb, label="before Enter fallback")
        sb.cdp.press_keys("#prompt-textarea", "Enter")
        short_sleep_dbg(sb, label="after Enter fallback")
        print("[DEBUG] Send via Enter fallback")
        return True
    except Exception as e:
        print(f"[SEND][ERROR] Enter fallback failed: {str(e)[:200]}")
        return False

# ====================== Scraper ======================

def scrape_chatgpt_responses(prompts):
    results = []
    total = len(prompts)
    i = 0
    max_retries = 2
    force_login_on_reopen = False

    while i < total:
        tries = 0
        while tries < max_retries and i < total:
            trigger_reopen = False
            try:
                with SB(uc=True, test=True, ad_block=True, locale="en") as sb:
                    url = "https://chatgpt.com/"
                    print("\n" + "=" * 80)
                    print("Opening ChatGPT:", url)
                    print("=" * 80 + "\n")

                    sb.activate_cdp_mode(url)
                    sleep_dbg(sb, a=8, b=15, label="after initial open")

                    if force_login_on_reopen:
                        print("[INFO] Forced login due to prior error")
                        lr = handle_login(sb, ACC["email"], ACC["password"])
                        if lr == "verification":
                            # Fetch OTP from Boomlify, then submit
                            code = fetch_chatgpt_code_from_boomlify(sb, ACC["email"])
                            if code and submit_chatgpt_verification_code(sb, code):
                                lr = True
                            else:
                                trigger_reopen = True
                        if lr == "reopen" or not lr:
                            print("Error:  Login failed -> reopen")
                            trigger_reopen = True
                        else:
                            sleep_dbg(sb, a=8, b=15, label="post-login settle")
                            force_login_on_reopen = False
                    else:
                        if login_page_visible(sb):
                            print("[INFO] Login page detected -> /auth/login flow")
                            lr = handle_login(sb, ACC["email"], ACC["password"])
                            if lr == "verification":
                                code = fetch_chatgpt_code_from_boomlify(sb, ACC["email"])
                                if code and submit_chatgpt_verification_code(sb, code):
                                    lr = True
                                else:
                                    trigger_reopen = True
                            if lr == "reopen" or not lr:
                                print("Error:  Login failed -> reopen")
                                trigger_reopen = True
                            else:
                                sleep_dbg(sb, a=8, b=15, label="post-login settle")
                        else:
                            print("[DEBUG] No login required")

                    if not trigger_reopen:
                        sb.click_if_visible('button[aria-label="Close dialog"]')
                        sb.click_if_visible('button[data-testid="close-button"]')
                        short_sleep_dbg(sb, label="after closing dialogs")
                        sel = wait_for_textarea(sb, timeout=40)
                        if not sel:
                            print("[ERROR] Textarea not found on load")
                            save_ss(sb, "textarea_not_found_on_load")
                            trigger_reopen = True
                            force_login_on_reopen = True

                    while not trigger_reopen and i < total:
                        prompt_raw = prompts[i]
                        prompt = sanitize_prompt(prompt_raw)
                        print("[%d/%d] Sanitized prompt: %s" % (i + 1, total, (prompt[:100] if prompt else "")))
                        print("-" * 80)

                        if not prompt:
                            print("[WARN] Empty prompt after cleaning; skipping")
                            results.append({
                                "prompt": prompt_raw,
                                "response": "Error: Empty prompt after cleaning",
                                "screenshot": None,
                                "captcha_type": None,
                            })
                            i += 1
                            continue

                        try:
                            # Dismiss “Stay logged out” modal if appears
                            login_modal_selectors = [
                                'a[href="#"][class*="text-secondary"]',
                                'a[href="#"]:contains("Stay logged out")',
                                '[role="dialog"] a[href="#"]',
                                'div[role="dialog"] a',
                            ]
                            for sel in login_modal_selectors:
                                if visible(sb, sel):
                                    print("[WARNING] LOGIN MODAL detected -> dismissing")
                                    sb.cdp.click(sel)
                                    short_sleep_dbg(sb, label="after dismiss click")
                                    print("[DEBUG] Modal dismissed")
                                    break

                            if not visible(sb, "#prompt-textarea"):
                                print("[ERROR] Textarea missing -> reopen & force login")
                                save_ss(sb, "textarea_missing_midrun")
                                trigger_reopen = True
                                force_login_on_reopen = True
                                continue

                            # Type prompt
                            sb.scroll_into_view("#prompt-textarea")
                            short_sleep_dbg(sb, label="after scroll to textarea")
                            sb.cdp.click("#prompt-textarea")
                            short_sleep_dbg(sb, label="after click textarea")
                            sb.cdp.select_all("#prompt-textarea")
                            sb.cdp.press_keys("#prompt-textarea", "Delete")
                            short_sleep_dbg(sb, label="after clear textarea")
                            sb.cdp.type("#prompt-textarea", prompt)
                            short_sleep_dbg(sb, label="after typing prompt")

                            # Send
                            if not try_send(sb):
                                print("Error:  Send failed -> reopen")
                                screenshot_path = save_ss(sb, f"send_failed_{i+1}")
                                results.append({
                                    "prompt": prompt_raw,
                                    "response": "Error: Send failed",
                                    "screenshot": screenshot_path,
                                    "captcha_type": None,
                                })
                                trigger_reopen = True
                                force_login_on_reopen = True
                                continue

                            # Wait finished + extra
                            with suppress(Exception):
                                sb.cdp.wait_for_element_not_visible('button[data-testid="stop-button"]', timeout=90)
                            sleep_dbg(sb, a=10, b=15, label="extra wait after streaming")

                            # Extract last assistant message
                            response_selectors = [
                                '[data-message-author-role="assistant"] .markdown',
                                '[data-message-author-role="assistant"] article',
                                'div[data-message-author-role="assistant"]',
                                '[class*="message"] [class*="markdown"]',
                                '[role="article"] .markdown',
                            ]
                            elems = []
                            for sel in response_selectors:
                                try:
                                    elems = sb.cdp.find_elements(sel)
                                    if elems:
                                        break
                                except Exception:
                                    pass

                            if not elems:
                                print("[WARNING] No response found")
                                screenshot_path = save_ss(sb, f"no_response_{i+1}")
                                results.append({
                                    "prompt": prompt_raw,
                                    "response": "Error: No response",
                                    "screenshot": screenshot_path,
                                    "captcha_type": None,
                                })
                                i += 1
                                sleep_dbg(sb, a=8, b=15, label="between prompts (no response)")
                                continue

                            try:
                                latest = elems[-1].get_html()
                                text = sb.get_beautiful_soup(latest).text.strip().replace("\n\n\n", "\n\n")
                            except Exception as e:
                                print("[WARNING] Extract failed:", str(e)[:200])
                                screenshot_path = save_ss(sb, f"extract_failed_{i+1}")
                                results.append({
                                    "prompt": prompt_raw,
                                    "response": "Error: Extract failed",
                                    "screenshot": screenshot_path,
                                    "captcha_type": None,
                                })
                                i += 1
                                sleep_dbg(sb, a=8, b=15, label="between prompts (extract failed)")
                                continue

                            if not text or len(text) < 10:
                                print("[WARNING] Response too short")
                                screenshot_path = save_ss(sb, f"empty_response_{i+1}")
                                results.append({
                                    "prompt": prompt_raw,
                                    "response": "Error: Empty response",
                                    "screenshot": screenshot_path,
                                    "captcha_type": None,
                                })
                                i += 1
                                sleep_dbg(sb, a=8, b=15, label="between prompts (short response)")
                                continue

                            screenshot_path = save_ss(sb, f"success_{i+1}")
                            results.append({
                                "prompt": prompt_raw,
                                "response": text,
                                "screenshot": screenshot_path,
                                "captcha_type": None,
                            })
                            print("[SUCCESS] Response received (%d chars)\n" % len(text))
                            i += 1
                            sleep_dbg(sb, a=8, b=15, label="between prompts")

                        except Exception as e:
                            print("[ERROR] Unexpected exception -> reopen & force login:", str(e)[:200])
                            screenshot_path = save_ss(sb, f"general_exception_{i+1}")
                            results.append({
                                "prompt": prompt_raw,
                                "response": f"Error: {str(e)[:150]}",
                                "screenshot": screenshot_path,
                                "captcha_type": None,
                            })
                            trigger_reopen = True
                            force_login_on_reopen = True
                            continue

                if trigger_reopen:
                    tries += 1
                    print(f"[INFO] Will reopen browser for prompt index {i} (try {tries}/{max_retries})")
                    continue
                else:
                    break

            except Exception as e:
                print("\n[FATAL] Browser creation/use failed -> will force login next try:", str(e)[:200])
                tries += 1
                force_login_on_reopen = True
                continue

        if i < total and tries >= max_retries:
            results.append({
                "prompt": prompts[i],
                "response": "Error: Could not complete prompt after retries",
                "screenshot": None,
                "captcha_type": None,
            })
            i += 1

    print("\n" + "=" * 80)
    print("All prompts processed!")
    print("=" * 80 + "\n")
    return results

# ====================== Entry ======================

def main():
    print("\n" + "=" * 80)
    print(f"Starting ChatGPT scraping for batch {batch_number}")
    print(f"Processing {len(batch_prompts)} prompts (max {MAX_PROMPTS})")
    print("=" * 80 + "\n")

    results = scrape_chatgpt_responses(batch_prompts)

    for idx, result in enumerate(results):
        qi = start_idx + idx
        result["batch_id"] = batch_number
        result["query_index"] = qi
        try:
            result["prompt_id"] = data["queries"][qi].get("id", qi)
        except Exception:
            result["prompt_id"] = qi

    out_file = f"results_batch_{batch_number}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    success = sum(1 for r in results if not str(r.get("response", "")).startswith("Error"))
    print("\n" + "=" * 80)
    print(f"[✓] Batch {batch_number}: {success}/{len(batch_prompts)} successful")
    print(f"[✓] Results saved to {out_file}")
    print("=" * 80 + "\n")
    return results

if __name__ == "__main__":
    main()
