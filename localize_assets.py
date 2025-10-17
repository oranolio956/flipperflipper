#!/usr/bin/env python3
"""
Script to localize all external CDN resources in CupidBot.ai HTML files
This will replace all CDN URLs with local asset paths
"""

import os
import re
from pathlib import Path

# Define the base directory
BASE_DIR = Path("/workspace/cupidbot-website-backup/cupidbot.ai")

# Mapping of CDN URLs to local paths (from root of site)
URL_MAPPINGS = [
    # CSS files
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/css/cupidbotai\.webflow\.[a-z0-9]+\.min\.css', 
     'assets/css/cupidbotai.webflow.min.css'),
    
    # JavaScript files
    (r'https://ajax\.googleapis\.com/ajax/libs/webfont/1\.6\.26/webfont\.js', 
     'assets/js/webfont.js'),
    (r'https://d3e54v103j8qbb\.cloudfront\.net/js/jquery-3\.5\.1\.min\.[a-z0-9]+\.js[^"]*', 
     'assets/js/jquery-3.5.1.min.js'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/js/webflow\.[a-z0-9]+\.js', 
     'assets/js/webflow.js'),
    
    # Favicon and icons
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/64434655b04ea639aa482974_icon%20\(1\)\.png', 
     'assets/images/favicon.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/64434659ea3c136c4108113e_icon%20\(2\)\.png', 
     'assets/images/apple-touch-icon.png'),
    
    # Hero images
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f4e50740bf677fa49018_bayle__heartbreaker_narrow-p-500\.png', 
     'assets/images/hero-image-500.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f4e50740bf677fa49018_bayle__heartbreaker_narrow-p-800\.png', 
     'assets/images/hero-image-800.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f4e50740bf677fa49018_bayle__heartbreaker_narrow\.png', 
     'assets/images/hero-image.png'),
    
    # Social media icons
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/644312313fc5a6382c3b93d3_twitter\.png', 
     'assets/images/twitter.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6443132fc6bbb1e4bdd9fba0_imageedit_4_4748485785\.png', 
     'assets/images/discord.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6443123262dc3f74412c5edb_ig-removebg-preview\.png', 
     'assets/images/instagram.png'),
    
    # Press logos
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f7f7e3f8a1e5915ef083_vice-p-500\.webp', 
     'assets/images/vice-500.webp'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f7f7e3f8a1e5915ef083_vice-p-800\.webp', 
     'assets/images/vice.webp'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f7f7e3f8a1e5915ef083_vice\.webp', 
     'assets/images/vice.webp'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f9db03c90101cd503e94_nypost-p-[0-9]+\.png', 
     'assets/images/nypost.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f9db03c90101cd503e94_nypost\.png', 
     'assets/images/nypost.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f9e94ee0d7966f3ae340_futurism-p-[0-9]+\.png', 
     'assets/images/futurism.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440f9e94ee0d7966f3ae340_futurism\.png', 
     'assets/images/futurism.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6447b34ecae193d045770e55_yahoo-p-[0-9]+\.png', 
     'assets/images/yahoo.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6447b34ecae193d045770e55_yahoo\.png', 
     'assets/images/yahoo.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440fa21f7300212a4556dba_bfmtv\.webp', 
     'assets/images/bfmtv.webp'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6447b4192c34ef4215403cd6_fox\.png', 
     'assets/images/fox.png'),
    
    # Calendar images
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440fbb3900c2378021e1068_cal-nobrands-p-[0-9]+\.png', 
     'assets/images/calendar.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f97f198da940/6440fbb3900c2378021e1068_cal-nobrands\.png', 
     'assets/images/calendar.png'),
    
    # Product screenshots (different CDN path)
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f956128da952/6495e5706d54f2a07e225499_cupidbot-scrnshots-p-500\.png', 
     'assets/images/product-screenshot-500.png'),
    (r'https://cdn\.prod\.website-files\.com/6440ef10d027f956128da952/6495e5706d54f2a07e225499_cupidbot-scrnshots\.png', 
     'assets/images/product-screenshot.png'),
]

def adjust_path_for_depth(local_path, depth):
    """
    Adjust the local path based on directory depth
    depth 0: index.html -> assets/...
    depth 1: product/beta.html -> ../assets/...
    """
    if depth == 0:
        return local_path
    else:
        return '../' * depth + local_path

def process_html_file(filepath):
    """Process a single HTML file and replace CDN URLs with local paths"""
    print(f"\nProcessing: {filepath}")
    
    # Calculate depth (number of directories from root)
    relative_path = filepath.relative_to(BASE_DIR)
    depth = len(relative_path.parent.parts)
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    replacements_made = 0
    
    # Apply all URL mappings
    for cdn_url_pattern, local_path in URL_MAPPINGS:
        adjusted_path = adjust_path_for_depth(local_path, depth)
        
        # Replace all occurrences
        new_content, count = re.subn(cdn_url_pattern, adjusted_path, content)
        if count > 0:
            print(f"  ✓ Replaced {count} occurrence(s) of {cdn_url_pattern[:60]}...")
            replacements_made += count
            content = new_content
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Saved {filepath.name} with {replacements_made} replacements")
    else:
        print(f"  ⚠️  No changes made to {filepath.name}")
    
    return replacements_made

def main():
    """Main function to process all HTML files"""
    print("=" * 70)
    print("CupidBot.ai Asset Localization Script")
    print("=" * 70)
    
    # Find all HTML files
    html_files = list(BASE_DIR.rglob("*.html"))
    
    print(f"\nFound {len(html_files)} HTML files to process:")
    for f in html_files:
        print(f"  - {f.relative_to(BASE_DIR)}")
    
    total_replacements = 0
    
    # Process each HTML file
    for html_file in html_files:
        replacements = process_html_file(html_file)
        total_replacements += replacements
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Made {total_replacements} total replacements across {len(html_files)} files")
    print("=" * 70)
    
    print("\n📋 Next Steps:")
    print("  1. Test the site locally: cd cupidbot.ai && python3 -m http.server 8000")
    print("  2. Open browser: http://localhost:8000")
    print("  3. Check that all images, CSS, and JS load correctly")
    print("  4. Test navigation between pages")
    print("  5. Deploy to your hosting platform")

if __name__ == "__main__":
    main()
