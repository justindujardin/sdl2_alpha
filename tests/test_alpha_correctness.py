"""
Test alpha blending mathematical correctness against known reference values.

These tests verify that sdl2_alpha produces mathematically correct Porter-Duff
"over" compositing results, focusing on edge cases that reveal alpha math bugs.
"""
import pytest
import sdl2_alpha


class TestPixelBlending:
    """Test single pixel alpha blending correctness."""
    
    def test_fully_opaque_over_opaque(self):
        """Fully opaque source should completely replace destination."""
        result = sdl2_alpha.blend_pixel(
            (255, 128, 64, 255),   # Opaque orange
            (64, 128, 255, 255)    # Opaque blue  
        )
        assert result == (255, 128, 64, 255), "Opaque source should replace destination"
    
    def test_fully_transparent_over_opaque(self):
        """Fully transparent source should leave destination unchanged."""
        result = sdl2_alpha.blend_pixel(
            (255, 128, 64, 0),     # Transparent orange
            (64, 128, 255, 255)    # Opaque blue
        )
        assert result == (64, 128, 255, 255), "Transparent source should not affect destination"
    
    def test_half_alpha_blending(self):
        """Test 50% alpha blending produces expected interpolation."""
        result = sdl2_alpha.blend_pixel(
            (255, 255, 255, 128),  # 50% white
            (0, 0, 0, 255)         # Opaque black
        )
        # Expected: roughly 50% interpolation  
        r, g, b, a = result
        assert 120 <= r <= 135, f"Red channel should be ~128, got {r}"
        assert 120 <= g <= 135, f"Green channel should be ~128, got {g}" 
        assert 120 <= b <= 135, f"Blue channel should be ~128, got {b}"
        assert a == 255, f"Alpha should be 255, got {a}"
    
    def test_premultiplied_alpha_correctness(self):
        """Test that premultiplied alpha math prevents dark halos."""
        # This is the classic test case that reveals incorrect alpha handling
        result = sdl2_alpha.blend_pixel(
            (255, 0, 0, 64),       # 25% red
            (0, 255, 0, 255)       # Opaque green
        )
        r, g, b, a = result
        
        # With correct premultiplied alpha, we should get reasonable blending
        # Without it, we get dark artifacts
        assert r > 50, f"Red contribution too low: {r} (dark halo artifact?)"
        assert g > 190, f"Green base too low: {g}"
        assert a == 255, f"Final alpha should be 255, got {a}"
    
    def test_zero_alpha_handling(self):
        """Test edge case of zero alpha in both source and destination."""
        result = sdl2_alpha.blend_pixel(
            (128, 128, 128, 0),    # Transparent gray
            (64, 64, 64, 0)        # Transparent dark gray
        )
        # When both have zero alpha, result should be zero (mathematically correct)
        assert result == (0, 0, 0, 0), "Zero alpha over zero alpha should be transparent"


class TestSurfaceBlending:
    """Test full surface alpha blending."""
    
    def create_test_surface(self, width: int, height: int, color: tuple) -> bytes:
        """Create a test surface with solid color."""
        r, g, b, a = color
        pixel_data = bytes([r, g, b, a] * width * height)
        return pixel_data
    
    def test_solid_color_blend(self):
        """Test blending two solid color surfaces."""
        width, height = 4, 4
        
        # Semi-transparent red over opaque blue
        red_surface = self.create_test_surface(width, height, (255, 0, 0, 128))
        blue_surface = self.create_test_surface(width, height, (0, 0, 255, 255))
        
        result_bytes = sdl2_alpha.blend_surface(red_surface, blue_surface, width, height)
        
        # Check first pixel
        result_pixel = (result_bytes[0], result_bytes[1], result_bytes[2], result_bytes[3])
        r, g, b, a = result_pixel
        
        assert r > 100, f"Should have red contribution: {r}"
        assert b > 100, f"Should have blue contribution: {b}"
        assert g < 50, f"Should have minimal green: {g}"
        assert a == 255, f"Alpha should be opaque: {a}"
    
    def test_buffer_size_validation(self):
        """Test that buffer size mismatches are caught."""
        with pytest.raises(ValueError, match="Buffer size mismatch"):
            sdl2_alpha.blend_surface(
                b"short",      # Wrong size
                b"also_short", # Wrong size  
                100, 100       # Claims 100x100
            )
    
    def test_empty_surface(self):
        """Test edge case of empty surface."""
        empty_bytes = b""
        result = sdl2_alpha.blend_surface(empty_bytes, empty_bytes, 0, 0)
        assert result == b""


