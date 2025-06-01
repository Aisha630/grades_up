from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv
import os
import functools
import time
import beepy
from utils import *
import subprocess
from twilio.rest import Client
from contextlib import contextmanager
from dataclasses import dataclass, field

load_dotenv()
logger = init_logging()

def log_exceptions(func):
    """Decorator for exception logging"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {e}")
            raise
    return wrapper


@dataclass
class GradeChecker:
    current_grades: dict = field(default_factory=dict)
    init_done: bool = False
    
    def __post_init__(self):
        self.setup_twilio()
    
    def setup_twilio(self):
        """Initialize Twilio client if credentials are available"""
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
        self.twilio_to = os.getenv("TO_WHATSAPP_NUMBER")
        
        self.twilio_client = Client(sid, token) if sid and token else None
        
    @contextmanager
    def browser_context(self, headless: bool=True):
        """Context manager for browser lifecycle"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            try:
                page = browser.new_page()
                yield page
            finally:
                browser.close()

    @log_exceptions
    def macos_notify(self, title: str, message: str):
        """Send macOS notification"""
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], check=True, timeout=10)


    @log_exceptions
    def send_whatsapp(self, course: str, grade: str):
        """Send WhatsApp notification"""
        if not (self.twilio_client and self.twilio_from and self.twilio_to):
            return
            
        message = self.twilio_client.messages.create(
            body=f"🎓 New grade: {course} → {grade}",
            from_=self.twilio_from,
            to=self.twilio_to
        )
        logger.info(f"WhatsApp sent (SID={message.sid})")
    

    @log_exceptions
    def scrape_grades(self, page: Page) -> dict:
        """Extract grades from the page"""
        page.wait_for_selector('table#TERM_CLASSES\\$scroll\\$0 table.PSLEVEL1GRID', timeout=10000)
        rows = page.locator('table#TERM_CLASSES\\$scroll\\$0 table.PSLEVEL1GRID tr')
        total_rows = rows.count()
        
        grades = {}
        for i in range(1, total_rows):
            cells = rows.nth(i).locator('td')
            if cells.count() >= 5:
                course_code = cells.nth(0).inner_text().strip()
                grade = cells.nth(4).inner_text().strip()
                if course_code and grade:
                    grades[course_code] = grade
        
        logger.info(f"Scraped {grades}")
        return grades
    
    def select_semester(self, page: Page) -> bool:
        """Select the semester radio button"""
        xpath_row = f'//tr[.//span[text()="{SEMESTER_NAME}"]]'
        xpath_input = f'{xpath_row}//input[@type="radio"]'
        
        try:
            page.eval_on_selector(xpath_input, """
                el => {
                    el.checked = true;
                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                }
            """)
            return True
        except Exception as e:
            logger.error(f"Failed to select semester: {e}")
            return False

    @log_exceptions
    def login_and_navigate(self, page: Page):
        """Handle login and navigation to grades page"""
        page.goto(SIGN_IN_URL)
        page.fill('#userid', os.getenv("ZAMBEEL_ID", ""))
        page.fill('#pwd', os.getenv("ZAMBEEL_PASSWORD", ""))
        page.click('input[name="Submit"]')
        page.wait_for_load_state("networkidle")
        
        page.goto(ENROLLMENT_TAB_URL)
        page.wait_for_load_state("networkidle")
        page.goto(GRADES_SEMESTER_URL)
        page.wait_for_load_state("networkidle")
        
        logger.info("Navigation completed")

    @log_exceptions
    def check_grades(self, page: Page) -> dict:
        """Check for new grades"""
        if not self.select_semester(page):
            return {}
            
        page.wait_for_timeout(500)
        page.click('input[id="DERIVED_SSS_SCT_SSR_PB_GO"]')
        page.wait_for_load_state("networkidle")
        
        grades = self.scrape_grades(page)
        
        if not self.init_done and grades:
            self.current_grades = grades.copy()
            self.init_done = True
            
        return grades
    
    @log_exceptions
    def process_grade_changes(self, new_grades: dict) -> bool:
        """Compare grades and notify of changes"""
        changes_found = False
        
        for course, grade in new_grades.items():
            if course not in self.current_grades or self.current_grades[course] != grade:
                logger.success(f"New grade detected: {course} → {grade}")
                
                beepy.beep(sound=6)
                self.macos_notify("📢 New Grade Posted!", f"{course}: {grade}")
                self.send_whatsapp(course, grade)
                
                self.current_grades[course] = grade
                changes_found = True
                logger.success(f"Grade change processed for {course}")
        
        return changes_found

    def run_single_check(self, page: Page) -> bool:
        """Perform one grade check cycle"""
        try:
            grades = self.check_grades(page)
            if grades:
                self.process_grade_changes(grades)
                return True
            else:
                logger.warning("No grades found in this cycle")
                return False
        except Exception as e:
            logger.exception(f"Grade check failed: {e}")
            return False

    def run(self, check_interval: int=DEFAULT_CHECK_INTERVAL, headless: bool=True):
        """Main execution loop"""
        retries = 0
        with self.browser_context(headless=headless) as page:
            self.login_and_navigate(page)
            
            while retries <= MAX_RETRIES:
                try:
                    success = self.run_single_check(page)
                    
                    if success:
                        logger.info(f"Check complete. Sleeping {check_interval} seconds...")
                    else:
                        logger.warning("Check failed, retrying sooner...")
                        
                    time.sleep(check_interval if success else DEFAULT_RETRY_DELAY)
                    
                    page.reload()
                    page.wait_for_load_state("networkidle")
                    retries = 0  

                except Exception as e:
                    logger.exception(f"Unexpected error: {e}")
                    time.sleep(DEFAULT_RETRY_DELAY)
                    self.login_and_navigate(page)
                    retries += 1


def main():
    checker = GradeChecker()
    checker.run(check_interval=DEFAULT_CHECK_INTERVAL, headless=False)  # 10 minutes


if __name__ == "__main__":
    main()
