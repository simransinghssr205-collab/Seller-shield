# SellerShield

**Check the buyer before you take the payment.**

SellerShield reads a buyer's message, tells the seller whether it looks like a scam, and uses that verdict to decide whether a PayPal payment is created or captured.

Built for the PayPal AI Hackathon. It runs on the PayPal **sandbox** only, so no real money moves. SellerShield is an independent project and is not made by or affiliated with PayPal.

**Demo video:** <paste your YouTube link here>

![SellerShield showing a high risk verdict](docs/screenshot.png)

## The problem

Sellers who accept PayPal get messages like:

- "I overpaid, please send back the difference"
- "I already sent the payment, ship it now"
- "Let's pay outside PayPal"

These are well-known scams, and they work because the seller is busy and the message sounds friendly. Most tools help after the money has moved. SellerShield checks before.

## What it does

| Verdict | What the seller sees | What happens with PayPal |
| --- | --- | --- |
| **Safe** | Looks safe | Normal checkout and capture |
| **Warning** | Be careful, with the reason | The order is created, but capture needs the seller to confirm |
| **Danger** | High risk, the scam type, and a safe reply to copy | No PayPal order is created |

Every check returns a risk score, the reasons, the type of scam (for example "Overpayment scam"), and a short safe reply the seller can copy and send.

The verdict is saved inside the PayPal order itself (the `custom_id` field). So it is still known after the app restarts, and an order marked high risk cannot be captured. A captured payment can be refunded in one click.

## How PayPal is used

- OAuth 2.0 client credentials for the access token
- **Orders v2:** create an order (with the SellerShield verdict in `custom_id`), get an order, capture an order
- **Payments v2:** refund a capture
- Sandbox only

## How AI is used

- Claude (Anthropic Messages API) reads the buyer's message and returns a verdict, the scam type, reasons, a one-sentence summary and a suggested reply.
- The buyer's message is treated as untrusted data in the prompt, so instructions hidden inside a message are not followed.
- Keyword rules always run next to the AI. The more severe verdict wins. If the AI is unavailable, the rules still give a verdict and the page says "Rules only".
- The default model is `claude-haiku-5-5`. Set `AI_MODEL` in `.env` to use another.

## How it fits together

```
Browser (Frontend, port 3000)
   |  buyer message, price
   v
Flask backend (port 5000)
   |-- risk_rules.py   keyword rules, always on
   |-- ai_checker.py   Claude call, when ANTHROPIC_API_KEY is set
   |-- analyzer.py     combines both, the more severe verdict wins
   '-- app.py -------> PayPal sandbox (create, get, capture, refund)
```

## Run it

You need Python 3, Node.js, and PayPal sandbox keys.

**1. Get sandbox keys.** On developer.paypal.com open Apps & Credentials, switch to **Sandbox**, click Create App (type Merchant), and copy the Client ID and Secret. Sandbox test accounts, including a Personal (buyer) account, are under Testing Tools.

**2. Install.**

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Mac or Linux)
pip install -r requirements.txt
```

**3. Create a `.env` file** in the project folder. It is in `.gitignore`, so never commit it.

```
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_secret
ANTHROPIC_API_KEY=your_key_for_the_ai_check
```

`ANTHROPIC_API_KEY` is optional. Without it, only the rules run.

**4. Start.**

```
venv\Scripts\python.exe run.py        (Windows)
venv/bin/python run.py                (Mac or Linux)
```

This starts the backend and the page together and opens http://localhost:3000. Without Node.js, run `python -m backend.app` in one terminal and `python -m http.server 3000 --directory Frontend` in another.

## Try it

Pick a sample from the list, click **Analyze message**, then **Create PayPal order**. When PayPal opens, log in with the sandbox **Personal** (buyer) account and approve. Then click **Capture payment**.

| Sample | Verdict | What happens |
| --- | --- | --- |
| 1. "Is this still available?" | Safe | Normal checkout and capture |
| 8. "Message me on WhatsApp" | Warning | Capture asks the seller to confirm |
| 4. "I overpaid, send back the difference" | Danger | No PayPal order is created |

## Tests

```
python -m unittest tests.test_rules tests.test_analyzer tests.test_app
```

The tests need no keys and no internet. The 15 sample messages in `data/sample_messages.csv` are checked against their expected verdicts.

## Project layout

```
backend/
  app.py            routes and PayPal gating
  paypal_client.py  PayPal API calls
  risk_rules.py     keyword rules, scam types, safe replies
  ai_checker.py     Claude call
  analyzer.py       combines rules and AI
  config.py         reads .env
Frontend/           the page (index.html, style.css, server.js)
data/               15 sample buyer messages
tests/              unit tests
run.py              starts backend and page together
```

## Limits

- The rules are English keyword patterns, so they catch common scams, not every scam.
- It uses the PayPal sandbox only, so it has not handled real payments.
- A person still confirms any warning, because the AI can be wrong.
- SellerShield does not replace PayPal's own seller protection or dispute process.

## What's next

- Authorize the payment first, then capture or void it after the seller reviews a warning.
- Rules and AI prompts for more languages.
- Connect to the marketplaces where sellers actually receive these messages.

## Team

- Harshita Jalewa
- Simran Kumari
- M Hema

## License

MIT. See `LICENSE`.
