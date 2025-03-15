from flask import Flask, request, jsonify
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# This is the entry point for Vercel
handler = app

