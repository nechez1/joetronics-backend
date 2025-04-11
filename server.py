from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import requests
import json  # 🔁 Moved to the top
from database import save_order, initialize_db


app = Flask(__name__)
CORS(app, supports_credentials=True)

# Initialize DB
initialize_db()

# ✅ Stripe Secret Key
stripe.api_key = 'sk_test_51RC9yAQO6JUJPWXewohUTZCJueovECgzF4UtTVo0ZLXt0wKn48F37V675vC0sdByK9vtErVa7Musvw9RdeifsnSZ00MqppFomj'

# ✅ Paystack Secret Key
PAYSTACK_SECRET_KEY = 'sk_test_044feda8ef39097190ca6e7738ff79c76da703f9'  # Replace with your real one


@app.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
def create_checkout_session():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'Preflight OK'}), 200

    try:
        data = request.get_json()
        products = data.get('products', [])

        print("📦 Received products:", products)

        line_items = [
            {
                'price_data': {
                    'currency': 'ngn',
                    'product_data': {'name': item['name']},
                    'unit_amount': int(item['price']) * 100,
                },
                'quantity': item['quantity'],
            }
            for item in products
        ]

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url='http://127.0.0.1:5501/html/sucess.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://127.0.0.1:5501/html/cancel.html',
        )

        return jsonify({'sessionId': session.id})

    except Exception as e:
        print("❌ Stripe Error:", str(e))
        return jsonify(error=str(e)), 400


@app.route('/checkout-session/<session_id>', methods=['GET'])
def get_checkout_session(session_id):
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['line_items', 'customer_details']
        )

        line_items = session.get('line_items', {}).get('data', [])
        items = [
            {
                'name': item['description'],
                'quantity': item['quantity'],
                'amount': item['amount_total']
            }
            for item in line_items
        ]

        return jsonify({
            'line_items': items,
            'amount_total': session['amount_total'],
            'customer_details': session.get('customer_details', {})
        })

    except Exception as e:
        print("❌ Failed to retrieve session:", str(e))
        return jsonify(error=str(e)), 400


@app.route('/verify-paystack', methods=['GET'])
def verify_paystack():
    reference = request.args.get('reference')
    if not reference:
        return jsonify({'error': 'Missing reference'}), 400

    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}'
    }

    try:
        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
        result = response.json()

        if not result.get('status'):
            return jsonify({'error': 'Paystack verification failed'}), 400

        data = result['data']
        customer = data.get('customer', {})
        amount = data.get('amount', 0)
        email = customer.get('email', 'N/A')

        # 🛒 Handle cart metadata safely
        raw_cart = data.get('metadata', {}).get('cart', [])
        try:
            cart = json.loads(raw_cart) if isinstance(raw_cart, str) else raw_cart
        except Exception as e:
            print("❌ Failed to parse cart JSON:", e)
            cart = []

        # 💾 Save to database
        save_order(reference, email, cart)

        return jsonify({
            'reference': reference,
            'amount': amount,
            'email': email,
            'cart': cart
        })

    except Exception as e:
        print("❌ Paystack Verify Error:", str(e))
        return jsonify({'error': 'Verification error'}), 400


if __name__ == '__main__':
    app.run(port=4242)
