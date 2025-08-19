#!/usr/bin/env python3
"""
SNS Event Publisher - AWS Event System
=====================================

This file sends events to AWS SNS when stock data is updated.
It handles:
- Sending notifications when new stock data arrives
- Event formatting and validation
- AWS SNS connection management
- Error handling and retries

Think of this as the "messenger" that tells other services when new data is available.
"""

import boto3
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from config.config_manager import config
import logging

logger = logging.getLogger(__name__)

class SNSPublisher:
    """Publisher for SNS events"""
    
    def __init__(self):
        self.sns_client = boto3.client(
            'sns',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            aws_session_token=config.AWS_SESSION_TOKEN,
            region_name=config.AWS_REGION
        )
        self.topic_arn = config.SNS_TOPIC_ARN
    
    def publish_stock_data_loaded(self, symbol: str, records_count: int, latest_date: str = None) -> bool:
        """
        Publish event when stock data is loaded
        
        Args:
            symbol: Stock symbol
            records_count: Number of records loaded
            latest_date: Latest date in the data
            
        Returns:
            True if published successfully
        """
        event = {
            "event_type": "stock_data_loaded",
            "symbol": symbol,
            "records_count": records_count,
            "latest_date": latest_date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Stock data loaded for {symbol}: {records_count} records"
        }
        
        return self._publish_event(event)
    
    def publish_company_info_updated(self, symbol: str, company_name: str = None) -> bool:
        """
        Publish event when company info is updated
        
        Args:
            symbol: Stock symbol
            company_name: Company name
            
        Returns:
            True if published successfully
        """
        event = {
            "event_type": "company_info_updated",
            "symbol": symbol,
            "company_name": company_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Company info updated for {symbol}: {company_name}"
        }
        
        return self._publish_event(event)
    
    def publish_batch_complete(self, symbols: List[str], total_records: int) -> bool:
        """
        Publish event when a batch of symbols is completed
        
        Args:
            symbols: List of symbols processed
            total_records: Total number of records processed
            
        Returns:
            True if published successfully
        """
        event = {
            "event_type": "batch_complete",
            "symbols": symbols,
            "symbols_count": len(symbols),
            "total_records": total_records,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Batch complete: {len(symbols)} symbols, {total_records} total records"
        }
        
        return self._publish_event(event)
    
    def publish_error(self, symbol: str, error_message: str, operation: str = "data_fetch") -> bool:
        """
        Publish error event
        
        Args:
            symbol: Stock symbol
            error_message: Error message
            operation: Operation that failed
            
        Returns:
            True if published successfully
        """
        event = {
            "event_type": "error",
            "symbol": symbol,
            "operation": operation,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Error in {operation} for {symbol}: {error_message}"
        }
        
        return self._publish_event(event)
    
    def publish_system_status(self, status: str, details: Dict = None) -> bool:
        """
        Publish system status event
        
        Args:
            status: Status message
            details: Additional details
            
        Returns:
            True if published successfully
        """
        event = {
            "event_type": "system_status",
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"System status: {status}"
        }
        
        return self._publish_event(event)
    
    def _publish_event(self, event: Dict) -> bool:
        """
        Publish an event to SNS
        
        Args:
            event: Event data to publish
            
        Returns:
            True if published successfully
        """
        try:
            if not self.topic_arn:
                logger.error("No SNS topic ARN configured")
                return False
            
            # Convert event to JSON string
            message = json.dumps(event, default=str)
            
            # Publish to SNS
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=message,
                Subject=f"Stock Data Event: {event.get('event_type', 'unknown')}"
            )
            
            logger.info(f"✅ Event published successfully: {event.get('event_type')} - {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SNS connection and topic access
        
        Returns:
            True if connection successful
        """
        try:
            if not self.topic_arn:
                logger.error("❌ No SNS topic ARN configured")
                return False
            
            # Test if we can list topics (this tests AWS credentials and SNS access)
            try:
                response = self.sns_client.list_topics()
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    logger.info("✅ SNS connection successful - can list topics")
                    logger.info(f"Topic ARN: {self.topic_arn}")
                    return True
                else:
                    logger.error("❌ SNS connection failed - invalid response")
                    return False
                    
            except Exception as list_error:
                # If listing topics fails, it's a real authentication/permission issue
                logger.error(f"❌ SNS authentication failed: {list_error}")
                logger.error("❌ Check AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
                return False
                
        except Exception as e:
            logger.error(f"❌ SNS connection test failed: {e}")
            return False

def main():
    """Test the SNS publisher"""
    publisher = SNSPublisher()
    
    # Test connection
    if not publisher.test_connection():
        print("❌ SNS connection failed")
        return
    
    print("🧪 Testing SNS event publishing...")
    
    # Test different event types
    test_events = [
        ("stock_data_loaded", publisher.publish_stock_data_loaded("AAPL", 100, "2025-07-28")),
        ("company_info_updated", publisher.publish_company_info_updated("AAPL", "Apple Inc")),
        ("batch_complete", publisher.publish_batch_complete(["AAPL", "GOOGL", "MSFT"], 300)),
        ("system_status", publisher.publish_system_status("Data fetch completed", {"processed_symbols": 20})),
    ]
    
    for event_type, success in test_events:
        status = "✅" if success else "❌"
        print(f"{status} {event_type} event")

if __name__ == "__main__":
    main() 