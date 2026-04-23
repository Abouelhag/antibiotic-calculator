import os
from flask import Flask, request, jsonify
from db import upgrade_to_premium

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    user_email = data.get('email')
    if user_email:
        upgrade_to_premium(user_email)
        print(f"✅ Upgraded {user_email} to premium")
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
