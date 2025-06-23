#!/usr/bin/env python3

# Test the audio download function directly
from utils import download_media_with_format

url = "https://www.instagram.com/reels/C_D_i9HoDC8/"
platform = "instagram"
format_id = "bestaudio[abr>=128]"
download_type = "audio"

print("Testing audio download...")
result = download_media_with_format(url, platform, format_id, download_type)
print(f"Result: {result}")