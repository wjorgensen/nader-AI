import asyncio
import os
from twikit import Client

from engine.packages.log import Logger
from engine.packages.red import Red


class TWTW:
    def __init__(self, language="en-US", cookies_file=None):
        """
        Initialize the TwitterWorker with a language and cookies file path.

        Args:
            language (str): Language code for the Twitter client
            cookies_file (str, optional): Path to store/load cookies for authentication.
            If None, defaults to cookies.json in the engine/cookies directory.
        """
        # Get the absolute path to the project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        # Set default cookies path if not provided
        if cookies_file is None:
            cookies_file = os.path.join(project_root, "engine", "cookies", "cookies.json")
        # If a relative path is provided, make it absolute from the project root
        elif not os.path.isabs(cookies_file):
            cookies_file = os.path.join(project_root, cookies_file)
            
        print(cookies_file)
        self.client = Client(language)
        self.cookies_file = cookies_file
        print(self.cookies_file)
        self.logger = Logger("TWTW", persist=True)
        self.kv = Red()

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
            self.logger.info(f"logging in as {username}")
            await self.client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password,
                cookies_file=self.cookies_file,
            )
            self.logger.info(f"logged in as {username}")
            return True
        except Exception as e:
            self.logger.error(f"login failed: {e}")
            return False
        
    def ping(self):
        return self.client.get_cookies()

    async def uid(self, username):
        return self.kv.red.get(username) or await self.cuid(username)

    async def cuid(self, username) -> str:
        usr = await self.client.get_user_by_screen_name(username)
        uid = usr.id
        self.kv.red.set(username, uid)
        self.logger.info(f"cached uid for {username}: {uid}")
        return uid

    async def dump(self, username):
        """
        Get detailed user information by username.
        
        Args:
            username (str): Twitter username
            
        Returns:
            dict: User information dictionary
        """
        try:
            uid = await self.uid(username)
            usr = await self.client.get_user_by_id(str(uid))
            return usr.__dict__
        except Exception as e:
            self.logger.error(f"Failed to dump user data for {username}: {e}")
            return {"error": str(e)}

    async def dm(self, username, text):
        """
        Send a direct message to a user by username.
        
        Args:
            username (str): Twitter username to send DM to
            text (str): Message content
            
        Returns:
            dict: Result of the DM operation or error information
        """
        try:
            uid = await self.uid(username)
            self.logger.info(f"Sending DM to {username} (ID: {uid})")
            result = await self.client.send_dm(user_id=str(uid), text=text)
            self.logger.info(f"DM sent successfully to {username}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to send DM to {username}: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    print(os.getcwd())
    
    async def main():
        worker = TWTW()
        await worker.login(
            username=os.getenv("TWITTER_USERNAME"),
            email=os.getenv("TWITTER_EMAIL"),
            password=os.getenv("TWITTER_PASSWORD"),
        )
        user_id = await worker.uid("wezabis")
        print(user_id)
        user_data = await worker.dump("wezabis")
        print(user_data)
        dm_result = await worker.dm("wezabis", "Hello from NaderAI!")
        print(dm_result)
    
    asyncio.run(main())
