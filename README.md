# BrewAI — AI-Powered Smart Café

Canonical corrected project build for the BrewAI college project.

## Three portals
- Customer: `/`
- Chef: `/chef/login`
- Admin: `/admin/login` (visiting `/admin` while logged out redirects here)

All portals share the same Flask backend and SQLite database.

## Customer features
- Registration/login/logout + persistent session option
- Login required before cart/checkout
- Menu search + working filters: All, Coffee, Tea, Cold Drinks, Snacks, Meals, Desserts
- Product customization: size, sugar, milk, extra espresso, food add-ons
- AI Picks: category, temperature, taste, hunger, dietary preference, mood, budget, Surprise Me, match score + explanation
- Cart progress: free delivery at ₹299, free brownie at ₹499
- Delivery, pickup and table QR ordering (`/table/7` etc.)
- Saved delivery addresses
- Demo COD, Card and UPI QR checkout
- AmEx demo: 8% BrewWallet cashback up to ₹150
- HDFC demo: 5% instant discount up to ₹100
- Random `BRxxxxxx` order number
- Live order tracking driven by Chef status
- 10 BrewPoints per completed ₹100 spent
- 500 BrewPoints can redeem one selected free item at checkout
- Verified birthday reward: free Chocolate Pastry on ₹199+ during birthday week, once per year
- Birthday DOB is locked after verification; uploaded ID bytes are not persisted
- Personalized loyalty insight derived from order history
- Feedback + sentiment classification

## Chef features
- Separate Chef login
- New → Preparing → Ready → Completed kitchen workflow
- Sees product quantities, customizations and table/order type
- Product availability / out-of-stock control

## Admin features
- Separate Admin login
- Revenue, orders, AOV, popular item, customers, new customers, 7-day trend
- All orders + cancellation
- Customer list
- Menu stock control
- Feedback/sentiment + management insight
- Table QR page (Tables 01–12)
- Chef management with maximum 5 active chefs

## Demo staff accounts
Change these before any public/non-demo use.

Admin: `admin@brewai.com` / `BrewAIAdmin!26`

Chefs:
- `chef1@brewai.com` / `ChefOne!26`
- `chef2@brewai.com` / `ChefTwo!26`
- `chef3@brewai.com` / `ChefThree!26`
- `chef4@brewai.com` / `ChefFour!26`
- `chef5@brewai.com` / `ChefFive!26`

## Product images
Put your JPG files in `static/images/`. Exact filenames are listed in `IMAGE_FILENAMES.txt`.

## Run locally on macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Render
Build: `pip install -r requirements.txt`
Start: `gunicorn app:app`
Set a strong `SECRET_KEY` environment variable.

## Important prototype notes
- Card and UPI flows are simulations; no real payment is processed.
- Birthday ID verification is a privacy-conscious college-demo flow, not production identity verification.
- SQLite is fine locally/class demo; use PostgreSQL for durable production cloud data.
