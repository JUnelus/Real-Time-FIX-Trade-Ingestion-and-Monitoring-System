from kafka import KafkaProducer
import websocket
import json
import threading

def to_fix(trade):
    # Map Binance trade to a simple FIX ExecutionReport message (35=8)
    # NOTE: This is illustrative; you can add more tags as needed!
    fix = (
        "8=FIX.4.2|35=8|49=BINANCE|56=CLIENT12|"
        f"11={trade['t']}|55={trade['s']}|54={1 if trade['m'] else 2}|"
        f"38={trade['q']}|44={trade['p']}|60={trade['T']}|"
        "10=000|"
    )
    return fix.replace('|', '\x01').encode()

def on_message(ws, message):
    msg = json.loads(message)
    if 'data' in msg and 'p' in msg['data']:
        fix_msg = to_fix(msg['data'])
        producer.send('fix-trades', value=fix_msg)
        print("Produced:", fix_msg)

def run_websocket():
    ws = websocket.WebSocketApp(
        "wss://stream.binance.com:9443/ws/btcusdt@trade",
        on_message=on_message
    )
    ws.run_forever()

if __name__ == "__main__":
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    # Use a thread so you can Ctrl+C cleanly
    t = threading.Thread(target=run_websocket, daemon=True)
    t.start()
    print("Started real-time Binance WebSocket → FIX → Kafka producer.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down.")
