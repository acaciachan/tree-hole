import numpy as np
import scipy
from scipy.stats import binom

stage = 7
p = 1/6
c = 1/4096
rts = 3
limit = 10**7

age_values = np.arange(1, stage)
t = np.arange(1 , limit + 1)
results = {}
for age in age_values:
    t = np.arange(1 , limit + 1)  
    y = binom.pmf(age, t * rts, c * p)
    max = np.argmax(y)
    print(f"当等待时间为{t[max]}t时，可使 age = {age} 的比例取到最大值为 {y[max]}")
    
h = (1 - binom.cdf(stage - 1 , t * rts, c * p) )   / t
max = np.argmax(h)
print(f"定时收割周期为{t[max]}t时，取到最大的效率为{h[max]}")