class TestRectBlending:
    """Test rectangular region blending."""
    
    def create_checkered_surface(self, width: int, height: int) -> bytes:
        """Create a checkered pattern for testing rect operations."""
        pixels = []
        for y in range(height):
            for x in range(width):
                if (x + y) % 2 == 0:
                    pixels.extend([255, 255, 255, 255])  # White
                else:
                    pixels.extend([0, 0, 0, 255])        # Black
        return bytes(pixels)
    
    def test_rect_bounds_checking(self):
        """Test that out-of-bounds rects are rejected."""
        surface = self.create_checkered_surface(4, 4)
        
        with pytest.raises(ValueError, match="Source rect out of bounds"):
            sdl2_alpha.blend_rect(
                surface, 4, 4, 2, 2, 4, 4,  # Source rect extends past edge
                surface, 4, 4, 0, 0          # Destination  
            )
    
    def test_partial_rect_blend(self):
        """Test blending a subset region."""
        width, height = 8, 8
        
        # Create red and blue surfaces
        red_surface = bytes([255, 0, 0, 128] * width * height)
        blue_surface = bytes([0, 0, 255, 255] * width * height)
        
        # Blend 4x4 region from center
        result_bytes = sdl2_alpha.blend_rect(
            red_surface, width, height, 2, 2, 4, 4,  # Source: center 4x4
            blue_surface, width, height, 2, 2        # Dest: same position
        )
        
        # Check that corners are unchanged (pure blue)
        corner_pixel = (result_bytes[0], result_bytes[1], result_bytes[2], result_bytes[3])
        assert corner_pixel == (0, 0, 255, 255), "Corner should be unchanged"
        
        # Check that center region is blended
        center_idx = ((height // 2) * width + (width // 2)) * 4
        center_pixel = (
            result_bytes[center_idx], 
            result_bytes[center_idx + 1],
            result_bytes[center_idx + 2], 
            result_bytes[center_idx + 3]
        )
        r, g, b, a = center_pixel
        assert r > 100, f"Center should have red: {r}"
        assert b > 100, f"Center should have blue: {b}"


class TestAccumulation:
    """Test alpha blending accumulation behavior to catch math errors."""
    
    def test_multiple_blend_accumulation(self):
        """Test that multiple blends don't create artifacts."""
        # Start with white background
        bg = (255, 255, 255, 255)
        
        # Apply multiple 10% black layers
        current = bg
        for _ in range(10):
            current = sdl2_alpha.blend_pixel(
                (0, 0, 0, 26),  # ~10% black (26/255 ≈ 0.1)
                current
            )
        
        r, g, b, a = current
        
        # After 10 layers of 10% black, we should have significant darkening
        # but not complete black (which would indicate math errors)
        assert 50 <= r <= 200, f"Red should be moderately dark: {r}"
        assert 50 <= g <= 200, f"Green should be moderately dark: {g}"
        assert 50 <= b <= 200, f"Blue should be moderately dark: {b}"
        assert a == 255, f"Alpha should remain opaque: {a}"
        
        # Colors should be equal (gray)
        assert abs(r - g) <= 2, "Should maintain gray color"
        assert abs(g - b) <= 2, "Should maintain gray color"