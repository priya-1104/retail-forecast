import os
import sys

# Add current directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from scripts.seed import seed_database

if __name__ == '__main__':
    seed_database()
