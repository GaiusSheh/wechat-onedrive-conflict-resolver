#!/usr/bin/env python3
"""
Simple ICO file fix using method that works better on Windows
"""
from PIL import Image
import os

def create_ico_simple():
    source = "gui/resources/downloads/main_transp_bg.png"
    output = "gui/resources/icons/app_new.ico"
    
    print("Creating ICO file with multiple sizes...")
    
    try:
        with Image.open(source) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create multiple sizes manually and save separately, then combine
            sizes_to_create = [16, 32, 48, 64, 128, 256]
            
            # Create individual size images
            resized_images = []
            for size in sizes_to_create:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                resized_images.append(resized)
                print(f"Created {size}x{size}")
            
            # Save using the method that seems to work
            if resized_images:
                # Try saving with explicit sizes parameter
                first_img = resized_images[0]
                other_imgs = resized_images[1:] if len(resized_images) > 1 else []
                
                first_img.save(
                    output,
                    format='ICO',
                    sizes=[(size, size) for size in sizes_to_create],
                    append_images=other_imgs
                )
                
                file_size = os.path.getsize(output)
                print(f"ICO saved: {output}, size: {file_size} bytes")
                
                if file_size > 760:  # Should be bigger than the old single-size version
                    print("SUCCESS: Multi-size ICO created!")
                    return True
                else:
                    print("WARNING: ICO might still be single size")
                    return False
                    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_ico_simple()