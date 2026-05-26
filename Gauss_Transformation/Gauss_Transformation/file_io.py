import os

def read_input_file(filepath):
    """读取 input.txt 提取 B, L, L0, L1"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"未找到输入文件: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        
    for line in lines:
        parts = line.split()
        try:
            floats = [float(x) for x in parts]
            if len(floats) >= 4:
                return floats[0], floats[1], floats[2], floats[3]
        except ValueError:
            continue
            
    raise ValueError("未能解析到包含 4 个有效大地数值的数据行。")

def write_output_file(filepath, results):
    """保存计算结果至 result2.txt"""
    headers = ["序号", "说明", "计算结果"]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(",".join(headers) + "\n")
        for item in results:
            f.write(f"{item[0]},{item[1]},{item[2]}\n")