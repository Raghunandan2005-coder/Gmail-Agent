import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import base64
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import time
SCOPES =['https://www.googleapis.com/auth/gmail.readonly']



# Slack function

def send_to_slack(message):
    webhook_url="https://hooks.slack.com/services/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"


    payload={
        "text":message
    }

    requests.post(webhook_url,json=payload)


# AUTH
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

creds=Credentials.from_authorized_user_file('token.json',SCOPES)
service=build('gmail','v1',credentials=creds)
print("service created!")

results=service.users().messages().list(userId='mustipallilakshmiraghunandan@gmail.com',maxResults=30).execute()
print("API called")
messages=results.get('messages',[])

print("Total Emails:",len(messages))

# stores Mails
important_mails=[]
seen_subjects=set()

# Loop through Mails
for msg in messages:
    msg_id=msg['id']

    # get full Email
    email=service.users().messages().get(userId='mustipallilakshmiraghunandan@gmail.com',id=msg_id).execute()
    headers=email['payload']['headers']
    print(type(email))
    subject=""
    sender=""

   # Extract subject and sender
    headers=email['payload']['headers']
    header_dict={h['name']:h['value'] for h in headers}
    subject=header_dict.get('Subject','No Subject')
    # skipping Duplicate subjects
    if subject in seen_subjects:
        continue
    seen_subjects.add(subject)
    
    sender=header_dict.get('From','No Sender')

    print("\n Email:")
    print("Subject:",subject)
    print("From:",sender)

    # extracting body
    body=""

    try:
        body_data=email['payload']['body']['data']
        if body_data:
            body=base64.urlsafe_b64decode(body_data).decode('utf-8')
    except:
        body ="No body found"

    print("Body:",body[:200])

    # clean HTML
    soup = BeautifulSoup(body, "html.parser")
    clean_text = soup.get_text()
    print("Body:", clean_text[:200])

    # Prority Detection
    important_keywords=["job","interview","offer","alert","Security","payment","due","alert","verification"]
    medium_keywords=["job","meeting","update"]
    important_senders = [
    "accounts.google.com",
    "bank",
    "tcsion.com",
    "alerts",
    "no-reply"
]
    text=(subject+ ""+clean_text).lower()
    sender_lower=sender.lower()
    if any(word in text for word in important_keywords)or\
       any(s in sender_lower for s in important_senders):
         priority="HIGH PRIORITY"
    elif any(word in text for word in medium_keywords):
         priority="MEDIUM PRIORITY"
    else:
         priority="LOW PRIORITY"

    print("Priority:",priority)

# Reply Detection
thread_id = email['threadId']
thread=service.users().threads().get(userId='mustipallilakshmiraghunandan@gmail.com',id=thread_id).execute()
messages_in_thread=thread['messages']
replied=False

for m in messages_in_thread:
    headers=m['payload']['headers']
    headers_dict={h['name']:h['value'] for h in headers}

    from_field=headers_dict.get('From','').lower()
    MY_EMAIL="mustipallilakshmiraghunandan@gmail.com"
    if MY_EMAIL in from_field:
        replied= True
        break
        
print("Replied:",replied)

# Store only if impotant & not replied
if priority == "HIGH PRIORITY" and not replied:
   print("Important Email & Not Replied")
   print("Subject:",subject)
   print("From:",sender)
   # Slack call
   msg=f"""Important Email!\n subject:{subject}\nFrom:{sender}
         Subject: {subject}
         From:  {sender}
         Time:{datetime.now().strftime('%H:%M:%S')}"""
         
   send_to_slack(msg)
   # Store
   mail_data={
       "subject": subject,
       "sender":sender,
       "time":datetime.now(),
       "alerted":False
    }
   important_mails.append(mail_data)

                           
elif priority=="MEDIUM PRIORITY":
    print("\n check after 1 hour later")
    print("Subject:" ,subject)
else:
    print("\n check when ever you are free")
    print("subject:",subject)

#  Monitoring loop
print("\n Monitoring for delayed Emails....\n")

while True:
   for mail in important_mails:
      if not mail["alerted"]and datetime.now()-mail["time"]>timedelta(seconds=10):
       print("Alert : NO response for important mail!",mail["subject"])
       print("subject:",mail["subject"])
       print("From:",mail["sender"])
       print("checking emails..")
       mail["alerted"]=True
       
   time.sleep(30)


