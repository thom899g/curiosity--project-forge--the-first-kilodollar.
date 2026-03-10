"""
Configuration management for Nexus Intelligence Core.
Handles environment variables, validation, and defaults.
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """Configuration for data source APIs"""
    alchemy_eth_api_key: str
    alchemy_polygon_api_key: str
    infura_api_key: str
    moralis_api_key: str
    consensus_threshold: int = 2
    
    def validate(self) -> bool:
        """Validate that required API keys are present"""
        required_keys = [
            ('Alchemy Ethereum', self.alchemy_eth_api_key),
            ('Infura', self.infura_api_key),
            ('Moralis', self.moralis_api_key)
        ]
        
        missing = [name for name, key in required_keys if not key]
        if missing:
            logger.error(f"Missing API keys: {', '.join(missing)}")
            return False
        
        if self.consensus_threshold < 1 or self.consensus_threshold > 3:
            logger.error(f"Invalid consensus threshold: {self.consensus_threshold}")
            return False
            
        return True


@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    credentials_path: Path
    project_id: str
    firestore_collection_prefix: str = "nexus_v1"
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        if not self.credentials_path.exists():
            logger.error(f"Firebase credentials not found at: {self.credentials_path}")
            return False
        
        if not self.project_id:
            logger.error("Firebase project ID is required")
            return False
            
        return True


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    developer_chat_id: str
    max_message_length: int = 4096
    
    def validate(self) -> bool:
        """Validate Telegram configuration"""
        if not self.bot_token:
            logger.error("Telegram bot token is required")
            return False
        return True


@dataclass
class StripeConfig:
    """Stripe payment configuration"""
    secret_key: str
    webhook_secret: str
    publishable_key: str
    webhook_endpoint: str = "/stripe/webhook"
    
    def validate(self) -> bool:
        """Validate Stripe configuration"""
        if not self.secret_key or not self.webhook_secret:
            logger.error("Stripe keys are required")
            return False
        return True


@dataclass
class TreasuryConfig:
    """Treasury configuration for revenue allocation"""
    wallet_address: str
    usdc_contract_address: str = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # Mainnet USDC
    min_transfer_amount: float = 100.0  # Minimum $100 for gas efficiency
    
    def validate(self) -> bool:
        """Validate treasury configuration"""
        if not self.wallet_address or not self.wallet_address.startswith("0x"):
            logger.error("Valid treasury wallet address required")
            return False
        return True


@dataclass
class OperationalConfig:
    """Operational configuration"""
    log_level: str = "INFO"
    max_retries: int = 3
    request_timeout: int = 30
    data_retention_days: int = 30
    
    def get_log_level(self) -> int:
        """Convert string log level to logging constant"""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(self.log_level.upper(), logging.INFO)


@dataclass
class NexusConfig:
    """Main configuration container"""
    data_sources: DataSourceConfig
    firebase: FirebaseConfig
    telegram: TelegramConfig
    stripe: StripeConfig
    treasury: TreasuryConfig
    operational: OperationalConfig = field(default_factory=OperationalConfig)
    
    @classmethod
    def from_env(cls) -> 'NexusConfig':
        """Load configuration from environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Operational config
        op_config = OperationalConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            data_retention_days=int(os.getenv("DATA_RETENTION_DAYS", "30"))
        )
        
        # Data sources
        data_config = DataSourceConfig(
            alchemy_eth_api_key=os.getenv("ALCHEMY_API_KEY_ETH", ""),
            alchemy_polygon_api_key=os.getenv("ALCHEMY_API_KEY_POLYGON", ""),
            infura_api_key=os.getenv("INFURA_API_KEY", ""),
            moralis_api_key=os.getenv("MORALIS_API_KEY", ""),
            consensus_threshold=int(os.getenv("CONSENSUS_THRESHOLD", "2"))
        )
        
        # Firebase
        creds_path = Path(os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json"))
        firebase_config = FirebaseConfig(
            credentials_path=creds_path,
            project_id=os.getenv("FIREBASE_PROJECT_ID", "")
        )
        
        # Telegram
        telegram_config = TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            developer_chat_id=os.getenv("TELEGRAM_DEVELOPER_CHAT_ID", "")
        )
        
        # Stripe
        stripe_config = StripeConfig(
            secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
            publishable_key=os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        )
        
        # Treasury
        treasury_config = TreasuryConfig(
            wallet_address=os.getenv("TREASURY_WALLET_ADDRESS", ""),
            min_transfer_amount=float(os.getenv("MIN_TRANSFER_AMOUNT", "100.0"))
        )
        
        return cls(
            data_sources=data_config,
            firebase=firebase_config,
            telegram=telegram_config,
            stripe=stripe_config,
            treasury=treasury_config,
            operational=op_config
        )
    
    def validate_all(self) -> bool:
        """Validate all configurations"""
        validations = [
            ("Data Sources", self.data_sources.validate()),
            ("Firebase", self.firebase.validate()),
            ("Telegram", self.telegram.validate()),
            ("Stripe", self.stripe.validate()),
            ("Treasury", self.treasury.validate())
        ]
        
        failed = [name for name, is_valid in validations if not is_valid]
        
        if failed:
            logger.error(f"Configuration validation failed for: {', '.join(failed)}")
            return False
        
        logger.info("All configurations validated successfully")
        return True


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the entire application"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('nexus.log', encoding='utf-8')
        ]
    )
    logger.info(f"Logging configured at level: {logging.getLevelName(log_level)}")