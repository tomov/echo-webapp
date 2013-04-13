# taken from https://github.com/simonwhitaker/PyAPNs

from apns import APNs, Payload

apns = APNs(use_sandbox=True, cert_file='certificates/EchoAPNDevCert.pem', key_file='certificates/EchoAPNDevKey.pem')

# Send a notification
token_hex = '04c11da985c7e9a615ddc039ce654b76e096db088602e71f8bbfc9fb6d59a91e'
payload = Payload(alert="Someone quoted you!", sound="default", badge=0)
apns.gateway_server.send_notification(token_hex, payload)
