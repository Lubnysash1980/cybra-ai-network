import time
import traceback
import requests
import hmac
import hashlib

# =========================
# CYBRA CLASSES
# =========================

class Config:
    BASE = "https://api.bybit.com"
    SYMBOL = "BTCUSDT"
    CATEGORY = "spot"
    QTY = "0.001"
    LOOP = 2
    WINDOW = 20
    BUY_THRESHOLD = 1.001
    SELL_THRESHOLD = 0.999


class CybraMarket:
    def price(self):
        try:
            r = requests.get(
                Config.BASE + "/v5/market/tickers",
                params={
                    "category": Config.CATEGORY,
                    "symbol": Config.SYMBOL
                },
                timeout=3
            )
            return float(r.json()["result"]["list"][0]["lastPrice"])
        except Exception as e:
            print("[MARKET ERROR]", e)
            return None


class CybraStrategy:
    def __init__(self):
        self.buf = []

    def signal(self, price):
        self.buf.append(price)

        if len(self.buf) > Config.WINDOW:
            self.buf.pop(0)

        avg = sum(self.buf) / len(self.buf)

        if price > avg * Config.BUY_THRESHOLD:
            return "Buy"

        if price < avg * Config.SELL_THRESHOLD:
            return "Sell"

        return "Hold"


class CybraExchange:
    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret

    def sign(self, payload):
        q = "&".join([f"{k}={v}" for k, v in sorted(payload.items())])
        return hmac.new(
            self.secret.encode(),
            q.encode(),
            hashlib.sha256
        ).hexdigest()

    def order(self, side):
        ts = str(int(time.time() * 1000))

        payload = {
            "category": Config.CATEGORY,
            "symbol": Config.SYMBOL,
            "side": side,
            "orderType": "Market",
            "qty": Config.QTY,
            "timestamp": ts
        }

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": self.sign(payload),
            "X-BAPI-TIMESTAMP": ts
        }

        try:
            r = requests.post(
                Config.BASE + "/v5/order/create",
                data=payload,
                headers=headers,
                timeout=5
            )
            print("[ORDER]", r.json())
        except Exception as e:
            print("[ORDER ERROR]", e)


class AutoHeal:
    def __init__(self):
        self.crashes = 0

    def protect(self, fn):
        while True:
            try:
                fn()
            except KeyboardInterrupt:
                print("\n[CYBRA STOPPED]")
                break
            except Exception:
                self.crashes += 1
                print("[AUTOHEAL] crash:", self.crashes)
                traceback.print_exc()
                time.sleep(3)


class Cybra:
    def __init__(self):
        print("====================================")
        print(" CYBRA CLASS ENGINE + AUTOHEAL")
        print("====================================")

        api = input("BYBIT API KEY: ").strip()
        sec = input("BYBIT SECRET KEY: ").strip()

        self.market = CybraMarket()
        self.strategy = CybraStrategy()
        self.exchange = CybraExchange(api, sec)

    def run(self):
        print("\n[CYBRA ACTIVE]\n")

        while True:
            p = self.market.price()

            if not p:
                print("[WAIT PRICE]")
                time.sleep(Config.LOOP)
                continue

            sig = self.strategy.signal(p)

            print("[PRICE]", p, "[SIGNAL]", sig)

            if sig in ["Buy", "Sell"]:
                self.exchange.order(sig)

            time.sleep(Config.LOOP)


# =========================
# IMPORT CYBRA ENTRY
# =========================

def run():
    AutoHeal().protect(lambda: Cybra().run())


if __name__ == "__main__":
    run()
