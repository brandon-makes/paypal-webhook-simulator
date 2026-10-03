#!/usr/bin/env python3
"""Entry point for CLI sub-commands."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from paypal_webhook.cli import main as cli_main

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    cli_main(args)

if __name__ == "__main__":
    main()