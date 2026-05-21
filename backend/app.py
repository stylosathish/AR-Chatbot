from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pandas as pd
import os

from database import save_history, find_previous_match

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# =========================
# GLOBAL VARIABLES
# =========================

KEYWORD_MAP = {}
EXCEL_FILE = "mapping.xlsx"

# =========================
# LOAD EXCEL (FIXED LOGIC)
# =========================

def load_excel():

    global KEYWORD_MAP
    KEYWORD_MAP = {}

    if os.path.exists(EXCEL_FILE):

        df = pd.read_excel(EXCEL_FILE)

        for _, row in df.iterrows():

            bucket = str(row["Bucket Name"]).strip()

            # -------------------------
            # MAIN KEYWORDS (FIXED SPLIT)
            # -------------------------
            keyword = str(row["Keyword"]).lower()

            if keyword and keyword != "nan":
                for k in keyword.split(","):
                    k = k.strip().lower()
                    if k:
                        KEYWORD_MAP[k] = bucket

            # -------------------------
            # ALTERNATE KEYWORDS (FIXED SPLIT)
            # -------------------------
            if "Alternate Keywords" in df.columns:

                alt = str(row["Alternate Keywords"]).lower()

                if alt and alt != "nan":

                    for k in alt.split(","):
                        k = k.strip().lower()
                        if k:
                            KEYWORD_MAP[k] = bucket


# Load on startup
load_excel()

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return "AR Backend Running Successfully"

# =========================
# UPLOAD EXCEL
# =========================

@app.route("/upload-excel", methods=["POST"])
def upload_excel():

    global KEYWORD_MAP

    try:
        file = request.files["file"]
        file.save(EXCEL_FILE)

        load_excel()

        return jsonify({
            "message": "Excel uploaded successfully",
            "keywords_loaded": len(KEYWORD_MAP)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# GET MAPPING (FOR UI)
# =========================

@app.route("/get-mapping", methods=["GET"])
def get_mapping():

    try:
        if not os.path.exists(EXCEL_FILE):
            return jsonify([])

        df = pd.read_excel(EXCEL_FILE)
        df = df.fillna("")

        return jsonify(df.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# SAVE MAPPING (FROM UI)
# =========================

@app.route("/save-mapping", methods=["POST"])
def save_mapping():

    global KEYWORD_MAP

    try:
        data = request.json

        df = pd.DataFrame(data)
        df.to_excel(EXCEL_FILE, index=False)

        load_excel()

        return jsonify({
            "message": "Mapping updated successfully",
            "rows": len(df)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# MATCH FUNCTION (FIXED BEHAVIOR)
# =========================

def find_bucket_from_excel(text):

    text = text.lower()
    matches = []

    for keyword, bucket in KEYWORD_MAP.items():

        if keyword in text:
            matches.append(bucket)

    if matches:
        return max(set(matches), key=matches.count)

    return None

# =========================
# ANALYZE LOGIC
# =========================

def analyze_correspondence(text):

    text = text.lower()

    excel_bucket = find_bucket_from_excel(text)

    if excel_bucket:
        return {
            "bucket": excel_bucket,
            "a1": "A1: Matched using Excel uploaded rules.",
            "confidence": "98%",
            "keywords": []
        }

    if "return to sender" in text or "bad address" in text:
        return {
            "bucket": "Bad Address",
            "a1": "A1: Bad address detected.",
            "confidence": "97%",
            "keywords": ["Return to Sender", "Bad Address"]
        }

    elif "refund" in text or "overpayment" in text:
        return {
            "bucket": "Refund Request",
            "a1": "A1: Refund request detected.",
            "confidence": "96%",
            "keywords": ["Refund", "Overpayment"]
        }

    elif "denied" in text or "not covered" in text:
        return {
            "bucket": "Denial",
            "a1": "A1: Claim denied.",
            "confidence": "95%",
            "keywords": ["Denied", "Not Covered"]
        }

    return {
        "bucket": "Insurance Bucket",
        "a1": "A1: Requires manual review.",
        "confidence": "85%",
        "keywords": ["Insurance Follow-up"]
    }

# =========================
# ANALYZE API
# =========================

@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():

    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json

    username = data.get("username")
    correspondence = data.get("correspondence")

    if not username or not correspondence:
        return jsonify({"error": "Username and correspondence required"}), 400

    result = analyze_correspondence(correspondence)

    previous_match = find_previous_match(correspondence.lower())

    if previous_match and previous_match["user"] == username:
        previous_match = None

    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    save_history(
        username=username,
        correspondence=correspondence.lower(),
        bucket=result["bucket"],
        a1=result["a1"],
        created_at=current_time
    )

    return jsonify({
        "bucket": result["bucket"],
        "a1": result["a1"],
        "confidence": result["confidence"],
        "keywords": result["keywords"],
        "previous_match": previous_match
    })

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)