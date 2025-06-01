# Zambeel Grade Notifier

This is a simple Python script I wrote because I was tired of manually checking the LUMS Zambeel portal again and again to see if grades were posted.

It automates the login process, navigates to the grades page, checks for changes, and sends you a notification if new grades appear. Notifications can be sent via macOS system alerts, WhatsApp (using Twilio), or a beep sound.

Run this in a tmux session or a backgrounf script, whatever you prefer.

---

## Features

* Logs into Zambeel with your credentials
* Selects the latest semester (configured in `utils.py`)
* Periodically checks for grade updates
* Sends a notification when new grades are found
* Keeps a local record of previously seen grades to avoid duplicate alerts
* Logs all activity to a file

---

## Requirements

* Python 3.9+
* [Playwright](https://playwright.dev/python/)
* `twilio`, `beepy`, `python-dotenv`, `colorlog`

Install dependencies:

```bash
uv venv
uv pip install -r requirements.txt  # or use pyproject.toml with `uv pip install .`
playwright install
```

---

## Setup

1. Create your `.env` file based on the sample:

```bash
cp .env.sample .env
```

Then fill in your environment variables:

```env
ZAMBEEL_ID=your_lums_id
ZAMBEEL_PASSWORD=your_password

# Optional: for WhatsApp alerts
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TO_WHATSAPP_NUMBER=whatsapp:+92xxxxxxxxxx
```

2. Set the semester name inside `utils.py`:

```python
SEMESTER_NAME = "Spring Semester 2024-25"
```

---

## Usage

Run the script:

```bash
uv run main.py
```

It will:

* Open a browser (non-headless by default)
* Log into Zambeel
* Select the correct semester
* Start checking for grades every 10 minutes (configurable)
* Notify you on any new grades via Whatsapp, a success sound, and notification on your Mac

Stop it any time with `Ctrl+C`.

---

## File Structure

```
.
├── main.py             # Main automation logic
├── utils.py            # Constants, logging, semester name
├── .env.sample         # Template for .env
├── pyproject.toml      # Project dependencies
├── grades.log       # Log file (auto-generated)
└── README.md           # This file
```

---

## Notes

* This is a personal script, no fancy UI or packaging.
* It was written for macOS; notifications and sound may not work elsewhere without changes.
* It assumes Zambeel login does not require CAPTCHA.
* Automatically retries if logged out or connection fails.
