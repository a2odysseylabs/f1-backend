import fastf1
import os
from pathlib import Path
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def setup_cache():
    """Configure FastF1 caching for optimal performance"""
    try:
        if settings.FASTF1_CACHE_ENABLED:
            # Create cache directory if it doesn't exist
            cache_dir = Path(settings.FASTF1_CACHE_DIR)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Enable FastF1 cache
            fastf1.Cache.enable_cache(str(cache_dir))
            logger.info(f"FastF1 cache enabled at: {cache_dir}")
        else:
            # Disable cache if configured to do so
            fastf1.Cache.disable_cache()
            logger.info("FastF1 cache disabled")
            
    except Exception as e:
        logger.error(f"Failed to setup FastF1 cache: {e}")
        # Continue without cache if setup fails
        fastf1.Cache.disable_cache()

def clear_cache():
    """Clear FastF1 cache"""
    try:
        fastf1.Cache.clear_cache()
        logger.info("FastF1 cache cleared")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")

def get_cache_info():
    """Get cache information"""
    try:
        return fastf1.Cache.get_cache_info()
    except Exception as e:
        logger.error(f"Failed to get cache info: {e}")
        return None 