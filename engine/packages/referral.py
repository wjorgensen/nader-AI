import secrets
import string
from typing import List, Optional
from datetime import datetime
from engine.packages.mongo import MDB

class ReferralSystem:
    def __init__(self):
        self.mdb = MDB()
        self.mdb.connect()
        self.WEZABIS_CODE = "joinTheNetwork"  # Permanent unlimited code for wezabis
        
    def generate_code(self, length: int = 8) -> str:
        """Generate a random referral code"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_referral_codes(self, count: int = 3) -> List[str]:
        """Generate multiple unique referral codes"""
        codes = []
        for _ in range(count):
            while True:
                code = self.generate_code()
                # Check if code already exists
                if not self.mdb.client["network"]["referrals"].find_one({"code": code}):
                    codes.append(code)
                    # Store the new code in database
                    self.mdb.client["network"]["referrals"].insert_one({
                        "code": code,
                        "used": False,
                        "created_at": datetime.now()
                    })
                    break
        return codes
    
    async def verify_referral(self, referrer_username: str, code: str) -> Optional[dict]:
        """Verify a referral code and mark it as used if valid"""
        if not self.mdb.client:
            return None
            
        # Clean up username (remove @ if present)
        clean_username = referrer_username.replace("@", "").lower()
            
        # Check for wezabis - accept any code for wezabis
        if clean_username == "wezabis":
            # For wezabis, any code works
            return {
                "telegram_username": "wezabis",
                "is_permanent": True
            }
            
        # Find the referrer
        referrer = self.mdb.client["network"]["people"].find_one({
            "telegram_username": clean_username
        })
        
        if not referrer:
            return None
            
        # Check if code exists and is unused
        referral = self.mdb.client["network"]["referrals"].find_one({
            "code": code,
            "used": False
        })
        
        if not referral:
            return None
            
        # Mark code as used (unless it's the permanent code)
        if code != self.WEZABIS_CODE:
            self.mdb.client["network"]["referrals"].update_one(
                {"code": code},
                {
                    "$set": {
                        "used": True,
                        "used_at": datetime.now()
                    }
                }
            )
            
        return referrer 