import os

# Bind to PORT environment variable dynamically provided by Render/Railway
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Single worker process to keep memory consumption low
workers = 1

# Handle concurrent requests using threads
threads = 4

# Increase timeout since training or predictions can be CPU/memory intensive
timeout = 120

# Keep alive connection timeout
keepalive = 2
