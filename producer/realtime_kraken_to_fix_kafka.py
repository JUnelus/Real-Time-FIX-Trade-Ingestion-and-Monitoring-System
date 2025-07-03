import websocket
import json
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:9092')

def to_fix(trade):
    # trade is a list: [price, volume, time, side, order type, misc]
    price, volume, tstamp, side, ordertype, misc = trade
    fix = (
        "8=FIX.4.2|35=8|49=KRAKEN|56=CLIENT12|"
        f"11={int(float(tstamp)*1e6)}|55=BTC/USD|54={'1' if side == 'b' else '2'}|"
        f"38={volume}|44={price}|60={tstamp}|"
        "10=000|"
    )
    return fix.replace('|', '\x01').encode()

def on_message(ws, message):
    msg = json.loads(message)
    if isinstance(msg, list) and msg[1] == 'trade':
        for trade in msg[2]:
            fix_msg = to_fix(trade)
            producer.send('fix-trades', value=fix_msg)
            print("Produced:", fix_msg)

def on_open(ws):
    ws.send(json.dumps({
        "event": "subscribe",
        "pair": ["XBT/USD"],
        "subscription": {"name": "trade"}
    }))

ws = websocket.WebSocketApp(
    "wss://ws.kraken.com/",
    on_open=on_open,
    on_message=on_message
)
ws.run_forever()