#!/usr/bin/env python3

import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('foobar.crt', 'foobar.key')

from app import app
#app.run(debug=True, host='0.0.0.0')
app.run(debug=True, host='0.0.0.0', ssl_context=context)
