import ssl
from app import create_app

app = create_app()

if __name__ == '__main__':
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('instance/certs/cert.pem', 'instance/certs/key.pem')
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=ssl_context)
