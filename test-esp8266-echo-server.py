from server.esp8266conn import pulley

ply = pulley(
        **{'ip': '10.0.0.38',
           'port': 8181,
           'buf_size': 124}
    )

print(ply.getcurrentloc())