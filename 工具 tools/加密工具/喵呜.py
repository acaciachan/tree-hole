def text2b(text, zero_str="0", one_str="1"):
    binary = ''.join(format(byte, '08b') for byte in text.encode('utf-8'))
    custom_binary = binary.replace('0', zero_str).replace('1', one_str)
    return custom_binary

def b2text(custom_binary, zero_str="0", one_str="1"):
    binary = custom_binary.replace(zero_str, '0').replace(one_str, '1')
    bytes_list = [binary[i:i+8] for i in range(0, len(binary), 8)]
    byte_data = bytes(int(b, 2) for b in bytes_list)
    return byte_data.decode('utf-8')

original_text = ""
encrypted = "呜呜呜喵喵呜喵呜呜喵喵呜呜呜呜喵呜喵喵喵喵喵呜呜呜呜呜喵喵呜喵呜呜喵喵呜呜呜喵喵呜喵呜呜呜呜呜喵呜呜呜喵喵呜喵呜呜喵呜呜喵喵喵喵呜喵喵喵呜呜呜呜呜呜呜喵喵呜呜呜呜喵喵喵呜喵呜呜呜喵喵呜喵喵喵喵呜呜呜喵喵呜呜呜呜喵喵喵呜喵呜呜呜喵呜呜呜喵喵喵喵呜呜呜呜呜呜喵"
print(f"原始文本: {original_text}")
print(f"加密结果: {text2b(original_text, "喵", "呜")}")
print(f"解密结果: {b2text(encrypted, "喵", "呜")}")