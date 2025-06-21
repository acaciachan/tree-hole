import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math

def clamp(value, min_value, max_value): # 夹子
    return max(min_value, min(value, max_value))

def timeOfDay(t): 
    d = (t / 24000.0 - 0.25) % 1.0  # %1.0 用来只取小数部分
    e = 0.5 - np.cos(d * np.pi) / 2.0
    return (d * 2.0 + e) / 3.0

def SkyBrightness(rain_level, thunder_level, time_of_day):

    d = 1.0 - rain_level * 5.0 / 16.0
    e = 1.0 - thunder_level * 5.0 / 16.0

    # 计算由于时间（一天中的不同时刻）导致的天空亮度变化
    f = 0.5 + 2.0 * clamp(math.cos(time_of_day * (math.pi * 2)), -0.25, 0.25)
    
    # 计算最终的天空变暗程度
    sky_darken = int((1.0 - f * d * e) * 11.0)
    
    return sky_darken

# 生成数据
time_values = np.array(range(0, 48000+1, 1))
timeOfDay_values = [timeOfDay(t) for t in time_values]
skyBrightness_values = [SkyBrightness(0, 0, timeOfDay) for timeOfDay in timeOfDay_values]

# 导出数据
df = pd.DataFrame({
    'time': time_values,
    'timeOfDay': timeOfDay_values,
    'skyBrightness': skyBrightness_values
})

df.to_csv('timeOfDay_and_skyBrightness.csv', index=False)

print("CSV文件已导出")

# 绘制图像
plt.plot(time_values, timeOfDay_values, label='timeOfDay')
plt.plot(time_values, skyBrightness_values, label='SkyBrightness')
plt.title('Time of Day and Sky Brightness Relationship')
plt.xlabel('Game Time (Ticks)')
plt.ylabel('Normalized Value / Brightness Level')
plt.grid(True)
plt.legend()
plt.show()
