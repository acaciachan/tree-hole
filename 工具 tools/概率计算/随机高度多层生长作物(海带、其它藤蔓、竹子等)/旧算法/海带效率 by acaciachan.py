import numpy as np
import pandas as pd
from tqdm import tqdm

# 1.1 参数
p = 00.14 # 被随机刻选中后执行生长函数的概率
harvestTiming = 5 # 收获造成的无法生长的时间，单位为tick
choose = 1 / 4096 # 一次随机刻选中一个方块的概率
MaxHeight = 25
randomPerTime = 3

# 1.2 测试时间
startTime = 1
endTime = 7200

# 1.3 初始化数据存储表格
AllStates = np.zeros((endTime - startTime + 1, MaxHeight + 1)) #第1列存储时间(tick)，第2列开始存储各限高下的概率

# 2. 计算各限高下的概率，每个限高下每个时间点的概率和效率
for heightLimit in tqdm(range(1, MaxHeight+1)):
    FirstState = np.zeros(heightLimit+1) 
    FirstState[0] = 1
    for t in tqdm(range(startTime, endTime + 1)):
        Count=0
        for growLimit in range(1, heightLimit+1):
            # 生成状态转移矩阵(对于当前的高度)
            TM = np.zeros((heightLimit + 1 , heightLimit + 1))
            for i in range(heightLimit + 1):
                for j in range(heightLimit + 1):
                    if i == j and i <= growLimit and j <= growLimit :
                        TM[i, j] = 1 - choose * p # 矩阵主对角线元素代表状态不变的概率
                    elif i + 1 == j and i <= growLimit and j <= growLimit + 1 :
                        TM[i, j] = choose * p # 矩阵主对角线元素右侧的元素代表到下一个阶段的概率
                    else:
                        TM[i, j] = 0 # 其他元素为0，代表状态不转移到其他阶段
            TM[growLimit, growLimit] = 1  # 最后一个状态是吸收态
            # 迭代
            State = np.dot(FirstState, np.linalg.matrix_power(TM, t*randomPerTime)) #当前状态=初始状态·(状态转移矩阵)^n
            # 计算产量
            for column in range(heightLimit+1):
                if growLimit == heightLimit :
                    Count += column * State[column] * ( MaxHeight + 1 - heightLimit ) / MaxHeight
                else : 
                    Count += column * State[column] / MaxHeight
        #求所有限高下的加权产量之和
        AllStates[t-startTime, heightLimit] = Count #将当前状态State存入AllStates列表中
        AllStates[t-startTime, 0] = t

# 4. 计算效率
AllStatesEfficiency = np.zeros_like(AllStates)
for i in range(AllStates.shape[0]):
    for j in range(0, MaxHeight+1):
        if j == 0:
            AllStatesEfficiency[i, j] = AllStates[i, j] #时间原样复制
        else:
            AllStatesEfficiency[i, j] = AllStates[i, j] / (AllStates[i, 0] + harvestTiming) #效率=各阶段概率/(等待时间+收割时间)
print(f"calculate complete")

# 5. 数据导出
AllStates = pd.DataFrame(AllStates)
AllStates.columns = ['时间'] + [f'限高={i+1}' for i in range(MaxHeight)]

AllStatesEfficiency = pd.DataFrame(AllStatesEfficiency)
AllStatesEfficiency.columns = ['时间'] + [f'限高={i+1}' for i in range(MaxHeight)]

with pd.ExcelWriter('海带的产量与效率(时间={startTime}~{endTime},收割时间={harvestTiming}).xlsx'.format(startTime=startTime, endTime=endTime, harvestTiming=harvestTiming), engine='xlsxwriter') as writer:
    AllStates.to_excel(writer, sheet_name='期望产量', index=False)
    AllStatesEfficiency.to_excel(writer, sheet_name='收割效率', index=False)

print(f"file created")
