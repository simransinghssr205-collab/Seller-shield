# Devpost description (draft, edit it so it sounds like your team)

## Tagline

Stops scam buyers before the PayPal payment moves.

## Inspiration

Sellers who take PayPal get messages like "I overpaid, please send back the difference", "I already sent the payment, ship it now" or "pay me outside PayPal". They are well-known scams, and they work because the seller is busy and the message sounds friendly. We wanted a check that happens before the money moves, not after.

## What it does

SellerShield reads a buyer's message and gives the seller a verdict: safe, warning or danger. It also gives a risk score, the reasons, the type of scam, and a short safe reply the seller can copy and send back.

The verdict then controls the PayPal payment:

- **Danger:** no PayPal order is created.
- **Warning:** the order is created, but the seller has to confirm before the payment is captured.
- **Safe:** normal PayPal checkout.

The verdict is saved inside the PayPal order, so it survives restarts and an order marked high risk cannot be captured. A captured payment can be refunded in one click.

## How we built it

- **PayPal:** OAuth 2.0, Orders v2 (create with the verdict in `custom_id`, get, capture) and Payments v2 (refund), all on the sandbox.
- **AI:** Claude through the Anthropic Messages API reads the message and returns the verdict, scam type, reasons, a summary and a suggested reply. The message is treated as untrusted data, so instructions hidden in it are not followed.
- **Rules:** keyword rules always run alongside the AI. The more severe verdict wins, and if the AI is unavailable the rules still work.
- **Stack:** Python and Flask for the backend, plain HTML, CSS and JavaScript for the page, and unit tests that run without keys or internet.

## Challenges

- Keeping the app useful when the AI service is slow or down. The rules fallback means the seller always gets a verdict.
- Keeping the verdict attached to the payment. Storing it in the PayPal order means it doesn't depend on our server's memory.

## What's next

- Authorize the payment first and capture or void it after the seller has reviewed a warning.
- Rules and AI prompts for more languages.
- Connect to the marketplaces where sellers actually receive these messages.

## Built with

Python, Flask, PayPal Orders and Payments APIs (sandbox), Anthropic Claude API, HTML, CSS, JavaScript

## Links to add on the form

- Public GitHub repo: (your repo link)
- Demo video: (your public YouTube link)
