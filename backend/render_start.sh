#!/bin/bash
# Render.com startup script for background agent

echo "Starting Anti-Berojgar Background Agent..."

# Run the background tracking loop once
python3 -c "
import asyncio
from main import background_tracking_loop

print('Running background tracking cycle...')
asyncio.run(background_tracking_loop())
print('Tracking cycle complete!')
"

echo "Agent cycle complete. Exiting."
