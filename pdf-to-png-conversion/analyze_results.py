#!/usr/bin/env python3
"""
Analyze and compare the quality of converted PNG images
"""

import os
from PIL import Image
import json


def analyze_image(image_path):
    """Analyze a PNG image and return metadata"""

    img = Image.open(image_path)

    return {
        'path': image_path,
        'size': os.path.getsize(image_path),
        'dimensions': img.size,
        'mode': img.mode,
        'format': img.format,
        'dpi': img.info.get('dpi', None)
    }


def compare_images(output_dir="output"):
    """Compare all generated images"""

    files = [f for f in os.listdir(output_dir) if f.endswith('.png')]

    # Group by method
    methods = {}
    for f in files:
        method_name = f.split('_page_')[0]
        if method_name not in methods:
            methods[method_name] = []
        methods[method_name].append(os.path.join(output_dir, f))

    print("Image Analysis and Comparison")
    print("=" * 70)
    print()

    results = {}

    for method_name, images in sorted(methods.items()):
        print(f"{method_name}:")
        print("-" * 70)

        method_results = []

        for img_path in sorted(images):
            info = analyze_image(img_path)
            method_results.append(info)

            page_num = os.path.basename(img_path).split('_page_')[1].replace('.png', '')
            print(f"  Page {page_num}:")
            print(f"    File size: {info['size']:,} bytes ({info['size']/1024:.1f} KB)")
            print(f"    Dimensions: {info['dimensions'][0]}x{info['dimensions'][1]} pixels")
            print(f"    Color mode: {info['mode']}")
            if info['dpi']:
                print(f"    DPI: {info['dpi']}")

        # Calculate averages
        avg_size = sum(r['size'] for r in method_results) / len(method_results)
        avg_width = sum(r['dimensions'][0] for r in method_results) / len(method_results)
        avg_height = sum(r['dimensions'][1] for r in method_results) / len(method_results)

        print(f"\n  Averages:")
        print(f"    File size: {avg_size/1024:.1f} KB")
        print(f"    Dimensions: {avg_width:.0f}x{avg_height:.0f} pixels")
        print()

        results[method_name] = {
            'images': method_results,
            'average_size': avg_size,
            'average_dimensions': (avg_width, avg_height)
        }

    # Save results to JSON
    with open('analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to analysis_results.json")

    # Comparison summary
    print("\nComparison Summary:")
    print("-" * 70)

    for method_name, data in sorted(results.items()):
        print(f"{method_name:20s} - Avg size: {data['average_size']/1024:6.1f} KB - "
              f"Avg dims: {data['average_dimensions'][0]:.0f}x{data['average_dimensions'][1]:.0f}")


if __name__ == "__main__":
    compare_images()
