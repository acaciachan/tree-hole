
#由于我的方法运行程序的效率过低，故采推荐使用它的方案
#此部分海带的模拟的核心代码是由chen_yu_xuan编写的，以下是他的个人主页链接
#https://space.bilibili.com/67131398

import numpy
import matplotlib.pyplot as plt

#对象参数
harvesting_time = 0
p = 0.14 #每随机刻海带生长的概率
公摊高度 = 2
maxHeight = 25

#时间参数
time_start = 1
time_end = 72000
time_step = 1

#定义状态转移矩阵，不断地往左上角转移
P = numpy.zeros((maxHeight+2,maxHeight+2))
P[0,0] = P[-1,-1] = 1
for i in range(maxHeight):
    P[i+1,i+1] = 1-p/4096 #每tick不变的概率
    P[i+1,i] = p/4096 #每tick变化的概率
    P[i+1,-1] = p/4096 # 最后一列是产量
P3=P@P@P

产量表 = []
效率表 = []
体积效率表 = []

for 限高 in range(1,maxHeight+1): #对于每一个限高
    #生成该限高下的初始状态概率矩阵
    S = numpy.zeros((1,maxHeight+2)) #在最后有额外一个表示产量的数
    for 可生长高度 in range(1,26): #
        S[0,min(限高,可生长高度)] += 1 / maxHeight
    #print(概率分布)
    #计算每个时间下的状态概率
    当前限高的产量表 = []
    当前限高的效率表 = []
    当前限高的体积效率表 = []
    for tickedtime in range(time_start,time_end+1,time_step): 
        S = S@P3
        #print(概率分布)
        产量 = S[0,-1] #第一行最后一列
        #保存每一个时间的数据
        当前限高的产量表.append(产量)
        当前限高的效率表.append(产量/(tickedtime+harvesting_time))
        当前限高的体积效率表.append(产量/(tickedtime+harvesting_time)/(限高+公摊高度))
    #汇总每个限高的数据
    产量表.append(当前限高的产量表)
    效率表.append(当前限高的效率表)
    体积效率表.append(当前限高的体积效率表)
    #print(产量图)
    #print(效率图)
    #print(体积效率图)


# 画所有图在一个窗口里
print("左上角(↖)是产量图，右上角(↗)是效率图，左下角(↙)是体积效率图")
fig, axs = plt.subplots(2, 2, figsize=(10, 15))  # 2行2列的子图，调整 figsize 以适应你的需求
for 当前限高的产量表 in 产量表:
    axs[0, 0].plot(range(len(当前限高的产量表)), 当前限高的产量表)
for 当前限高的效率表 in 效率表:
    axs[0, 1].plot(range(len(当前限高的效率表)), 当前限高的效率表)
for 当前限高的体积效率表 in 体积效率表:
    axs[1, 0].plot(range(len(当前限高的体积效率表)), 当前限高的体积效率表)
plt.tight_layout()
plt.show()
