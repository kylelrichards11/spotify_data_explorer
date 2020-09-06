import pickle
import base64
import os.path
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file gmail_creds.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class Gmail():
    """ A class to send emails from gmail account """
    def __init__(self):
        self.address_from = "pythontextnotif@gmail.com"
        self.address_to = "kyleredsox11@gmail.com"
        self.service = self._auth()

    def _auth(self):
        """ Authenticates with gmail

        Parameters
        ----------
        None

        Returns
        -------
        gmail auth object
        """
        creds = None
        # The file gmail_creds.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('gmail_creds.pickle'):
            with open('gmail_creds.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('gmail_creds.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('gmail', 'v1', credentials=creds)
        return service

    def send_message(self, message):
        """Sends a message.

        Parameters
        ----------
        message : str - the message to send

        Returns
        -------
        None
        """
        message = MIMEText(message)
        message['to'] = self.address_to
        message['from'] = self.address_from
        message['subject'] = "Listen Error"
        message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        self.service.users().messages().send(userId="me", body=message).execute()

if __name__ == "__main__":
    gmail = Gmail()
    gmail.send_message("Test Message")
