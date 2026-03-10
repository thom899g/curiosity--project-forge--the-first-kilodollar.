#!/usr/bin/env python3
"""
Generate synthetic training data for initial ML model training.
This creates a realistic dataset of wallet behaviors for pattern recognition.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generate synthetic but realistic crypto transaction data"""
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.behavior_patterns = {
            'accumulator': {
                'tx_value_mean': 50000,
                'tx_value_std': 10000,
                'frequency': 0.3,
                'destinations': ['DEX', 'EOA'] * 8 + ['CEX'] * 2
            },
            'distributor': {
                'tx_value_mean': 20000,
                'tx_value_std': 5000,
                'frequency': 0.4,
                'destinations': ['CEX'] * 7 + ['DEX', 'Contract'] * 3
            },
            'liquidity_provider': {
                'tx_value_mean': 100000,
                'tx_value_std': 30000,
                'frequency': 0.2,
                'destinations': ['DEX'] * 9 + ['Contract'] * 1
            },
            'arbitrageur': {
                'tx_value_mean': 15000,
                'tx_value_std': 5000,
                'frequency': 0.1,
                'destinations': ['DEX'] * 10
            }
        }
    
    def generate_wallet_address(self) -> str:
        """Generate synthetic Ethereum address"""
        hex_chars = '0123456789abcdef'
        return '0x' + ''.join(self.rng.choice(list(hex_chars), size=40))
    
    def generate_timestamp_series(self, n: int, start_date: str = "2024-01-01") -> List[datetime]:
        """Generate realistic timestamps with patterns"""
        base = pd.Timestamp(start_date)
        # Create some clustering (transactions often happen in bursts)
        clusters = self.rng.integers(0, n//10, size=n)
        hours = self.rng.exponential(24, size=n)  # Most within 24h
        minutes = self.rng.normal(0, 30, size=n)
        
        timestamps = []
        for i in range(n):
            days = clusters[i] // 10
            hour = int(hours[i]) % 24
            minute = max(0, min(59, int(minutes[i])))
            timestamp = base + timedelta(days=days, hours=hour, minutes=minute)
            timestamps.append(timestamp)
        
        return sorted(timestamps)
    
    def generate_transaction_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate comprehensive transaction dataset"""
        logger.info(f"Generating {n_samples} synthetic transaction records")
        
        # Initialize lists for each column
        data = {
            'transaction_hash': [],
            'wallet_address': [],
            'transaction_value_eth': [],
            'transaction_value_usd': [],
            'timestamp': [],
            'destination_type': [],
            'behavior_pattern': [],
            'gas_used': [],
            'gas_price_gwei': [],
            'success': [],
            'contract_interaction': [],
            'input_data_length': []
        }
        
        # Generate wallet addresses (reuse some for patterns)
        n_wallets = max(50, n_samples // 200)
        wallets = [self.generate_wallet_address() for _ in range(n_wallets)]
        
        # Assign behaviors to wallets
        behaviors = list(self.behavior_patterns.keys())
        wallet_behaviors = {
            wallet: self.rng.choice(behaviors, p=[0.3, 0.4, 0.2, 0.1])
            for wallet in wallets
        }
        
        # Generate timestamps
        timestamps = self.generate_timestamp_series(n_samples)
        
        for i in range(n_samples):
            # Select wallet
            wallet = self.rng.choice(wallets)
            behavior = wallet_behaviors[wallet]
            pattern_config = self.behavior_patterns[behavior]
            
            # Generate transaction hash
            tx_hash = '0x' + ''.join(self.rng.choice(list('0123456789abcdef'), size=64))
            
            # Generate transaction value based on behavior
            tx_value_eth = max(0.1, self.rng.normal(
                pattern_config['tx_value_mean'],
                pattern_config['tx_value_std']
            ))
            
            # USD value with some variation
            eth_price = self.rng.uniform(2500, 3500)
            tx_value_usd = tx_value_eth * eth_price
            
            # Destination type based on behavior
            dest_type = self.rng.choice(pattern_config['destinations'])
            
            # Gas usage
            gas_used = self.rng.integers(21000, 500000)
            gas_price = self.rng.uniform(20, 150)
            
            # Contract interaction (more likely for certain destinations)
            is_contract = dest_type in ['Contract', 'DEX']
            input_length = self.rng.integers(0, 1000) if is_contract else 0
            
            # Success rate (95% success)
            success = self.rng.random() > 0.05
            
            # Populate data
            data['transaction_hash'].append(tx_hash)
            data['wallet_address'].append(wallet)
            data['transaction_value_eth'].append(tx_value_eth)
            data['transaction_value_usd'].append(tx_value_usd)
            data['timestamp'].append(timestamps[i])
            data['destination_type'].append(dest_type)
            data['behavior_pattern'].append(behavior)
            data['gas_used'].append(gas_used)
            data['gas_price_gwei'].append(gas_price)
            data['success'].append(success)
            data['contract_interaction'].append(is_contract)
            data['input_data_length'].append(input_length)
        
        df = pd.DataFrame(data)
        
        # Add derived features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['value_category']