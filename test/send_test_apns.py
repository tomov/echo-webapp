# taken from https://github.com/simonwhitaker/PyAPNs
# just sends a test notification to rishi to make sure it works (sorry rishi)
import sys

sys.path.append('..') # hack to be able to import files from parent directory without messing with modules
from apns import APNs, Payload

apns = APNs(use_sandbox=False, cert_file='../certificates/EchoAPNSProdCert.pem', key_file='../certificates/newEchoAPNSProdKey.pem')

# Send a notification
#token_hex1 = '04c11da985c7e9a615ddc039ce654b76e096db088602e71f8bbfc9fb6d59a91e' # rishi's phone
token_hex1 = '884a19da5dc0a72d8aecb5ad6fe7ee2e49e9d8aacd618aedb785f067cb114de1' # rishi's phone 2
#token_hex1 = 'a40a3af5b674bc891614ecaf7a4d528150264e90a2dc1b16756148e14d41be64' # jacob's
#token_hex1 = '5093a4269fb4065bd70b6e23aed3f40b8978e1335cd0b889c9ed99c6c2d30631' # chris
#token_hex1 = 'a6f283a5eff9cd231efb1980558795a0443833d5d6470b61e972c8f786b9ae3f' # juan
token_hex1 = 'a951d8aba5ec3532edc6426583681e3749e2b71c9e1724219897382efd8154b0' # momchil
#payload = Payload(alert="Someone quoted you!", sound="default", badge=1)
payload = Payload(alert="This is a test notification. Please disregard.", sound="default", badge=69)
apns.gateway_server.send_notification(token_hex1, payload)
