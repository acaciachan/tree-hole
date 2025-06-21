import random
import numpy as np

def text2b(text, zero_str="0", one_str="1", noise_list=['#', '$', '@', '&'], poisson_lambda=5):
    """
    text: 输入文本
    zero_str: 替换0的字符串
    one_str: 替换1的字符串
    noise_list: 干扰字符串列表
    poisson_lambda: 泊松分布的期望值(平均每多少个字符插入一个干扰字符串)
    """
    # 将文本转换为二进制
    binary = ''.join(format(byte, '08b') for byte in text.encode('utf-8'))
    custom_binary = binary.replace('0', zero_str).replace('1', one_str)
    
    # 生成泊松分布的间隔序列
    result = []
    pos = 0
    
    while pos < len(custom_binary):
        # 生成下一次插入的间隔（泊松分布）
        interval = np.random.poisson(poisson_lambda)
        if interval == 0:  # 防止间隔为0
            interval = 1
            
        # 添加正常字符
        end_pos = min(pos + interval, len(custom_binary))
        result.append(custom_binary[pos:end_pos])
        
        # 如果还没到末尾，添加随机干扰字符串
        if end_pos < len(custom_binary):
            result.append(random.choice(noise_list))
        
        pos = end_pos
    
    return ''.join(result)

def b2text(custom_binary, zero_str="0", one_str="1", noise_list=['#', '$', '@', '&']):
    """
    custom_binary: 加密后的字符串
    zero_str: 替换0的字符串
    one_str: 替换1的字符串
    noise_list: 干扰字符串列表（未直接使用，但保留参数以保持接口一致）
    """
    # 初始化结果二进制字符串
    binary = ''
    i = 0
    
    # 逐个读取 zero_str 和 one_str
    while i < len(custom_binary):
        if custom_binary.startswith(zero_str, i):
            binary += '0'
            i += len(zero_str)
        elif custom_binary.startswith(one_str, i):
            binary += '1'
            i += len(one_str)
        else:
            # 跳过非 zero_str 和 one_str 的部分（即噪声）
            i += 1
    
    # 将二进制转换回字节
    bytes_list = [binary[i:i+8] for i in range(0, len(binary), 8)]
    byte_data = bytes(int(b, 2) for b in bytes_list)
    
    return byte_data.decode('utf-8')

# 示例
noise_list = ['❤', '嗯❤啊~', '❤嗯啊~', '嗯啊❤~', '嗯❤~', '啊❤~', '❤嗯~', '啊❤~']
original_text = ""
encrypted = "呜呜呜喵喵呜喵呜呜啊❤~喵喵呜呜呜呜喵嗯❤~呜喵喵喵喵喵❤呜呜❤嗯~呜呜呜喵喵呜❤喵呜呜啊❤~喵喵呜呜呜啊❤~喵喵❤嗯啊~呜喵呜❤嗯~呜呜呜呜❤嗯~喵呜❤嗯~呜呜喵❤嗯啊~喵呜嗯❤~喵啊❤~呜呜喵呜呜喵啊❤~喵喵喵呜啊❤~喵喵喵啊❤~呜呜呜呜呜嗯❤~呜呜喵喵呜呜❤嗯啊~呜呜喵喵喵呜嗯❤~喵呜呜呜嗯❤啊~喵喵呜啊❤~喵喵啊❤~喵喵呜嗯❤~呜呜喵嗯❤~喵呜呜嗯❤啊~呜呜喵喵喵啊❤~呜喵啊❤~呜呜呜喵嗯❤啊~呜呜呜嗯❤啊~喵喵喵"

print(f"原始文本: {original_text}")
print(f"加密结果: {text2b(original_text, '喵', '呜', noise_list, poisson_lambda=4)}")
print(f"解密结果: {b2text(encrypted, '喵', '呜', noise_list)}")