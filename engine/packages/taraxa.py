import os
import csv
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime
from engine.packages.log import Logger
from engine.packages.mongo import MDB

class TaraxaProcessor:
    """
    Processes Telegram message data to enhance the AI agent's understanding of crypto conversations.
    This helps the agent act more like a crypto user who uses Telegram.
    """
    
    def __init__(self):
        self.logger = Logger("taraxa", persist=True)
        self.mdb = MDB()
        self.collection_name = "telegram_insights"
        
    def process_csv(self, csv_path: str) -> Dict[str, Any]:
        """
        Process the Telegram CSV data and extract insights.
        
        Args:
            csv_path (str): Path to the CSV file containing Telegram messages
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted insights
        """
        try:
            self.logger.info(f"Processing Telegram CSV data from: {csv_path}")
            
            # Load CSV data
            df = pd.read_csv(csv_path)
            
            # Basic validation
            required_columns = ['chat_id', 'id', 'date', 'user_id', 'sender_type', 'text', 
                               'member_online_count', 'views', 'replies', 'forwards', 'reply_to_id']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns in CSV: {missing_columns}")
                return {"status": "error", "message": f"Missing columns: {missing_columns}"}
            
            # Process and extract insights
            insights = self._extract_insights(df)
            
            # Store insights in MongoDB
            self._store_insights(insights)
            
            return {"status": "success", "insights": insights}
            
        except Exception as e:
            self.logger.error(f"Error processing Telegram CSV: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _extract_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract insights from the Telegram data.
        
        Args:
            df (pd.DataFrame): DataFrame containing Telegram messages
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted insights
        """
        # Convert date strings to datetime objects
        df['date'] = pd.to_datetime(df['date'])
        
        # Basic statistics
        total_messages = len(df)
        unique_users = df['user_id'].nunique()
        unique_chats = df['chat_id'].nunique()
        
        # Time analysis
        df['hour'] = df['date'].dt.hour
        hourly_activity = df.groupby('hour').size().to_dict()
        
        # Most active users
        most_active_users = df['user_id'].value_counts().head(10).to_dict()
        
        # Most popular chats
        most_popular_chats = df['chat_id'].value_counts().head(10).to_dict()
        
        # Extract common crypto terms and topics
        crypto_terms = self._extract_crypto_terms(df['text'])
        
        # Engagement analysis
        avg_replies = df['replies'].mean()
        avg_views = df['views'].mean()
        avg_forwards = df['forwards'].mean()
        
        # Conversation patterns
        conversation_chains = self._analyze_conversation_chains(df)
        
        # Language patterns
        language_patterns = self._analyze_language_patterns(df['text'])
        
        return {
            "total_messages": total_messages,
            "unique_users": unique_users,
            "unique_chats": unique_chats,
            "hourly_activity": hourly_activity,
            "most_active_users": most_active_users,
            "most_popular_chats": most_popular_chats,
            "crypto_terms": crypto_terms,
            "engagement": {
                "avg_replies": avg_replies,
                "avg_views": avg_views,
                "avg_forwards": avg_forwards
            },
            "conversation_chains": conversation_chains,
            "language_patterns": language_patterns,
            "processed_at": datetime.now().isoformat()
        }
    
    def _extract_crypto_terms(self, texts: pd.Series) -> Dict[str, int]:
        """
        Extract common crypto terms from message texts.
        
        Args:
            texts (pd.Series): Series containing message texts
            
        Returns:
            Dict[str, int]: Dictionary of crypto terms and their frequencies
        """
        # Common crypto terms to look for
        crypto_keywords = [
            "btc", "eth", "bitcoin", "ethereum", "defi", "nft", "dao", "web3",
            "blockchain", "token", "coin", "wallet", "mining", "staking", "yield",
            "airdrop", "smart contract", "solana", "sol", "avax", "avalanche",
            "layer 2", "l2", "rollup", "zk", "zero knowledge", "proof", "consensus",
            "dex", "amm", "liquidity", "pool", "swap", "bridge", "gas", "gwei",
            "metamask", "ledger", "cold wallet", "hot wallet", "private key",
            "public key", "seed phrase", "mnemonic", "block", "transaction",
            "hash", "address", "erc20", "erc721", "eip", "fork", "halving",
            "moon", "hodl", "fud", "fomo", "ath", "atl", "dyor", "ngmi", "wagmi"
        ]
        
        # Count occurrences
        term_counter = Counter()
        
        for text in texts.dropna():
            text_lower = text.lower()
            for term in crypto_keywords:
                if term in text_lower:
                    term_counter[term] += 1
        
        return dict(term_counter.most_common(50))
    
    def _analyze_conversation_chains(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze conversation chains and reply patterns.
        
        Args:
            df (pd.DataFrame): DataFrame containing Telegram messages
            
        Returns:
            Dict[str, Any]: Dictionary containing conversation chain analysis
        """
        # Create a mapping of messages to their replies
        reply_map = defaultdict(list)
        
        for _, row in df.iterrows():
            if not pd.isna(row['reply_to_id']).any():
                reply_map[row['reply_to_id']].append(row['id'])
        
        # Analyze chain lengths
        chain_lengths = []
        for original_id, replies in reply_map.items():
            chain_lengths.append(len(replies))
        
        # Calculate statistics on chain lengths
        if chain_lengths:
            avg_chain_length = sum(chain_lengths) / len(chain_lengths)
            max_chain_length = max(chain_lengths) if chain_lengths else 0
        else:
            avg_chain_length = 0
            max_chain_length = 0
        
        return {
            "avg_chain_length": avg_chain_length,
            "max_chain_length": max_chain_length,
            "total_chains": len(reply_map)
        }
    
    def _analyze_language_patterns(self, texts: pd.Series) -> Dict[str, Any]:
        """
        Analyze language patterns in the messages.
        
        Args:
            texts (pd.Series): Series containing message texts
            
        Returns:
            Dict[str, Any]: Dictionary containing language pattern analysis
        """
        # Common crypto slang and expressions
        crypto_slang = {
            "gm": 0,
            "gn": 0,
            "ser": 0,
            "ser/sir": 0,
            "ngmi": 0,
            "wagmi": 0,
            "lfg": 0,
            "degen": 0,
            "anon": 0,
            "wen": 0,
            "fren": 0,
            "gmi": 0,
            "ape": 0,
            "aping": 0,
            "bullish": 0,
            "bearish": 0,
            "rekt": 0,
            "pump": 0,
            "dump": 0,
            "moon": 0,
            "lambo": 0,
            "chad": 0,
            "based": 0,
            "alpha": 0,
            "beta": 0,
            "dyor": 0,
            "fud": 0,
            "fomo": 0,
            "hodl": 0,
            "paper hands": 0,
            "diamond hands": 0
        }
        
        # Count occurrences
        for text in texts.dropna():
            text_lower = text.lower()
            for slang in crypto_slang:
                if f" {slang} " in f" {text_lower} ":
                    crypto_slang[slang] += 1
        
        # Calculate average message length
        avg_length = texts.dropna().str.len().mean()
        
        # Calculate percentage of messages with emojis (simplified check)
        emoji_count = texts.dropna().str.contains(r'[\U0001F300-\U0001F6FF]').sum()
        emoji_percentage = (emoji_count / len(texts.dropna())) * 100 if len(texts.dropna()) > 0 else 0
        
        return {
            "slang_usage": {k: v for k, v in crypto_slang.items() if v > 0},
            "avg_message_length": avg_length,
            "emoji_percentage": emoji_percentage
        }
    
    def _store_insights(self, insights: Dict[str, Any]) -> None:
        """
        Store the extracted insights in MongoDB.
        
        Args:
            insights (Dict[str, Any]): Dictionary containing extracted insights
        """
        try:
            # Store in MongoDB
            if not self.mdb.client:
                self.logger.error("MongoDB client not initialized")
                return
            db = self.mdb.client["taraxa"]
            db[self.collection_name].insert_one(insights)
            self.logger.info(f"Stored Telegram insights in MongoDB collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Error storing insights in MongoDB: {str(e)}")
    
    def get_insights_for_agent(self) -> Dict[str, Any]:
        """
        Retrieve processed insights to enhance the AI agent's knowledge.
        
        Returns:
            Dict[str, Any]: Dictionary containing insights for the agent
        """
        try:
            # Get the most recent insights
            if not self.mdb.client:
                self.logger.error("MongoDB client not initialized")
                return {}
            
            db = self.mdb.client["taraxa"]
            insights = db[self.collection_name].find_one(
                sort=[("processed_at", -1)]
            )
            
            if not insights:
                self.logger.warning("No Telegram insights found in the database")
                return {}
            
            # Format insights for the agent
            agent_insights = {
                "crypto_terms": insights.get("crypto_terms", {}),
                "language_patterns": insights.get("language_patterns", {}),
                "conversation_style": {
                    "avg_chain_length": insights.get("conversation_chains", {}).get("avg_chain_length", 0),
                    "engagement_metrics": insights.get("engagement", {})
                },
                "activity_patterns": {
                    "hourly_activity": insights.get("hourly_activity", {})
                }
            }
            
            return agent_insights
            
        except Exception as e:
            self.logger.error(f"Error retrieving insights for agent: {str(e)}")
            return {}
    
    def enhance_character(self, character_path: str) -> Dict[str, Any]:
        """
        Enhance the AI agent's character with Telegram insights.
        
        Args:
            character_path (str): Path to the character.json file
            
        Returns:
            Dict[str, Any]: Updated character data
        """
        try:
            # Load character data
            with open(character_path, 'r') as f:
                character = json.load(f)
            
            # Get insights
            insights = self.get_insights_for_agent()
            
            if not insights:
                self.logger.warning("No insights available to enhance character")
                return character
            
            # Enhance topics with popular crypto terms
            if "crypto_terms" in insights and insights["crypto_terms"]:
                top_terms = list(insights["crypto_terms"].keys())[:10]
                character["topics"].extend([term for term in top_terms if term not in character["topics"]])
            
            # Enhance style with language patterns
            if "language_patterns" in insights and "slang_usage" in insights["language_patterns"]:
                top_slang = list(insights["language_patterns"]["slang_usage"].keys())[:5]
                slang_style = f"occasionally use crypto slang like: {', '.join(top_slang)}"
                if slang_style not in character["style"]["chat"]:
                    character["style"]["chat"].append(slang_style)
            
            # Save enhanced character
            with open(character_path, 'w') as f:
                json.dump(character, f, indent=2)
            
            self.logger.info(f"Enhanced character with Telegram insights: {character_path}")
            return character
            
        except Exception as e:
            self.logger.error(f"Error enhancing character: {str(e)}")
            return {}

# Example usage
if __name__ == "__main__":
    processor = TaraxaProcessor()
    
    # Process CSV data
    # result = processor.process_csv("path/to/telegram_data.csv")
    
    # Enhance character
    # processor.enhance_character("engine/agent/character/character.json")
