use pyo3::prelude::*;
use pyo3::types::PyBytes;
use palette::{LinSrgba, blend::Compose};
use rayon::prelude::*;
use std::slice;

/// Fast, correct alpha blending for SDL2 surfaces
/// 
/// Provides mathematically correct premultiplied alpha blending
/// to fix SDL2's broken alpha compositing behavior.

#[derive(Debug, Clone, Copy)]
pub struct Rgba8 {
    pub r: u8,
    pub g: u8, 
    pub b: u8,
    pub a: u8,
}

impl Rgba8 {
    #[inline]
    fn to_linear(self) -> LinSrgba<f32> {
        LinSrgba::new(
            self.r as f32 / 255.0,
            self.g as f32 / 255.0, 
            self.b as f32 / 255.0,
            self.a as f32 / 255.0,
        )
    }

    #[inline]
    fn from_linear(color: LinSrgba<f32>) -> Self {
        Rgba8 {
            r: (color.red.clamp(0.0, 1.0) * 255.0).round() as u8,
            g: (color.green.clamp(0.0, 1.0) * 255.0).round() as u8,
            b: (color.blue.clamp(0.0, 1.0) * 255.0).round() as u8,
            a: (color.alpha.clamp(0.0, 1.0) * 255.0).round() as u8,
        }
    }
}

/// Alpha blend a single pixel using Porter-Duff "over" operation
#[pyfunction]
fn blend_pixel(src: (u8, u8, u8, u8), dst: (u8, u8, u8, u8)) -> (u8, u8, u8, u8) {
    let src_rgba = Rgba8 { r: src.0, g: src.1, b: src.2, a: src.3 };
    let dst_rgba = Rgba8 { r: dst.0, g: dst.1, b: dst.2, a: dst.3 };
    
    let src_linear = src_rgba.to_linear();
    let dst_linear = dst_rgba.to_linear();
    
    // Porter-Duff "over" operation with correct premultiplied alpha
    let result = src_linear.over(dst_linear);
    let result_rgba = Rgba8::from_linear(result);
    
    (result_rgba.r, result_rgba.g, result_rgba.b, result_rgba.a)
}

/// Blend source buffer over destination buffer
/// 
/// Both buffers must be RGBA8888 format with same dimensions.
/// Performs parallel processing for large surfaces.
#[pyfunction]
fn blend_surface(py: Python, src_bytes: &Bound<'_, PyBytes>, dst_bytes: &Bound<'_, PyBytes>, width: u32, height: u32) -> PyResult<PyObject> {
    let src_data = src_bytes.as_bytes();
    let dst_data = dst_bytes.as_bytes();
    
    let expected_len = (width * height * 4) as usize;
    if src_data.len() != expected_len || dst_data.len() != expected_len {
        return Err(pyo3::exceptions::PyValueError::new_err(
            format!("Buffer size mismatch: expected {}, got src:{} dst:{}", 
                   expected_len, src_data.len(), dst_data.len())
        ));
    }

    // Convert to RGBA pixels and blend in parallel
    let mut result: Vec<u8> = Vec::with_capacity(expected_len);
    result.resize(expected_len, 0);
    
    let pixel_count = (width * height) as usize;
    
    // Process in parallel chunks
    result.par_chunks_mut(4)
        .zip(src_data.par_chunks(4))
        .zip(dst_data.par_chunks(4))
        .for_each(|((result_pixel, src_pixel), dst_pixel)| {
            let src_rgba = Rgba8 {
                r: src_pixel[0],
                g: src_pixel[1], 
                b: src_pixel[2],
                a: src_pixel[3],
            };
            let dst_rgba = Rgba8 {
                r: dst_pixel[0],
                g: dst_pixel[1],
                b: dst_pixel[2], 
                a: dst_pixel[3],
            };
            
            let src_linear = src_rgba.to_linear();
            let dst_linear = dst_rgba.to_linear();
            let blended = src_linear.over(dst_linear);
            let result_rgba = Rgba8::from_linear(blended);
            
            result_pixel[0] = result_rgba.r;
            result_pixel[1] = result_rgba.g;
            result_pixel[2] = result_rgba.b;
            result_pixel[3] = result_rgba.a;
        });

    Ok(PyBytes::new_bound(py, &result).into())
}

/// Blend with rectangular region support
#[pyfunction] 
fn blend_rect(
    py: Python,
    src_bytes: &Bound<'_, PyBytes>, 
    src_width: u32,
    src_height: u32,
    src_x: u32,
    src_y: u32,
    src_w: u32, 
    src_h: u32,
    dst_bytes: &Bound<'_, PyBytes>,
    dst_width: u32,
    dst_height: u32, 
    dst_x: u32,
    dst_y: u32
) -> PyResult<PyObject> {
    // Bounds checking
    if src_x + src_w > src_width || src_y + src_h > src_height {
        return Err(pyo3::exceptions::PyValueError::new_err("Source rect out of bounds"));
    }
    if dst_x + src_w > dst_width || dst_y + src_h > dst_height {
        return Err(pyo3::exceptions::PyValueError::new_err("Destination rect out of bounds"));
    }
    
    let src_data = src_bytes.as_bytes();
    let dst_data = dst_bytes.as_bytes();
    let mut result = dst_data.to_vec();
    
    // Blit rect with alpha blending
    for y in 0..src_h {
        for x in 0..src_w {
            let src_idx = (((src_y + y) * src_width + (src_x + x)) * 4) as usize;
            let dst_idx = (((dst_y + y) * dst_width + (dst_x + x)) * 4) as usize;
            
            let src_rgba = Rgba8 {
                r: src_data[src_idx],
                g: src_data[src_idx + 1],
                b: src_data[src_idx + 2], 
                a: src_data[src_idx + 3],
            };
            let dst_rgba = Rgba8 {
                r: result[dst_idx],
                g: result[dst_idx + 1],
                b: result[dst_idx + 2],
                a: result[dst_idx + 3],
            };
            
            let src_linear = src_rgba.to_linear();
            let dst_linear = dst_rgba.to_linear(); 
            let blended = src_linear.over(dst_linear);
            let result_rgba = Rgba8::from_linear(blended);
            
            result[dst_idx] = result_rgba.r;
            result[dst_idx + 1] = result_rgba.g;
            result[dst_idx + 2] = result_rgba.b;
            result[dst_idx + 3] = result_rgba.a;
        }
    }
    
    Ok(PyBytes::new_bound(py, &result).into())
}

