"""
Performance tests for sdl2_alpha alpha blending operations.

These tests verify that sdl2_alpha meets performance expectations
and scales appropriately with surface size.
"""
import time
import pytest
import sdl2_alpha


class TestPerformance:
    """Test performance characteristics of blending operations."""
    
    @pytest.mark.parametrize("size", [
        (64, 64),      # Small: 4K pixels
        (256, 256),    # Medium: 65K pixels  
        (512, 512),    # Large: 262K pixels
        (1024, 1024),  # Very large: 1M pixels
    ])
    def test_surface_blend_scaling(self, size):
        """Test that surface blending scales reasonably with size."""
        width, height = size
        pixel_count = width * height
        
        # Create test surfaces
        red_data = bytes([255, 0, 0, 128] * pixel_count)
        blue_data = bytes([0, 0, 255, 255] * pixel_count)
        
        # Measure blend time
        start_time = time.perf_counter()
        result = sdl2_alpha.blend_surface(red_data, blue_data, width, height)
        end_time = time.perf_counter()
        
        blend_time = end_time - start_time
        pixels_per_second = pixel_count / blend_time if blend_time > 0 else float('inf')
        
        # Performance expectations (realistic for debug builds)
        # Small surfaces have significant overhead relative to processing time
        if pixel_count < 10_000:  # < 10K pixels  
            min_pixels_per_second = 1_000_000
        elif pixel_count < 100_000:  # < 100K pixels
            min_pixels_per_second = 3_000_000
        else:
            min_pixels_per_second = 5_000_000
        
        assert len(result) == pixel_count * 4, "Result should have correct size"
        assert pixels_per_second >= min_pixels_per_second, (
            f"Performance too slow: {pixels_per_second:.0f} pixels/sec "
            f"(minimum: {min_pixels_per_second}) for {width}x{height}"
        )
        
        print(f"{width}x{height}: {pixels_per_second:.0f} pixels/sec ({blend_time*1000:.2f}ms)")
    
    def test_pixel_blend_overhead(self):
        """Test single pixel blend overhead."""
        test_cases = [
            ((255, 0, 0, 128), (0, 255, 0, 255)),
            ((128, 128, 128, 64), (255, 255, 255, 255)),
            ((0, 0, 0, 0), (128, 128, 128, 128)),
        ]
        
        iterations = 100_000
        
        start_time = time.perf_counter()
        for _ in range(iterations):
            for src, dst in test_cases:
                sdl2_alpha.blend_pixel(src, dst)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        ops_per_second = (iterations * len(test_cases)) / total_time
        
        # Should handle at least 500K pixel operations per second
        min_ops_per_second = 500_000
        
        assert ops_per_second >= min_ops_per_second, (
            f"Pixel blend too slow: {ops_per_second:.0f} ops/sec "
            f"(minimum: {min_ops_per_second})"
        )
        
        print(f"Pixel blend: {ops_per_second:.0f} ops/sec")
    
    def test_rect_blend_efficiency(self):
        """Test that rect blending is efficient for partial operations."""
        width, height = 256, 256
        pixel_count = width * height
        
        # Create test surfaces  
        src_data = bytes([255, 128, 64, 128] * pixel_count)
        dst_data = bytes([64, 128, 255, 255] * pixel_count)
        
        # Test different rect sizes
        rect_sizes = [
            (32, 32),   # Small rect
            (64, 64),   # Medium rect
            (128, 128), # Large rect
        ]
        
        for rect_w, rect_h in rect_sizes:
            rect_pixels = rect_w * rect_h
            
            start_time = time.perf_counter()
            result = sdl2_alpha.blend_rect(
                src_data, width, height, 0, 0, rect_w, rect_h,
                dst_data, width, height, 0, 0
            )
            end_time = time.perf_counter()
            
            blend_time = end_time - start_time
            pixels_per_second = rect_pixels / blend_time if blend_time > 0 else float('inf')
            
            # Should be reasonably fast for small rects
            min_pixels_per_second = 2_000_000
            
            assert len(result) == pixel_count * 4, "Result should have full surface size"
            assert pixels_per_second >= min_pixels_per_second, (
                f"Rect blend too slow: {pixels_per_second:.0f} pixels/sec "
                f"for {rect_w}x{rect_h} rect"
            )
            
            print(f"Rect {rect_w}x{rect_h}: {pixels_per_second:.0f} pixels/sec")


class TestMemoryEfficiency:
    """Test memory usage patterns."""
    
    def test_large_surface_memory(self):
        """Test that large surfaces don't cause excessive memory usage."""
        width, height = 1024, 1024
        pixel_count = width * height
        expected_size = pixel_count * 4
        
        # Create large test surfaces
        src_data = bytes([255, 128, 64, 200] * pixel_count)
        dst_data = bytes([64, 128, 255, 255] * pixel_count)
        
        # Ensure we have the expected input size
        assert len(src_data) == expected_size
        assert len(dst_data) == expected_size
        
        # Blend should not fail due to memory constraints
        result = sdl2_alpha.blend_surface(src_data, dst_data, width, height)
        
        # Output should be exactly the expected size
        assert len(result) == expected_size, "Output size should match input"
        
        # Result should contain actual blended data (not just zeros)
        # Check a few sample pixels
        for i in range(0, len(result), expected_size // 10):
            if i + 3 < len(result):
                pixel = (result[i], result[i+1], result[i+2], result[i+3])
                assert any(channel > 0 for channel in pixel), f"Pixel at {i} is all zeros"