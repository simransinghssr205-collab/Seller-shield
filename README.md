# SellerShield

Check the buyer before you take the payment.

SellerShield looks at the message a buyer sends you and tells you if it looks like a scam. That result then decides if a PayPal payment is allowed to go through.

We built it for the PayPal AI Hackathon. It only uses the PayPal sandbox, so no real money moves. SellerShield is our own project and is not made by or connected to PayPal.

Live demo: https://sellershield-4133.onrender.com/

Demo video: https://www.youtube.com/watch?v=C_MyVet62uc

## Why we made it

If you sell things online and take PayPal, you get messages like "I paid too much, please send the difference back" or "I already paid, ship it now" or "let's do this outside PayPal". These are common scams. They work because the seller is busy and the message sounds nice.

Most tools only help after the money is gone. We wanted something that checks before.

## What it does

You paste the buyer's message. SellerShield gives back:

- a result: safe, warning or high risk
- a risk score out of 100
- the reasons
- the kind of scam, like "Overpayment scam"
- a short safe reply you can copy and send

The result then controls the PayPal payment:

| Result | What happens |
| --- | --- |
| Safe | Normal PayPal checkout |
| Warning | The order is made, but you have to confirm before the money is taken |
| High risk | No PayPal order is made at all |

The result is also saved inside the PayPal order (in the `custom_id` field). So it is not lost if the app restarts, and an order marked high risk can never be captured. A payment that was taken can be refunded with one click.

## How we use PayPal

- OAuth 2.0 to get an access token
- Orders v2 to create, get and capture an order
- Payments v2 to refund a payment
- Sandbox only

## How we use AI

- The message is checked by an AI model (Claude, through the Anthropic API). It gives the result, the scam type, the reasons and a suggested reply.
- We also wrote keyword rules that always run. If the AI says it is more risky than the rules do, we go with the AI. If the AI is not available, the rules still work and the page shows "Rules only".
- The buyer's message is treated as untrusted text, so instructions hidden inside a message are not followed.
- The model can be changed with `AI_MODEL` in `.env`.

## How it fits together

```
Browser (Frontend, port 3000)
   |  buyer message, price
   v
Flask backend (port 5000)
   |-- risk_rules.py   keyword rules, always on
   |-- ai_checker.py   AI call, when ANTHROPIC_API_KEY is set
   |-- analyzer.py     combines both, the riskier result wins
   '-- app.py -------> PayPal sandbox (create, get, capture, refund)
```

## How to run it

You need Python 3, Node.js and PayPal sandbox keys.

1. Get sandbox keys. On developer.paypal.com go to Apps & Credentials, switch to Sandbox, click Create App (type Merchant), and copy the Client ID and Secret. The test buyer account is under Testing Tools.

2. Install:

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Mac or Linux)
pip install -r requirements.txt
```

3. Make a `.env` file in the project folder. It is in `.gitignore`, so do not commit it.

```
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
```

4. Start it:

```
venv\Scripts\python.exe run.py        (Windows)
venv/bin/python run.py                (Mac or Linux)
```

This starts the backend and the page and opens http://localhost:3000. If you do not have Node.js, run `python -m backend.app` in one terminal and `python -m http.server 3000 --directory Frontend` in another.

## Try it

Pick a sample, click Analyze message, then Create PayPal order. When PayPal opens, log in with the sandbox Personal (buyer) account and approve. Then click Capture payment.

| Sample | Result | What happens |
| --- | --- | --- |
| 1. "Is this still available?" | Safe | Normal checkout and capture |
| 8. "Message me on WhatsApp" | Warning | Capture asks you to confirm |
| 4. "I overpaid, send back the difference" | High risk | No PayPal order is made |

## Tests

```
python -m unittest tests.test_rules tests.test_analyzer tests.test_app
```

They do not need keys or internet. They check all 15 sample messages in `data/sample_messages.csv` against the result we expect.

## Files

```
backend/
  app.py            routes and the PayPal checks
  paypal_client.py  PayPal API calls
  risk_rules.py     keyword rules, scam types, safe replies
  ai_checker.py     the AI call
  analyzer.py       combines rules and AI
  config.py         reads .env
Frontend/           the page (index.html, style.css, server.js)
data/               15 sample buyer messages
tests/              unit tests
run.py              starts backend and page together
```

## Limits

- The rules are English keywords, so they catch common scams but not every scam.
- It only uses the PayPal sandbox. It has never handled real payments.
- The live demo link only fully supports the message check. After a buyer approves a payment on PayPal, the hosted version sends them back to `localhost`, so approve, capture and refund only work end to end when you run the app locally. We ran out of time to finish the hosted return setting (`FRONTEND_URL`).
- The AI can be wrong, which is why a person still confirms every warning.
- It does not replace PayPal's own seller protection or dispute process.

## What we want to add next

- Authorize the payment first, then capture or cancel it after the seller reviews a warning.
- Rules and AI prompts for more languages.
- Connect it to the sites where sellers actually get these messages.

## Team

- Harshita Jalewa
- Simran Kumari
- M Hema

## License

MIT. See `LICENSE`.
