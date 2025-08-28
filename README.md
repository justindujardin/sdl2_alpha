# sdl2_alpha - Fast Alpha Blending for SDL2

sdl2_alpha provides mathematically correct alpha blending to fix SDL2's broken alpha compositing behavior. Built with Rust and PyO3 for maximum performance.

## Why sdl2_alpha?

SDL2's built-in alpha blending has fundamental flaws:
- Incorrect destination alpha handling
- Platform-specific premultiplication inconsistencies  
- Accumulation errors that degrade transparency (the dreaded "persistent haze")

sdl2_alpha implements Porter-Duff "over" compositing with proper premultiplied alpha math, delivering visually correct results for composition-heavy applications.

## 🚀 Development Setup (Complete Newbie Guide)

### Prerequisites

You need Rust and Python. If you don't have Rust:

```bash
# Install Rust (this installs rustc, cargo, etc.)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Verify Rust installation
rustc --version
cargo --version
```

### Install maturin (Rust-Python bridge)

```bash
pip install maturin
```

### Development Workflow

```bash
cd sdl2_alpha/

# Development build (fast compile, not optimized, includes debug info)
maturin develop

# This installs the package in development mode so you can import it immediately
# Changes to Rust code require rebuilding with maturin develop
```

### Release Builds (for production/benchmarking)

```bash
cd sdl2_alpha/

# Release build (slow compile, fully optimized)
maturin build --release

# Install the optimized wheel
pip install target/wheels/*.whl --force-reinstall

# OR do both in one command
maturin develop --release
```

### Testing Your Changes

```bash
cd sdl2_alpha/

# Install test dependencies
pip install -e .[test]

# Run the test suite
pytest tests/ -v

# Run just performance tests
pytest tests/test_performance.py -v -s

# Quick functionality test
python -c "
import sdl2_alpha
result = sdl2_alpha.blend_pixel((255,0,0,128), (0,255,0,255))
print(f'Test blend result: {result}')
print('✅ sdl2_alpha working!' if result[0] > 100 and result[1] > 100 else '❌ Something wrong')
"
```

### When to Use Which Build

- **Development build** (`maturin develop`):
  - Use when actively coding/debugging
  - Much faster to compile
  - Good enough for testing functionality
  - ~3-5x slower than release

- **Release build** (`maturin build --release`):
  - Use for performance testing
  - Use for final integration
  - Takes much longer to compile
  - Full SIMD optimizations enabled

### Useful Commands

```bash
# Clean everything and start over
cd sdl2_alpha/
cargo clean
rm -rf target/

# Check for Rust issues without compiling
cargo check

# See what maturin will build
maturin list-python

# Force rebuild everything
maturin develop --force

# Build specific Python version
maturin develop --python 3.10
```

### Troubleshooting

**"maturin not found"**:
```bash
pip install maturin
```

**"Rust compiler errors"**:
```bash
cargo check  # Shows errors without building Python extension
```

**"Import errors after rebuild"**:
```bash
# Sometimes Python caches the old version
python -c "import sys; print([p for p in sys.path if 'sdl2_alpha' in p])"
pip uninstall sdl2_alpha
maturin develop
```

**"Performance is slow"**:
- Make sure you're using release build: `maturin develop --release`
- Debug builds are much slower

## API Usage

```python
import sdl2_alpha

# Blend single pixel (for testing)
result = sdl2_alpha.blend_pixel(
    (255, 128, 64, 128),  # src (r,g,b,a)
    (64, 128, 255, 255)   # dst (r,g,b,a)  
)

# Zero-copy in-place blending (FAST - this is what Rendery uses)
sdl2_alpha.blend_rect_inplace(
    src_ptr,        # Raw pointer to source pixels
    src_width, src_height,
    src_x, src_y, src_w, src_h,  # Source rectangle (can be negative)
    dst_ptr,        # Raw pointer to destination pixels  
    dst_width, dst_height,
    dst_x, dst_y    # Destination position (can be negative)
)

# Copy-based blending (slower but easier)
blended_bytes = sdl2_alpha.blend_surface(
    src_bytes, dst_bytes, width, height
)

blended_bytes = sdl2_alpha.blend_rect(
    src_bytes, src_width, src_height, src_x, src_y, src_w, src_h,
    dst_bytes, dst_width, dst_height, dst_x, dst_y
)
```

## Performance Characteristics

- **~72 FPS** for 100 frames with 20 overlapping 50x50 elements on 800x600 surface
- **~1440 blits/sec** with automatic clipping
- **Zero-copy** direct memory access (blend_rect_inplace)
- **Automatic clipping** handles negative coordinates and off-screen blits
- **Fast paths** for fully opaque (direct copy) and fully transparent (skip) pixels

## Integration with Rendery

sdl2_alpha is automatically used by Rendery's SDL2 surface backend. All `surface.blit()` calls with alpha blending go through sdl2_alpha's zero-copy fast path.

## License

MIT