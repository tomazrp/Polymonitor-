import requests
import time

TARGET_WALLET    = "0x44c58184f89a5c2f699dc8943009cb3d75a08d45"
TELEGRAM_TOKEN   = "8368229870:AAGKkCAGUIuxK5j2k8zqdo9mW7d_AoBd60c"
TELEGRAM_CHAT_ID = "959891943"
POLL_INTERVAL    = 30
MIN_VOLUME_USD   = 1000

POLYMARKET_API = "https://clob.polymarket.com"
seen_trade_ids = set()

def get_recent_trades(wallet):
    try:
        r = requests.get(
            f"{POLYMARKET_API}/trades",
            params={"maker_address": wallet, "limit": 20},
            timeout=10
        )
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"[ERRO API] {e}")
        return []

def get_market_name(condition_id):
    try:
        r = requests.get(
            f"https://gamma-api.polymarket.com/markets",
            params={"condition_id": condition_id},
            timeout=10
        )
        data = r.json()
        if data:
            return data[0].get("question", condition_id)
    except:
        pass
    return condition_id

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown"
            }
        )
    except Exception as e:
        print(f"[ERRO TELEGRAM] {e}")

def format_alert(trade, market_name):
    side   = "🟢 COMPROU (YES)" if trade.get("side") == "BUY" else "🔴 VENDEU (NO)"
    price  = float(trade.get("price", 0))
    size   = float(trade.get("size", 0))
    volume = price * size
    odd    = round(1 / price, 2) if price > 0 else 0

    return (
        f"🚨 *@horizonsplendidview ENTROU*\n\n"
        f"{side}\n"
        f"📋 *Mercado:* {market_name[:60]}\n"
        f"💰 *Preço:* `{price:.2f}¢` → Odd: `{odd}`\n"
        f"📦 *Contratos:* `{size:,.0f}`\n"
        f"💵 *Volume:* `${volume:,.2f} USDC`\n"
    )

def run():
    print("🤖 Monitorando @horizonsplendidview...")
    send_telegram("🤖 *Bot iniciado!*\nMonitorando @horizonsplendidview em tempo real.")

    trades = get_recent_trades(TARGET_WALLET)
    for t in trades:
        seen_trade_ids.add(t["id"])
    print(f"✅ {len(seen_trade_ids)} trades carregados. Aguardando novas entradas...\n")

    while True:
        time.sleep(POLL_INTERVAL)
        trades = get_recent_trades(TARGET_WALLET)
        novos  = [t for t in trades if t["id"] not in seen_trade_ids]

        for trade in reversed(novos):
            seen_trade_ids.add(trade["id"])
            price  = float(trade.get("price", 0))
            size   = float(trade.get("size", 0))
            volume = price * size

            if volume < MIN_VOLUME_USD:
                continue

            market_name = get_market_name(trade.get("market", ""))
            msg = format_alert(trade, market_name)
            send_telegram(msg)
            print(f"⚡ Alerta enviado! Volume: ${volume:,.2f}")

if __name__ == "__main__":
    run()
