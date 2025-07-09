#!/usr/bin/env python3
"""
Test script to verify the escrow system implementation
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.escrow_service import EscrowService
from app.core.database import get_database
from bson import ObjectId
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_escrow_system():
    """Test the complete escrow system functionality"""
    # Initialize database connection
    from app.core.database import connect_to_mongo
    await connect_to_mongo()
    
    db = get_database()
    escrow_service = EscrowService(db)
    
    # Create a test user
    test_user_id = ObjectId()
    test_user = {
        "_id": test_user_id,
        "name": "Test User",
        "points": 1000,
        "escrow_amount": 0,
        "team": "Test Team"
    }
    
    try:
        # Insert test user
        from app.core.database import Collections
        await db[Collections.USERS].insert_one(test_user)
        logger.info(f"Created test user: {test_user_id}")
        
        # Test 1: Create escrow
        escrow_id = await escrow_service.create_escrow(
            user_id=test_user_id,
            amount=500,
            escrow_type="stock_order",
            metadata={
                "side": "buy",
                "quantity": 10,
                "price": 50
            }
        )
        logger.info(f"Created escrow: {escrow_id}")
        
        # Verify user points were deducted and escrow_amount increased
        user = await db[Collections.USERS].find_one({"_id": test_user_id})
        assert user["points"] == 500, f"Expected 500 points, got {user['points']}"
        assert user["escrow_amount"] == 500, f"Expected 500 escrow_amount, got {user['escrow_amount']}"
        logger.info("✓ Escrow creation test passed")
        
        # Test 2: Complete escrow
        await escrow_service.complete_escrow(escrow_id)
        logger.info(f"Completed escrow: {escrow_id}")
        
        # Verify escrow_amount was reset
        user = await db[Collections.USERS].find_one({"_id": test_user_id})
        assert user["escrow_amount"] == 0, f"Expected 0 escrow_amount, got {user['escrow_amount']}"
        logger.info("✓ Escrow completion test passed")
        
        # Test 3: Create and cancel escrow
        escrow_id2 = await escrow_service.create_escrow(
            user_id=test_user_id,
            amount=200,
            escrow_type="pvp_battle"
        )
        logger.info(f"Created second escrow: {escrow_id2}")
        
        await escrow_service.cancel_escrow(escrow_id2)
        logger.info(f"Cancelled escrow: {escrow_id2}")
        
        # Verify points were refunded
        user = await db[Collections.USERS].find_one({"_id": test_user_id})
        assert user["points"] == 500, f"Expected 500 points after cancel, got {user['points']}"
        assert user["escrow_amount"] == 0, f"Expected 0 escrow_amount after cancel, got {user['escrow_amount']}"
        logger.info("✓ Escrow cancellation test passed")
        
        # Test 4: Get user escrows
        escrows = await escrow_service.get_user_escrows(test_user_id)
        assert len(escrows) == 2, f"Expected 2 escrows, got {len(escrows)}"
        logger.info("✓ Get user escrows test passed")
        
        logger.info("🎉 All escrow system tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Clean up test data
        await db[Collections.USERS].delete_one({"_id": test_user_id})
        await db[Collections.ESCROWS].delete_many({"user_id": test_user_id})
        logger.info("Cleaned up test data")

if __name__ == "__main__":
    asyncio.run(test_escrow_system())