/// Fast in-place alpha blending with automatic clipping
/// 
/// SAFETY: Caller must ensure pointers are valid
#[pyfunction] 
unsafe fn blend_rect_inplace(
    src_ptr: usize,
    src_width: u32,
    src_height: u32,
    src_x: i32,
    src_y: i32, 
    src_w: u32,
    src_h: u32,
    dst_ptr: usize,
    dst_width: u32,
    dst_height: u32,
    dst_x: i32,
    dst_y: i32
) -> PyResult<()> {
    // Fast clipping logic - all in one place
    let mut sx = src_x;
    let mut sy = src_y;
    let mut sw = src_w as i32;
    let mut sh = src_h as i32;
    let mut dx = dst_x;
    let mut dy = dst_y;
    
    // Clip source bounds
    if sx < 0 { dx -= sx; sw += sx; sx = 0; }
    if sy < 0 { dy -= sy; sh += sy; sy = 0; }
    if sx + sw > src_width as i32 { sw = src_width as i32 - sx; }
    if sy + sh > src_height as i32 { sh = src_height as i32 - sy; }
    
    // Clip destination bounds
    if dx < 0 { sx -= dx; sw += dx; dx = 0; }
    if dy < 0 { sy -= dy; sh += dy; dy = 0; }
    if dx + sw > dst_width as i32 { sw = dst_width as i32 - dx; }
    if dy + sh > dst_height as i32 { sh = dst_height as i32 - dy; }
    
    // Early exit if clipped to nothing
    if sw <= 0 || sh <= 0 { return Ok(()); }

    // Create safe slices from raw pointers
    let src_slice = slice::from_raw_parts(
        src_ptr as *const u8,
        (src_width * src_height * 4) as usize
    );
    let dst_slice = slice::from_raw_parts_mut(
        dst_ptr as *mut u8,
        (dst_width * dst_height * 4) as usize
    );

    // Use clipped dimensions (cast back to u32 after clipping)
    let final_sw = sw as u32;
    let final_sh = sh as u32;
    let final_sx = sx as u32;
    let final_sy = sy as u32;
    let final_dx = dx as u32;
    let final_dy = dy as u32;
    
    // Optimized single-threaded in-place blending
    for y in 0..final_sh {
        for x in 0..final_sw {
            let src_idx = (((final_sy + y) * src_width + (final_sx + x)) * 4) as usize;
            let dst_idx = (((final_dy + y) * dst_width + (final_dx + x)) * 4) as usize;

            // Fast path optimizations
            let src_a = src_slice[src_idx + 3];
            
            if src_a == 0 {
                // Fully transparent - skip
                continue;
            } else if src_a == 255 {
                // Fully opaque - direct copy (fastest path)
                dst_slice[dst_idx] = src_slice[src_idx];
                dst_slice[dst_idx + 1] = src_slice[src_idx + 1];
                dst_slice[dst_idx + 2] = src_slice[src_idx + 2];
                dst_slice[dst_idx + 3] = 255;
            } else {
                // Proper alpha blend for semi-transparent pixels
                let src_rgba = Rgba8 {
                    r: src_slice[src_idx],
                    g: src_slice[src_idx + 1],
                    b: src_slice[src_idx + 2],
                    a: src_a,
                };
                let dst_rgba = Rgba8 {
                    r: dst_slice[dst_idx],
                    g: dst_slice[dst_idx + 1],
                    b: dst_slice[dst_idx + 2],
                    a: dst_slice[dst_idx + 3],
                };

                let src_linear = src_rgba.to_linear();
                let dst_linear = dst_rgba.to_linear();
                let blended = src_linear.over(dst_linear);
                let result_rgba = Rgba8::from_linear(blended);

                dst_slice[dst_idx] = result_rgba.r;
                dst_slice[dst_idx + 1] = result_rgba.g;
                dst_slice[dst_idx + 2] = result_rgba.b;
                dst_slice[dst_idx + 3] = result_rgba.a;
            }
        }
    }

    Ok(())
}

#[pymodule]
fn blendy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(blend_pixel, m)?)?;
    m.add_function(wrap_pyfunction!(blend_surface, m)?)?;
    m.add_function(wrap_pyfunction!(blend_rect, m)?)?;
    m.add_function(wrap_pyfunction!(blend_rect_inplace, m)?)?;
    Ok(())
}