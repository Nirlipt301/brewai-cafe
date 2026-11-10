# BrewAI smoke-test checklist

1. Customer `/`: hero fits at desktop/mobile widths; quote is in `templates/index.html`.
2. `/menu`: search works; all category filters work; no Vegetarian filter; Tea contains Masala Chai/Mango Iced Tea.
3. Logged-out Add to Cart redirects to customer login.
4. Register customer; login; wallet/cart/profile navbar appears.
5. Customize two versions of the same product; they remain separate cart lines.
6. ₹299+ shows free delivery; ₹499+ adds a free brownie to placed order.
7. Delivery requires address; saved address can be reused. Pickup does not require address.
8. `/table/7` selects Table 07, removes delivery fee, and Chef/Admin see Table 07.
9. COD places order. Card validates demo fields; AmEx credits wallet; HDFC discounts total. UPI QR shows amount and Payment Done places order.
10. Order number is `BR` + 6 digits.
11. Chef `/chef/login` cannot accept Admin account; Admin `/admin/login` cannot accept Chef account.
12. Chef changes New → Preparing → Ready → Completed; customer `/orders` shows same status.
13. Chef/Admin stock toggle makes item unavailable on customer menu.
14. Admin cannot exceed 5 active chefs; removed chef cannot log in.
15. Feedback appears in Admin Feedback & AI with sentiment counts/insight.
16. Birthday verification stores only verification result; DOB has no edit route after verification.
17. Verified birthday + ₹199+ adds birthday pastry once per year during birthday week.
18. 500+ BrewPoints offers free-item redemption and deducts 500 points.
19. Rewards/Profile show personalized loyalty insight after order history exists.
20. Rewards and Why BrewAI navbar links open distinct pages; footer has no development checklist.
