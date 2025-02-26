import asyncio
from twikit import Client
from log import NaderLogger
from red import KV

class TWTWorker:
    
    def __init__(self, language='en-US', cookies_file='cookies.json'):
        """
        Initialize the TwitterWorker with a language and cookies file path.
        
        Args:
            language (str): Language code for the Twitter client
            cookies_file (str): Path to store/load cookies for authentication
        """
        self.client = Client(language)
        self.cookies_file = cookies_file
        self.logger = NaderLogger('TWTW', persist=True)
        self.kv = KV()
        
    async def login(self, username, email, password):
        """
        Log in to Twitter using the provided credentials.
        
        Args:
            username (str): Twitter username
            email (str): Email associated with the Twitter account
            password (str): Password for the Twitter account
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            await self.client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password,
                cookies_file=self.cookies_file
            )
            self.logger.info(f"logged in as {username}")
            return True
        except Exception as e:
            self.logger.error(f"login failed: {e}")
            return False
    
    async def uid(self, username):
        return self.kv.get(username) or await self.cuid(username)

    async def cuid(self, username):
        usr = await self.client.get_user_by_screen_name(username)
        uid = usr.id
        self.kv.set(username, uid)
        self.logger.info(f"cached uid for {username}: {uid}")
        return uid


if __name__ == "__main__":
    worker = TWTWorker()
    asyncio.run(
        worker.login(
            username='tester55002',
            email='thewezabisessays@gmail.com',
            password='nadertestingbot'  
        )
    )
    asyncio.run(worker.uid('wizrdware'))