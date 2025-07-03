def parse_fix_message(raw_message):
    # Split by SOH delimiter
    fields = raw_message.decode().split('\x01')
    parsed = {}
    for field in fields:
        if '=' in field:
            k, v = field.split('=', 1)
            parsed[k] = v
    return parsed

# Example usage:
# parsed = parse_fix_message(b"8=FIX.4.2\x0135=D\x01...")
