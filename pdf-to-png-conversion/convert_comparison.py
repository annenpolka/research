#!/usr/bin/env python3
"""
PDF to PNG Conversion Methods Comparison

This script compares different methods for converting PDF files to PNG images.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any
import sys


class ConversionMethod:
    """Base class for PDF to PNG conversion methods"""

    def __init__(self, name: str):
        self.name = name
        self.available = False
        self.error_msg = None

    def check_availability(self) -> bool:
        """Check if this method is available"""
        raise NotImplementedError

    def convert(self, pdf_path: str, output_dir: str, dpi: int = 150) -> List[str]:
        """Convert PDF to PNG images. Returns list of output files."""
        raise NotImplementedError

    def get_info(self) -> str:
        """Get information about this method"""
        return f"{self.name}: {'Available' if self.available else f'Not available - {self.error_msg}'}"


class PDF2ImageMethod(ConversionMethod):
    """Using pdf2image library (requires poppler)"""

    def __init__(self):
        super().__init__("pdf2image")
        self.check_availability()

    def check_availability(self) -> bool:
        try:
            from pdf2image import convert_from_path
            self.available = True
            return True
        except ImportError as e:
            self.error_msg = f"pdf2image not installed: {e}"
            return False
        except Exception as e:
            self.error_msg = str(e)
            return False

    def convert(self, pdf_path: str, output_dir: str, dpi: int = 150) -> List[str]:
        from pdf2image import convert_from_path

        images = convert_from_path(pdf_path, dpi=dpi)
        output_files = []

        for i, image in enumerate(images):
            output_path = os.path.join(output_dir, f"{self.name}_page_{i+1}.png")
            image.save(output_path, "PNG")
            output_files.append(output_path)

        return output_files


class PyMuPDFMethod(ConversionMethod):
    """Using PyMuPDF (fitz) library"""

    def __init__(self):
        super().__init__("PyMuPDF")
        self.check_availability()

    def check_availability(self) -> bool:
        try:
            import fitz
            self.available = True
            return True
        except ImportError as e:
            self.error_msg = f"PyMuPDF not installed: {e}"
            return False

    def convert(self, pdf_path: str, output_dir: str, dpi: int = 150) -> List[str]:
        import fitz

        pdf_document = fitz.open(pdf_path)
        output_files = []

        # Calculate zoom factor from DPI (default 72 DPI)
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=mat)
            output_path = os.path.join(output_dir, f"{self.name}_page_{page_num+1}.png")
            pix.save(output_path)
            output_files.append(output_path)

        pdf_document.close()
        return output_files


class PillowMethod(ConversionMethod):
    """Using Pillow library directly"""

    def __init__(self):
        super().__init__("Pillow")
        self.check_availability()

    def check_availability(self) -> bool:
        try:
            from PIL import Image
            self.available = True
            return True
        except ImportError as e:
            self.error_msg = f"Pillow not installed: {e}"
            return False

    def convert(self, pdf_path: str, output_dir: str, dpi: int = 150) -> List[str]:
        from PIL import Image

        output_files = []

        try:
            # Pillow can open some PDFs directly, but support is limited
            images = Image.open(pdf_path)

            # Try to get all pages
            page_num = 0
            while True:
                try:
                    images.seek(page_num)
                    output_path = os.path.join(output_dir, f"{self.name}_page_{page_num+1}.png")
                    images.save(output_path, "PNG", dpi=(dpi, dpi))
                    output_files.append(output_path)
                    page_num += 1
                except EOFError:
                    break
        except Exception as e:
            raise Exception(f"Pillow direct PDF support failed: {e}")

        return output_files


class GhostscriptMethod(ConversionMethod):
    """Using Ghostscript command line tool"""

    def __init__(self):
        super().__init__("Ghostscript")
        self.check_availability()

    def check_availability(self) -> bool:
        import subprocess
        try:
            result = subprocess.run(['gs', '--version'],
                                  capture_output=True,
                                  timeout=5)
            if result.returncode == 0:
                self.available = True
                return True
            else:
                self.error_msg = "gs command failed"
                return False
        except FileNotFoundError:
            self.error_msg = "Ghostscript (gs) not found"
            return False
        except Exception as e:
            self.error_msg = str(e)
            return False

    def convert(self, pdf_path: str, output_dir: str, dpi: int = 150) -> List[str]:
        import subprocess

        output_pattern = os.path.join(output_dir, f"{self.name}_page_%d.png")

        cmd = [
            'gs',
            '-dNOPAUSE',
            '-dBATCH',
            '-sDEVICE=png16m',
            f'-r{dpi}',
            f'-sOutputFile={output_pattern}',
            pdf_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # Find generated files
        output_files = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith(f"{self.name}_page_")
        ])

        return output_files


def benchmark_conversion(method: ConversionMethod, pdf_path: str, output_dir: str, dpi: int = 150) -> Dict[str, Any]:
    """Benchmark a conversion method"""

    if not method.available:
        return {
            'method': method.name,
            'success': False,
            'error': method.error_msg,
            'time': None,
            'files': []
        }

    try:
        start_time = time.time()
        output_files = method.convert(pdf_path, output_dir, dpi)
        elapsed_time = time.time() - start_time

        # Get file sizes
        file_sizes = [os.path.getsize(f) for f in output_files]

        return {
            'method': method.name,
            'success': True,
            'time': elapsed_time,
            'files': output_files,
            'num_pages': len(output_files),
            'file_sizes': file_sizes,
            'total_size': sum(file_sizes),
            'avg_size': sum(file_sizes) / len(file_sizes) if file_sizes else 0
        }
    except Exception as e:
        return {
            'method': method.name,
            'success': False,
            'error': str(e),
            'time': None,
            'files': []
        }


def main():
    """Main comparison function"""

    print("PDF to PNG Conversion Methods Comparison")
    print("=" * 60)
    print()

    # Initialize all methods
    methods = [
        PDF2ImageMethod(),
        PyMuPDFMethod(),
        PillowMethod(),
        GhostscriptMethod()
    ]

    # Check availability
    print("Checking method availability:")
    for method in methods:
        print(f"  {method.get_info()}")
    print()

    # Test PDF path
    pdf_path = "sample.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found. Please create a sample PDF first.")
        return 1

    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Run benchmarks
    print(f"Converting {pdf_path} to PNG...")
    print()

    results = []
    for method in methods:
        print(f"Testing {method.name}...")
        result = benchmark_conversion(method, pdf_path, output_dir, dpi=150)
        results.append(result)

        if result['success']:
            print(f"  ✓ Success in {result['time']:.3f}s")
            print(f"    Pages: {result['num_pages']}")
            print(f"    Total size: {result['total_size']/1024:.1f} KB")
            print(f"    Avg size: {result['avg_size']/1024:.1f} KB")
        else:
            print(f"  ✗ Failed: {result['error']}")
        print()

    # Summary
    print("Summary:")
    print("-" * 60)
    successful_results = [r for r in results if r['success']]

    if successful_results:
        fastest = min(successful_results, key=lambda x: x['time'])
        smallest = min(successful_results, key=lambda x: x['total_size'])

        print(f"Fastest method: {fastest['method']} ({fastest['time']:.3f}s)")
        print(f"Smallest output: {smallest['method']} ({smallest['total_size']/1024:.1f} KB)")

        print("\nAll results:")
        for result in successful_results:
            print(f"  {result['method']:15s} - {result['time']:.3f}s - {result['total_size']/1024:.1f} KB")
    else:
        print("No methods succeeded.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
