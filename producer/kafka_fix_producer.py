from kafka import KafkaProducer
import time

# Sample FIX messages (NewOrderSingle, ExecutionReport)
messages = [
    "8=FIX.4.2|35=D|49=CLIENT12|56=BROKER12|34=215|52=20190605-19:41:57.316|11=12345|21=1|55=BTCUSD|54=1|38=10|40=2|44=10000.0|10=072|",
    "8=FIX.4.2|35=8|49=BROKER12|56=CLIENT12|34=216|52=20190605-19:41:58.316|11=12345|17=1|20=0|150=0|39=0|55=BTCUSD|54=1|38=10|44=10000.0|10=157|"
]

def to_fix(msg):
    return msg.replace('|', '\x01').encode()

producer = KafkaProducer(bootstrap_servers='localhost:9092')

while True:
    for msg in messages:
        producer.send('fix-trades', value=to_fix(msg))
        print("Produced:", msg)
        time.sleep(2)
