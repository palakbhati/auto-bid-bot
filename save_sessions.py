from playwright.sync_api import sync_playwright
import time
import os

def save_linkedin():
    print("\n=== Saving LinkedIn Session ===")
    os.makedirs("./linkedin_session", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./linkedin_session",
            headless=False,
            slow_mo=100,
            args=[
                "--no-sandbox",
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = browser.new_page()

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        print("➡ Opening LinkedIn...")
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        time.sleep(3)

        # Check if "Welcome Back" screen is showing
        welcome_back = page.query_selector(".signin-other-account, [data-test-id='welcome-back']")
        account_btn = page.query_selector(".artdeco-list__item")

        if account_btn:
            print("🔄 'Welcome Back' screen detected — clicking account...")
            account_btn.click()
            time.sleep(3)

        # Wait for feed
        print("⏳ Waiting for LinkedIn feed...")
        try:
            page.wait_for_url(
                lambda url: "feed" in url or "mynetwork" in url or "jobs" in url,
                timeout=120000
            )
            print(f"✅ Login detected! URL: {page.url}")
        except:
            # Maybe it needs password
            print("⏳ Might need password — please complete login in browser window...")
            print("   Waiting up to 2 minutes...")
            try:
                page.wait_for_url(
                    lambda url: "feed" in url or "mynetwork" in url,
                    timeout=120000
                )
                print(f"✅ Login detected! URL: {page.url}")
            except:
                print(f"⚠️ Could not detect login. URL: {page.url}")

        time.sleep(5)
        cookies = browser.cookies()
        print(f"🍪 Saved {len(cookies)} cookies")
        page.screenshot(path="linkedin_logged_in.png")
        print("📸 Screenshot saved!")
        browser.close()
        print("✅ LinkedIn session saved!\n")

def save_x():
    print("\n=== Saving X (Twitter) Session ===")
    os.makedirs("./x_session", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="./x_session",
            headless=False,
            slow_mo=100,
            args=[
                "--no-sandbox",
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        page = browser.new_page()

        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        print("➡ Opening X (Twitter)...")
        page.goto("https://x.com/login", wait_until="domcontentloaded")

        print("➡ Please login in the browser window that opened.")
        print("⏳ Script will automatically detect when you are logged in...")
        print("   (You have 120 seconds to login)")

        try:
            page.wait_for_url(
                lambda url: "home" in url or "/following" in url or (
                    "x.com" in url and "login" not in url and "i/flow" not in url
                ),
                timeout=120000
            )
            print(f"✅ Login detected! URL: {page.url}")
        except:
            print(f"⚠️  Timeout. Current URL: {page.url}")

        print("⏳ Saving cookies, please wait 5 seconds...")
        time.sleep(5)

        cookies = browser.cookies()
        print(f"🍪 Saved {len(cookies)} cookies")

        page.screenshot(path="x_logged_in.png")
        print("📸 Screenshot saved as x_logged_in.png — check it to confirm!")

        browser.close()
        print("✅ X session saved!\n")


if __name__ == "__main__":
    print("🚀 Starting session saver...")
    print("=" * 50)
    print("IMPORTANT: Login in the NEW browser window")
    print("that will open — NOT in your regular Chrome!")
    print("=" * 50)

    save_linkedin()
    save_x()

    print("\n✅ All done! Check the screenshots to confirm login worked.")