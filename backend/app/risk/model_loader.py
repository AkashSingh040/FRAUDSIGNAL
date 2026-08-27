import os
import joblib
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "fraud_model.pkl")
METADATA_PATH = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
THRESHOLD_CONFIG_PATH = os.path.join(ARTIFACTS_DIR, "threshold_config.json")

class FraudModelLoader:
    def __init__(self):
        self.model = None
        self.features = []
        self.cat_cols = []
        self.freq_maps = {}
        self.metadata = None
        self.optimal_threshold = 0.5
        self.is_loaded = False
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(METADATA_PATH):
            try:
                # Load LightGBM model artifact
                artifact = joblib.load(MODEL_PATH)
                self.model = artifact["model"]
                self.features = artifact["features"]
                self.cat_cols = artifact["cat_cols"]
                self.freq_maps = artifact["freq_maps"]
                
                # Load metadata
                with open(METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
                    
                # Load threshold config
                if os.path.exists(THRESHOLD_CONFIG_PATH):
                    with open(THRESHOLD_CONFIG_PATH, "r") as f:
                        config = json.load(f)
                        self.optimal_threshold = config.get("optimal_threshold", 0.5)
                        
                self.is_loaded = True
                logger.info(f"Loaded Fraud Model: {self.metadata.get('model_name')} {self.metadata.get('model_version')} | Threshold: {self.optimal_threshold}")
            except Exception as e:
                logger.error(f"Failed to load model: {e}", exc_info=True)
        else:
            logger.warning("Model artifacts not found. Operating in RULES-ONLY mode.")

    def get_status(self) -> Dict[str, Any]:
        if self.is_loaded and self.metadata:
            return {
                "trained": True,
                "model_name": self.metadata.get("model_name"),
                "version": self.metadata.get("model_version"),
                "dataset": self.metadata.get("dataset"),
                "roc_auc": self.metadata.get("roc_auc"),
                "pr_auc": self.metadata.get("pr_auc"),
                "precision": self.metadata.get("precision"),
                "recall": self.metadata.get("recall"),
                "f1": self.metadata.get("f1"),
                "threshold": self.optimal_threshold,
                "feature_count": self.metadata.get("feature_count"),
                "trained_at": self.metadata.get("trained_at")
            }
        return {
            "trained": False,
            "dataset": "IEEE-CIS Fraud Detection",
            "message": "Model not trained. Using deterministic rules."
        }

    def _extract_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Maps a NormalizedTransaction to the IEEE-CIS feature space dynamically."""
        # Base features
        amount = transaction.get('amount', 0)
        timestamp_str = transaction.get('timestamp')
        
        # Parse timestamp to get hour and day (simulating time-based offset)
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            hour = dt.hour
            # Dummy day extraction since IEEE-CIS is based on an unknown reference date
            # We'll use day of year as a proxy
            day = dt.timetuple().tm_yday
        except:
            hour = 12
            day = 1
            
        metadata = transaction.get('metadata', {})
        
        raw_features = {
            'TransactionAmt': amount,
            'LogTransactionAmt': np.log1p(amount),
            'hour': hour,
            'day': day,
            'card1': metadata.get('card_bin', 0),
            'card2': metadata.get('card2', 0),
            'card3': metadata.get('card3', 150),
            'card5': metadata.get('card5', 226),
            'addr1': metadata.get('addr1', 0),
            'addr2': metadata.get('addr2', 87),
            'dist1': metadata.get('dist1', 0),
            'ProductCD': metadata.get('product_cd', 'W'),
            'card4': metadata.get('card_brand', 'visa'),
            'card6': metadata.get('card_type', 'credit'),
            'P_emaildomain': metadata.get('email_domain', 'gmail.com'),
            'R_emaildomain': metadata.get('r_email_domain', 'missing')
        }
        
        # Add frequency encoded features
        for col in ['card1', 'card2', 'addr1', 'P_emaildomain']:
            val = raw_features[col]
            # Lookup freq, fallback to 0 if unseen
            freq = self.freq_maps.get(col, {}).get(val, 0.0)
            raw_features[f'{col}_count'] = freq
            
        # Add missing V features (default to 0 or median)
        for i in range(1, 15):
            raw_features[f'V{i}'] = metadata.get(f'V{i}', 0)
            
        return raw_features

    def predict(self, transaction: Dict[str, Any]) -> Optional[float]:
        if not self.is_loaded or not self.model:
            return None
        
        try:
            raw_features = self._extract_features(transaction)
            
            # Construct DataFrame matching exact training feature order
            df = pd.DataFrame([raw_features])[self.features]
            
            # Cast categorical columns
            for col in self.cat_cols:
                df[col] = df[col].astype(str).fillna('missing').astype('category')
                
            prob = self.model.predict_proba(df)[0][1]
            return float(prob)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

model_loader = FraudModelLoader()
