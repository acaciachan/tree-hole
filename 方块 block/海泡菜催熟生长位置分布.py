import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

def plot_sea_pickle_growth():
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    fig = plt.figure(figsize=(12, 10))
    
    # 创建3D图形
    ax = fig.add_subplot(111, projection='3d')
    
    # 模拟生长区域
    xStart = -2
    span = 5
    zSpan = 1
    zOffSet = 0
    count = 0
    
    positions = []
    
    # 重现Java代码中的逻辑
    for x in range(span):
        for z in range(zSpan):
            endY = 2  # 相对高度
            for startY in range(endY - 2, endY):
                # 计算实际位置
                x_pos = xStart + x
                z_pos = -zOffSet + z
                y_pos = startY
                positions.append((x_pos, y_pos, z_pos))
        
        # 更新Z轴参数（菱形生长）
        if count < 2:
            zSpan += 2
            zOffSet += 1
        else:
            zSpan -= 2
            zOffSet -= 1
        count += 1
    
    # 转换为numpy数组便于绘图
    positions = np.array(positions)
    
    # 绘制所有可能生长的位置
    ax.scatter(positions[:, 0], positions[:, 2], positions[:, 1], 
               c='lightblue', s=100, alpha=0.7, label='可能生长位置')
    
    # 标记被催熟的中心位置
    ax.scatter(0, 0, 1, c='red', s=200, marker='*', label='被催熟的海泡菜')
    
    # 设置坐标轴标签
    ax.set_xlabel('X 轴')
    ax.set_ylabel('Z 轴')
    ax.set_zlabel('Y 轴')
    
    # 设置标题
    ax.set_title('海泡菜骨粉催熟生长区域\n（3D菱形分布）', fontsize=14)
    
    # 添加网格
    ax.grid(True, alpha=0.3)
    
    # 设置坐标轴范围
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_zlim(-1, 2)
    
    # 添加图例
    ax.legend()
    
    # 调整视角以便更好地观察
    ax.view_init(elev=20, azim=45)
    
    plt.tight_layout()
    plt.show()
    
    # 打印统计信息
    print(f"总共有 {len(positions)} 个可能生长位置")
    print("生长区域形状：3D菱形")
    print("X轴范围：-2 到 2")
    print("Y轴范围：0 到 1") 
    print("Z轴范围：中间宽两端窄的菱形")

def plot_2d_top_view():
    """绘制俯视图"""
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.figure(figsize=(10, 8))
    
    # 同样的逻辑计算位置，但只关注XZ平面
    xStart = -2
    span = 5
    zSpan = 1
    zOffSet = 0
    count = 0
    
    xz_positions = []
    
    for x in range(span):
        for z in range(zSpan):
            x_pos = xStart + x
            z_pos = -zOffSet + z
            xz_positions.append((x_pos, z_pos))
        
        if count < 2:
            zSpan += 2
            zOffSet += 1
        else:
            zSpan -= 2
            zOffSet -= 1
        count += 1
    
    xz_positions = np.array(xz_positions)
    
    # 绘制俯视图
    plt.scatter(xz_positions[:, 0], xz_positions[:, 1], 
                c='green', s=80, alpha=0.6, label='生长区域')
    plt.scatter(0, 0, c='red', s=150, marker='*', label='中心位置')
    
    plt.xlabel('X 轴')
    plt.ylabel('Z 轴')
    plt.title('海泡菜生长区域俯视图\n（菱形分布）')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

# 运行绘图
if __name__ == "__main__":
    plot_sea_pickle_growth()
    plot_2d_top_view()