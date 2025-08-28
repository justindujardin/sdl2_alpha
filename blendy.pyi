"""Type stubs for blendy - Fast Alpha Blending for SDL2"""

from typing import Tuple

def blend_pixel(
    src: Tuple[int, int, int, int], 
    dst: Tuple[int, int, int, int]
) -> Tuple[int, int, int, int]:
    """Blend single pixel using Porter-Duff 'over' operation.
    
    Args:
        src: Source pixel as (r, g, b, a) tuple (0-255)
        dst: Destination pixel as (r, g, b, a) tuple (0-255)
        
    Returns:
        Blended pixel as (r, g, b, a) tuple (0-255)
        
    Example:
        result = blendy.blend_pixel((255, 0, 0, 128), (0, 255, 0, 255))
    """
    ...

def blend_surface(
    src_bytes: bytes,
    dst_bytes: bytes, 
    width: int,
    height: int
) -> bytes:
    """Blend source surface over destination surface (copy-based).
    
    Args:
        src_bytes: Source surface pixel data (RGBA8888 format)
        dst_bytes: Destination surface pixel data (RGBA8888 format)
        width: Surface width in pixels
        height: Surface height in pixels
        
    Returns:
        Blended surface pixel data as bytes
        
    Note:
        Both surfaces must be same size and RGBA8888 format.
        This creates a copy - use blend_rect_inplace for zero-copy.
    """
    ...

def blend_rect(
    src_bytes: bytes,
    src_width: int,
    src_height: int,
    src_x: int,
    src_y: int,
    src_w: int,
    src_h: int,
    dst_bytes: bytes,
    dst_width: int,
    dst_height: int,
    dst_x: int,
    dst_y: int
) -> bytes:
    """Blend rectangular region (copy-based).
    
    Args:
        src_bytes: Source surface pixel data (RGBA8888)
        src_width, src_height: Source surface dimensions
        src_x, src_y, src_w, src_h: Source rectangle
        dst_bytes: Destination surface pixel data (RGBA8888)
        dst_width, dst_height: Destination surface dimensions
        dst_x, dst_y: Destination position
        
    Returns:
        Blended destination surface as bytes
        
    Note:
        Creates a copy - use blend_rect_inplace for zero-copy.
    """
    ...

def blend_rect_inplace(
    src_ptr: int,
    src_width: int,
    src_height: int,
    src_x: int,
    src_y: int,
    src_w: int,
    src_h: int,
    dst_ptr: int,
    dst_width: int,
    dst_height: int,
    dst_x: int,
    dst_y: int
) -> None:
    """Fast zero-copy in-place alpha blending with automatic clipping.
    
    Args:
        src_ptr: Raw pointer to source pixel data (RGBA8888)
        src_width, src_height: Source surface dimensions
        src_x, src_y: Source rectangle position (can be negative)
        src_w, src_h: Source rectangle size
        dst_ptr: Raw pointer to destination pixel data (RGBA8888)
        dst_width, dst_height: Destination surface dimensions
        dst_x, dst_y: Destination position (can be negative)
        
    Note:
        This is the fastest path used by Rendery. Modifies destination
        surface in-place. Automatic clipping handles out-of-bounds coordinates.
        
        SAFETY: Caller must ensure pointers are valid RGBA32 surface data.
        
    Example:
        # Get SDL surface pointers
        src_ptr = ctypes.cast(src_surface.pixels, ctypes.c_void_p).value
        dst_ptr = ctypes.cast(dst_surface.pixels, ctypes.c_void_p).value
        
        # Blend 50x50 region from (0,0) to (25,25)
        blendy.blend_rect_inplace(
            src_ptr, 100, 100, 0, 0, 50, 50,
            dst_ptr, 200, 200, 25, 25
        )
    """
    ...