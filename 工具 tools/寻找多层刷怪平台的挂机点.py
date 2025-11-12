import numpy as np
import matplotlib.pyplot as plt

# ========== 可调参数 ==========
num_layers = 9
layer_spacing = 4
plane_width = 235
plane_height = 201
shell_inner_radius = 24
shell_outer_radius = 128
step_size = 0.0625  # 支持小数！例如 1/16 = 0.0625（MC 坐标精度常用）

# ========== 设置中文字体 ==========
plt.rcParams['font.family'] = 'Microsoft YaHei'
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# ========== 平台 y 坐标（顶层 y=0） ==========
top_y = 0
layer_ys = np.array([top_y - i * layer_spacing for i in range(num_layers)], dtype=float)
bottom_y = layer_ys[-1]
center_y = (top_y + bottom_y) / 2.0  # 例如 -16.0

# ========== 预处理 (x, z) 平面 r² 频次 ==========
x_vals = np.arange(-plane_width // 2, plane_width // 2 + 1)
z_vals = np.arange(-plane_height // 2, plane_height // 2 + 1)
X, Z = np.meshgrid(x_vals, z_vals, indexing='ij')
r2_vals = (X**2 + Z**2).ravel()
max_r2 = int(r2_vals.max())
r2_counts = np.bincount(r2_vals, minlength=max_r2 + 1)

# ========== 遍历范围：从几何中心到最高有效高度 ==========
y_start = center_y                     # 例如 -16.0
y_end = top_y + shell_outer_radius     # 0 + 128 = 128
# 使用 np.arange 注意浮点精度问题，可改用 np.linspace，但 arange 对 step 更直观
y_vals = np.arange(y_start, y_end + step_size/2, step_size)  # +step/2 避免浮点截断

# ========== 计算每个 y_c 的点数 ==========
R_inner_sq = shell_inner_radius ** 2
R_outer_sq = shell_outer_radius ** 2
counts = []

for y_c in y_vals:
    total = 0.0
    for y_layer in layer_ys:
        dy_sq = (y_layer - y_c) ** 2
        high_r2 = R_outer_sq - dy_sq
        if high_r2 < 0:
            continue
        low_r2 = R_inner_sq - dy_sq

        r2_low = int(np.floor(low_r2)) + 1
        r2_high = int(np.floor(high_r2))

        if r2_low > r2_high:
            continue
        r2_low = max(r2_low, 0)
        r2_high = min(r2_high, max_r2)
        if r2_low <= r2_high:
            total += r2_counts[r2_low : r2_high + 1].sum()
    counts.append(total)

counts = np.array(counts)

# ========== 找最大值 ==========
max_idx = np.argmax(counts)
best_y = y_vals[max_idx]
best_count = counts[max_idx]

# ========== 绘图 ==========
plt.figure(figsize=(12, 6))
plt.plot(y_vals, counts, 'b-', linewidth=1.2, label='刷怪点数量')

# 标出关键线
plt.axvline(center_y, color='red', linestyle='--', label=f'几何中心 (y={center_y:.1f})')
plt.axvline(0, color='green', linestyle=':', label='顶层 (y=0)')

# 标出最大值点
plt.scatter([best_y], [best_count], color='purple', zorder=5, s=50)
plt.annotate(f'最佳点\n(y={best_y:.3f}, 点数={int(best_count)})',
             xy=(best_y, best_count),
             xytext=(best_y + 10, best_count * 0.9),
             arrowprops=dict(arrowstyle='->', color='purple'),
             fontsize=10,
             color='purple',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5))

# 标签和标题
plt.xlabel('球心高度 y（相对于顶层中心，单位：方块）')
plt.ylabel('球壳内可刷怪整数点数量')
plt.title('MC 刷怪塔：挂机高度 vs 刷怪点数量（高精度步长）')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

# ========== 输出结果 ==========
print(f"【配置】{num_layers}层 × {plane_width}×{plane_height}，层高{layer_spacing}")
print(f"【球壳】半径 {shell_inner_radius} ~ {shell_outer_radius}")
print(f"【步长】{step_size}")
print(f"【几何中心】y = {center_y}")
print(f"【最佳挂机高度】y = {best_y:.4f}（相对于顶层）")
print(f"【最大刷怪点数】{int(best_count)}")