#!/usr/bin/env python3
"""Main entry point for Skill Hub"""

import argparse
import sys
import asyncio
from skill_hub.config.config import Config
from skill_hub.server.server import Server


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Skill Hub - A Quart-based API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind the server to",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    parser.add_argument(
        "--auth-token",
        type=str,
        required=True,
        help="Authentication token (required)",
    )
    
    parser.add_argument(
        "--database-url",
        type=str,
        default="",
        help="PostgreSQL database URL (e.g., postgresql://user:pass@localhost:5432/dbname)",
    )
    
    parser.add_argument(
        "--database-pool-size",
        type=int,
        default=10,
        help="Database connection pool size",
    )
    
    parser.add_argument(
        "--database-max-overflow",
        type=int,
        default=20,
        help="Database connection pool max overflow",
    )
    
    parser.add_argument(
        "--database-pool-recycle",
        type=int,
        default=3600,
        help="Database connection pool recycle time in seconds",
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Data directory path",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    
    parser.add_argument(
        "--api-prefix",
        type=str,
        default="/api",
        help="API URL prefix",
    )
    
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = Config(
            host=args.host,
            port=args.port,
            debug=args.debug,
            auth_token=args.auth_token,
            database_url=args.database_url,
            database_pool_size=args.database_pool_size,
            database_max_overflow=args.database_max_overflow,
            database_pool_recycle=args.database_pool_recycle,
            data_dir=args.data_dir,
            log_level=args.log_level,
            api_prefix=args.api_prefix,
        )
        
        # Create and start server
        server = Server(config)
        server.start()
        
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
