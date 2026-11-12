# SellerShield demo video script (about 2 minutes 30 seconds)

Devpost wants a public YouTube video under 3 minutes. Aim for 2:30 so a slow moment doesn't push you over.

## Before you record (15 minutes)

- Backend and page running: `venv\Scripts\python.exe run.py`
- `.env` has your sandbox keys **and** `ANTHROPIC_API_KEY`, so the verdict card says "AI + rules". Check this before you start.
- Click **Test PayPal connection**. The badge must say Connected.
- Open a second browser tab on sandbox.paypal.com and log in as the sandbox **Personal** (buyer) account first. Then approving a payment takes one click on camera.
- Close other tabs and notifications. Use a window about 1280 pixels wide so text is readable.
- Do one full practice run first. It also uses up any first-time delays.
- Record with Windows Game Bar (Win + Alt + R), OBS, or a Meet recording with only you in it.

## Script

**0:00 to 0:20. The problem** (page open, nothing clicked)

> "If you sell online and take PayPal, you get messages like 'I overpaid, send me back the difference' or 'I already sent the payment, ship it now'. They're scams, and they're easy to miss. SellerShield checks the buyer's message before you take the payment."

**0:20 to 0:55. A safe message goes through** (sample 1)

- Choose sample 1, click **Analyze message**. Point at "Looks safe".
- Keep the price at 25.00, click **Create PayPal order**, approve as the buyer, and come back to the page.
- Click **Capture payment**. It shows COMPLETED.

> "A normal question is safe, so it goes through ordinary PayPal checkout."

**0:55 to 1:30. A suspicious message needs the seller to confirm** (sample 8)

- Choose sample 8, click **Analyze message**. Point at "Be careful" and the reason.
- Create the order, approve, come back. Point at "Verdict saved inside the PayPal order".
- Click **Capture payment**. When the confirmation appears, read the first line aloud and click OK.

> "This buyer wants to move to WhatsApp. SellerShield doesn't block it, but the seller has to confirm before the money is taken. And the verdict is stored inside the PayPal order itself."

**1:30 to 2:05. A scam is blocked** (sample 4)

- Choose sample 4, click **Analyze message**. Point at "High risk", "Overpayment scam" and the reasons.
- Click **Copy reply**.
- Click **Create PayPal order**. Point at "No PayPal order was created."

> "This is the classic overpayment scam. SellerShield names it, explains why, and gives the seller a safe reply to send. And no PayPal order is created at all."

**2:05 to 2:30. How it works and close** (page, or the README diagram)

> "Behind this, keyword rules and Claude both judge the message, and the more severe verdict wins. If the AI is down, the rules still work. The verdict controls PayPal orders, captures and refunds. SellerShield: PayPal and AI, stopping scams before the money moves."

Optional, if you have time: after a captured payment, click **Refund payment** and say "and any payment can be refunded in one click". Cut it if you're past 2:30.

## After recording

1. Watch the video once. Check the text is readable and nothing private is on screen: no `.env`, no keys, no personal tabs.
2. Upload to YouTube. Set visibility to **Public**.
3. Title: "SellerShield: stopping scam buyers with PayPal and AI". In the description, put the GitHub repo link.
4. YouTube takes a few minutes to process. Do this early, not in the last hour.
5. Copy the YouTube link for the Devpost form.
