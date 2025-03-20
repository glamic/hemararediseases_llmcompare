import requests
import pandas as pd
import json
import os

#API
proxy_api_url = "XXX"
api_key = "XXX"
#api_key = "XXX"
model = "gpt-4o-2024-11-20"

def extract_json(text):
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def get_normalized_mapping(diagnoses_list):
    prompt = (
        """请帮我将下面相同、相似或意思接近的诊断归并为一个标准的诊断名称，要求满足以下规则：
1. 如果诊断名称中包含括号说明，请优先提取括号内的具体诊断名称作为标准名称。例如："风湿性疾病（如风湿性关节炎）"应提取"风湿性关节炎"用于归一化。
2. 标准名称不包含括号和多余说明，只保留诊断名称本身。
示例：输入诊断列表：["风湿性疾病（如风湿性关节炎）", "风湿性关节炎", "急性支气管炎"]。预期输出：{"风湿性疾病（如风湿性关节炎）": "风湿性关节炎", "风湿性关节炎": "风湿性关节炎", "急性支气管炎": "急性支气管炎"}
请只输出一个合法的 JSON 对象，键是原始诊断，值是归一化后的诊断名称，不要附加其他说明。
"""
        + "\n诊断列表：\n" + json.dumps(diagnoses_list, ensure_ascii=False)
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "专业的医学专家和数据处理助手"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(proxy_api_url, headers=headers, json=payload)
        response.raise_for_status()
    except Exception as e:
        print("调用 API 失败：", e)
        return {}
    
    try:
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("解析 API 返回结果失败：", e)
        print("返回内容：", response.text)
        return {}
    
    content = extract_json(content)
    
    try:
        mapping = json.loads(content)
    except Exception as e:
        print("JSON 解析错误：", e)
        print("返回内容：", content)
        mapping = {}
    
    return mapping

def main():
    input_excel = "inputfile.xlsx"
    output_excel = "outputfile.xlsx"
    temp_csv = "temp.csv"

    df = pd.read_excel(input_excel)
    diagnoses_columns = df.columns[2:12]
    patient_id_column = df.columns[0]
    mapping_cache = {}
    
    #CSV
    if os.path.exists(temp_csv):
        os.remove(temp_csv)
    df.head(0).to_csv(temp_csv, index=False, encoding="utf-8")
    print(f"已创建 CSV 文件并写入表头：{temp_csv}")

    # 按病历编号分组处理
    for patient_id, group in df.groupby(patient_id_column):
        diag_set = set()
        for idx in group.index:
            for col in diagnoses_columns:
                diag = str(df.at[idx, col]).strip()
                if diag and diag.lower() != "nan":
                    diag_set.add(diag)
        
        if not diag_set:
            mapping = {}
        else:
            diag_key = tuple(sorted(diag_set))
            if diag_key in mapping_cache:
                mapping = mapping_cache[diag_key]
            else:
                mapping = get_normalized_mapping(list(diag_set))
                mapping_cache[diag_key] = mapping
        
        # replacing
        for idx in group.index:
            for col in diagnoses_columns:
                orig_diag = str(df.at[idx, col]).strip()
                if orig_diag and orig_diag.lower() != "nan":
                    normalized_diag = mapping.get(orig_diag, orig_diag)
                    df.at[idx, col] = normalized_diag
        
        # writing CSV
        group.to_csv(temp_csv, mode='a', index=False, header=False, encoding="utf-8")
        print(f"病历编号 {patient_id} 归一化完成，并追加到 CSV 文件中。")
    
    print(f"所有病历的归一化结果已实时保存到 CSV 文件：{temp_csv}")
    
    #save
    df.to_excel(output_excel, index=False)
    print(f"最终归一化后的 Excel 文件已保存到：{output_excel}")

if __name__ == '__main__':
    main()

