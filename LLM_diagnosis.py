import openai
import pandas as pd
import time

#openAI API Key
client = openai.OpenAI(api_key="YOUR KEY")

#read Excel file
file_path = "your file.xlsx" 
df = pd.read_excel(file_path)

if "病例编号" not in df.columns or "入院记录" not in df.columns:
    raise ValueError("Excel 文件缺少必要的列：'病例编号' 和 '入院记录'")

model = "gpt-4o-2024-11-20"  #model
num_trials = 5  #repeat
num_diagnoses = 10  #10 diagnoses

results = []

for index, row in df.iterrows():
    case_id = row["病例编号"]
    case_text = row["入院记录"]

    for trial in range(1, num_trials + 1):
        print(f"正在处理病历 {case_id}，第 {trial} 次请求...")

        # **🔹 构造 Prompt**
        prompt = f"""
        请假设你是一名具有经验的专业医师，这是一份出院病历记录，请根据其内容提供最有可能的 10 个主诊断，
        主诊断的可能性按从大到小排序。
        
        病历记录：
        {case_text}

        请按如下格式返回（不需要额外解释）：
        1. 诊断1
        2. 诊断2
        3. 诊断3
        ...
        """

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )

            diagnosis_text = response.choices[0].message.content  
            diagnoses = diagnosis_text.split("\n")[:num_diagnoses]
            diagnoses = [diag.split(". ", 1)[-1] for diag in diagnoses]

            results.append([case_id, trial, case_text] + diagnoses)

        except Exception as e:
            print(f"处理病历 {case_id} 时出错：{e}")
        
        time.sleep(1)

output_file = "results.xlsx"
columns = ["病例编号", "重复次数", "入院记录"] + [f"诊断{i+1}" for i in range(num_diagnoses)]
df_results = pd.DataFrame(results, columns=columns)
df_results.to_excel(output_file, index=False)

print(f"结果已保存到 {output_file}")
