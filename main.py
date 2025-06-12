#!/usr/bin/env python3
import sys
import traceback
from game import WumpusGame

def main():
    try:
        game = WumpusGame()
        game.run()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()