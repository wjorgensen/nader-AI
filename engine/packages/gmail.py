import imaplib
import email
import os
from dotenv import load_dotenv
import asyncio

from log import Logger
from red import Red

load_dotenv()


class GmailWorker:
    def __init__(self, imap_url="imap.gmail.com"):
        """
        Initialize the GmailWorker with server details.

        Args:
            imap_url (str): IMAP server URL
        """
        self.username = os.getenv("GMAIL") or ""
        self.password = os.getenv("GMAIL_PASSWORD") or ""
        self.imap_url = imap_url
        self.logger = Logger("GMAIL", persist=True)
        self.mail = None

    async def connect(self):
        """
        Connect and log in to Gmail using credentials from environment variables.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to Gmail as {self.username}")
            # IMAP is not async, but we'll wrap it in an async function for consistency
            self.mail = imaplib.IMAP4_SSL(self.imap_url)
            self.mail.login(self.username, self.password)
            self.logger.info(f"Connected to Gmail as {self.username}")
            self.red = Red()
            return True
        except Exception as e:
            self.logger.error(f"Gmail connection failed: {e}")
            return False

    def logout(self):
        """
        Logout from the Gmail account.
        """
        if self.mail:
            self.mail.logout()
            self.logger.info("Logged out from Gmail")


if __name__ == "__main__":
    worker = GmailWorker()
