from PIL import ImageChops
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import io


def calculate_capacity(image):
    width, height = image.size
    return (width * height * 3) // 8  # in characters


def generate_difference_image(original, stego):
    return ImageChops.difference(original, stego)


def lsb_change_count(original, stego):
    o = np.array(original).flatten()
    s = np.array(stego).flatten()
    return sum(o[i] != s[i] for i in range(len(o)))


def plot_rgb_histogram(original, stego):
    """Side-by-side RGB histogram comparison of original vs stego image."""
    orig_arr = np.array(original.convert("RGB"))
    stego_arr = np.array(stego.convert("RGB"))

    colors = ['red', 'green', 'blue']
    channel_names = ['Red', 'Green', 'Blue']

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("RGB Histogram: Original vs Stego", fontsize=14, fontweight='bold')

    for i, (color, name) in enumerate(zip(colors, channel_names)):
        axes[i].hist(orig_arr[:, :, i].flatten(), bins=256, range=(0, 256),
                     color=color, alpha=0.5, label='Original', density=True)
        axes[i].hist(stego_arr[:, :, i].flatten(), bins=256, range=(0, 256),
                     color=color, alpha=0.5, label='Stego', linestyle='dashed',
                     histtype='step', linewidth=1.5, density=True)
        axes[i].set_title(f"{name} Channel")
        axes[i].set_xlabel("Pixel Intensity")
        axes[i].set_ylabel("Density")
        axes[i].legend()

    plt.tight_layout()
    return _fig_to_image(fig)


def plot_difference_heatmap(original, stego):
    """Heatmap showing where pixel changes occurred between original and stego."""
    orig_arr = np.array(original.convert("RGB")).astype(int)
    stego_arr = np.array(stego.convert("RGB")).astype(int)

    diff = np.abs(orig_arr - stego_arr).sum(axis=2)  # sum over RGB channels

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Pixel Difference Heatmap", fontsize=14, fontweight='bold')

    axes[0].imshow(original)
    axes[0].set_title("Original Image")
    axes[0].axis('off')

    heatmap = axes[1].imshow(diff, cmap='hot', interpolation='nearest')
    axes[1].set_title("Difference Heatmap (Brighter = More Changed)")
    axes[1].axis('off')
    fig.colorbar(heatmap, ax=axes[1], fraction=0.046, pad=0.04)

    plt.tight_layout()
    return _fig_to_image(fig)


def plot_lsb_visualization(original, stego):
    """Visualize LSB layer of original vs stego to show where bits were modified."""
    orig_arr = np.array(original.convert("RGB"))
    stego_arr = np.array(stego.convert("RGB"))

    orig_lsb = (orig_arr & 1) * 255
    stego_lsb = (stego_arr & 1) * 255
    lsb_diff = np.abs(orig_lsb.astype(int) - stego_lsb.astype(int)).sum(axis=2)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("LSB Bit Plane Analysis", fontsize=14, fontweight='bold')

    axes[0].imshow(orig_lsb)
    axes[0].set_title("Original LSB Plane")
    axes[0].axis('off')

    axes[1].imshow(stego_lsb)
    axes[1].set_title("Stego LSB Plane")
    axes[1].axis('off')

    axes[2].imshow(lsb_diff, cmap='hot')
    axes[2].set_title("LSB Change Map (White = Changed)")
    axes[2].axis('off')

    plt.tight_layout()
    return _fig_to_image(fig)


def plot_bit_plane(image, title="Bit Plane Analysis"):
    """Show all 8 bit planes for the Red channel of the image."""
    arr = np.array(image.convert("RGB"))[:, :, 0]  # Red channel

    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    fig.suptitle(f"{title} — Red Channel Bit Planes", fontsize=14, fontweight='bold')

    for bit in range(8):
        row, col = divmod(bit, 4)
        plane = ((arr >> bit) & 1) * 255
        axes[row][col].imshow(plane, cmap='gray')
        axes[row][col].set_title(f"Bit {bit} {'(LSB)' if bit == 0 else '(MSB)' if bit == 7 else ''}")
        axes[row][col].axis('off')

    plt.tight_layout()
    return _fig_to_image(fig)


def plot_pixel_value_scatter(original, stego, sample_size=3000):
    """Scatter plot comparing pixel values of original vs stego (sampled)."""
    orig_arr = np.array(original.convert("RGB")).flatten()
    stego_arr = np.array(stego.convert("RGB")).flatten()

    # Sample for performance
    idx = np.random.choice(len(orig_arr), min(sample_size, len(orig_arr)), replace=False)
    o_sample = orig_arr[idx]
    s_sample = stego_arr[idx]

    changed = o_sample != s_sample

    fig, ax = plt.subplots(figsize=(7, 6))
    fig.suptitle("Pixel Value Scatter: Original vs Stego", fontsize=14, fontweight='bold')

    ax.scatter(o_sample[~changed], s_sample[~changed], s=1, color='steelblue',
               alpha=0.3, label='Unchanged')
    ax.scatter(o_sample[changed], s_sample[changed], s=8, color='red',
               alpha=0.7, label='Changed (LSB modified)')
    ax.plot([0, 255], [0, 255], 'k--', linewidth=1, label='y = x (no change)')
    ax.set_xlabel("Original Pixel Value")
    ax.set_ylabel("Stego Pixel Value")
    ax.legend(markerscale=4)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)

    plt.tight_layout()
    return _fig_to_image(fig)


def plot_analysis_summary(original, stego):
    """Bar chart summary: total pixels, changed pixels, capacity used."""
    orig_arr = np.array(original.convert("RGB")).flatten()
    stego_arr = np.array(stego.convert("RGB")).flatten()

    total = len(orig_arr)
    changed = int(np.sum(orig_arr != stego_arr))
    unchanged = total - changed
    capacity = calculate_capacity(original)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Steganography Impact Summary", fontsize=14, fontweight='bold')

    # Pie chart
    axes[0].pie(
        [changed, unchanged],
        labels=[f'Modified\n({changed:,})', f'Unmodified\n({unchanged:,})'],
        colors=['#e74c3c', '#2ecc71'],
        autopct='%1.2f%%',
        startangle=140,
        textprops={'fontsize': 10}
    )
    axes[0].set_title("Pixel Modification Ratio")

    # Bar chart - stats
    stats = {
        'Total Pixels': total,
        'Changed Pixels': changed,
        'Max Capacity\n(chars)': capacity,
    }
    bars = axes[1].bar(stats.keys(), stats.values(),
                       color=['#3498db', '#e74c3c', '#f39c12'])
    axes[1].set_title("Image Statistics")
    axes[1].set_ylabel("Count")
    for bar in bars:
        axes[1].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() * 1.01,
                     f'{int(bar.get_height()):,}',
                     ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    return _fig_to_image(fig)


def _fig_to_image(fig):
    """Convert matplotlib figure to PIL Image."""
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()