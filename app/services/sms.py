# File: app/services/sms.py

import logging

logger = logging.getLogger(__name__)

async def send_otp_via_sms(phone_number: str, otp_code: str):
    # This is a background task, so it's safe to log here.
    # In production, you would replace this with your actual SMS provider's API call.
    logger.info(f"--- [SMS Service Simulation] ---")
    logger.info(f"Sending OTP {otp_code} to {phone_number}")
    logger.info(f"--- [End Simulation] ---")