from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import time
import random

app = Flask(__name__)

# ─────────────────────────────────────────────────
# HELPER: Get a logged-in LinkedIn page
# ─────────────────────────────────────────────────
def get_linkedin_page(browser):
    page = browser.new_page()
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)

    # Go to feed first
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    time.sleep(3)

    # Handle Welcome Back / login redirect
    for attempt in range(3):
        url = page.url
        print(f"🔁 Attempt {attempt+1} — URL: {url}")

        if "feed" in url:
            print("✅ Already on feed!")
            break

        if "uas" in url or "login" in url or "authwall" in url:
            print("🔄 Login/Welcome screen detected — trying to click account...")

            # Try clicking the account button (Welcome Back screen)
            try:
                account = page.wait_for_selector(
                    ".artdeco-list__item, [data-test-id='remember-me-user']",
                    timeout=5000
                )
                if account:
                    account.click()
                    print("👆 Clicked account button")
                    time.sleep(4)
                    continue
            except:
                pass

            # Try clicking Sign In button if visible
            try:
                sign_in = page.query_selector("button[type='submit'], .sign-in-form__submit-btn")
                if sign_in:
                    sign_in.click()
                    time.sleep(4)
                    continue
            except:
                pass

        time.sleep(3)

    return page


# ─────────────────────────────────────────────────
# LINKEDIN: Search posts
# ─────────────────────────────────────────────────
@app.route("/linkedin/search", methods=["GET"])
def linkedin_search():
    keyword = request.args.get("keyword", "looking for developer")
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./linkedin_session",
                headless=False,
                args=[
                    "--no-sandbox",
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                ],
                ignore_default_args=["--enable-automation"],
            )

            page = get_linkedin_page(browser)

            # Now go to search
            search_url = f"https://www.linkedin.com/search/results/content/?keywords={keyword.replace(' ', '%20')}&sortBy=date_posted"
            print(f"🔍 Searching: {search_url}")
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(random.uniform(4, 6))

            # Scroll to load posts
            for _ in range(4):
                page.evaluate("window.scrollBy(0, 700)")
                time.sleep(1.5)

            # Take screenshot for debugging
            page.screenshot(path="linkedin_search_result.png")
            print("📸 Screenshot saved")

            # Extract posts using JavaScript
            posts_data = page.evaluate("""
                () => {
                    const results = [];
                    const seen = new Set();

                    // Method 1: data-urn with activity
                    document.querySelectorAll('[data-urn*="activity"]').forEach(el => {
                        const urn = el.getAttribute('data-urn');
                        const text = el.innerText.trim();
                        if (urn && text.length > 50 && !seen.has(urn)) {
                            seen.add(urn);
                            results.push({ post_id: urn, text: text.slice(0, 600), method: 'data-urn' });
                        }
                    });

                    if (results.length > 0) return results;

                    // Method 2: role=article
                    document.querySelectorAll('[role="article"]').forEach((el, i) => {
                        const text = el.innerText.trim();
                        const id = 'article_' + i;
                        if (text.length > 50 && !seen.has(id)) {
                            seen.add(id);
                            results.push({ post_id: id, text: text.slice(0, 600), method: 'role-article' });
                        }
                    });

                    if (results.length > 0) return results;

                    // Method 3: feed update links
                    document.querySelectorAll('a[href*="/feed/update/"]').forEach((link, i) => {
                        const href = link.getAttribute('href');
                        const urn = href.split('/feed/update/')[1]?.split('?')[0] || '';
                        const container = link.closest('li') || link.closest('div');
                        const text = container ? container.innerText.trim() : '';
                        if (urn && text.length > 50 && !seen.has(urn)) {
                            seen.add(urn);
                            results.push({ post_id: urn, text: text.slice(0, 600), method: 'feed-link' });
                        }
                    });

                    return results;
                }
            """)

            print(f"📦 Found {len(posts_data)} posts")

            # Save HTML
            html = page.content()
            with open("linkedin_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"💾 HTML saved ({len(html)} bytes)")

            for post in posts_data[:20]:
                results.append({
                    "post_id": post.get("post_id", ""),
                    "text": post.get("text", ""),
                    "platform": "linkedin",
                    "method": post.get("method", "")
                })

            browser.close()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    print(f"✅ Returning {len(results)} posts")
    return jsonify(results)


# ─────────────────────────────────────────────────
# LINKEDIN: Post comment
# ─────────────────────────────────────────────────
@app.route("/linkedin/comment", methods=["POST"])
def linkedin_comment():
    data = request.json
    post_id = data.get("post_id")
    comment_text = data.get("comment")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./linkedin_session",
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            page = get_linkedin_page(browser)
            page.goto(f"https://www.linkedin.com/feed/update/{post_id}/")
            time.sleep(random.uniform(4, 7))

            comment_box = page.query_selector(".comments-comment-box__text-editor")
            if comment_box:
                comment_box.click()
                time.sleep(1)
                for char in comment_text:
                    comment_box.type(char)
                    time.sleep(random.uniform(0.04, 0.12))
                time.sleep(2)
                submit = page.query_selector(".comments-comment-box__submit-button")
                if submit:
                    submit.click()
                    time.sleep(3)

            browser.close()
            return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────
# X: Search posts
# ─────────────────────────────────────────────────
@app.route("/x/search", methods=["GET"])
def x_search():
    keyword = request.args.get("keyword", "looking for developer")
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./x_session",
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            page = browser.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)

            search_url = f"https://x.com/search?q={keyword.replace(' ', '+')}&f=live"
            page.goto(search_url, wait_until="domcontentloaded")
            time.sleep(random.uniform(3, 5))

            for _ in range(3):
                page.evaluate("window.scrollBy(0, 600)")
                time.sleep(1.5)

            tweets = page.query_selector_all("article[data-testid='tweet']")
            print(f"🐦 Found {len(tweets)} tweets")

            for tweet in tweets[:15]:
                try:
                    text_el = tweet.query_selector("[data-testid='tweetText']")
                    text = text_el.inner_text() if text_el else ""
                    link_el = tweet.query_selector("a[href*='/status/']")
                    tweet_url = "https://x.com" + link_el.get_attribute("href") if link_el else ""
                    tweet_id = tweet_url.split("/status/")[-1].split("?")[0] if tweet_url else ""
                    if text and tweet_id:
                        results.append({
                            "post_id": tweet_id,
                            "text": text,
                            "platform": "x",
                            "post_url": tweet_url
                        })
                except:
                    continue

            browser.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(results)


# ─────────────────────────────────────────────────
# X: Post reply
# ─────────────────────────────────────────────────
@app.route("/x/reply", methods=["POST"])
def x_reply():
    data = request.json
    post_url = data.get("post_url")
    reply_text = data.get("comment")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir="./x_session",
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            page = browser.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            page.goto(post_url)
            time.sleep(random.uniform(3, 5))

            reply_btn = page.query_selector("[data-testid='reply']")
            if reply_btn:
                reply_btn.click()
                time.sleep(2)
                editor = page.query_selector("[data-testid='tweetTextarea_0']")
                if editor:
                    for char in reply_text:
                        editor.type(char)
                        time.sleep(random.uniform(0.04, 0.1))
                    time.sleep(2)
                    send = page.query_selector("[data-testid='tweetButton']")
                    if send:
                        send.click()
                        time.sleep(3)

            browser.close()
            return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("✅ Flask server running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)