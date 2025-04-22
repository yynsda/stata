import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind, chi2_contingency, shapiro, kstest,f_oneway, kruskal

st.set_page_config(page_title="差异性分析工具", page_icon="📊", layout="wide")
st.title("差异性分析工具")
st.write("上传数据文件，进行差异性分析。")
def highlight_p_value(val):
    try:
        if isinstance(val, str) and "<" not in val:
            p = float(val)
            if p < 0.05:
                return 'color: red; font-weight: bold'
    except:
        return ''
    return ''

def generate_test_data():
    np.random.seed(42)
    data = pd.DataFrame({
        "Age": np.random.randint(18, 65, size=100),
        "Weight": np.random.normal(loc=60, scale=10, size=100),
        "Height": np.random.normal(loc=170, scale=10, size=100),
        "Gender": np.random.choice([0, 1], size=100),
        "Education": np.random.choice([1, 2, 3], size=100),
        "GPA": np.random.choice([1, 2], size=100)
    })
    return data

def normality_test(data, column, n_threshold=5000):
    n = len(data[column].dropna())
    if n < n_threshold:
        stat, p_value = shapiro(data[column].dropna())
        method = "Shapiro-Wilk"
    else:
        stat, p_value = kstest(data[column].dropna(), 'norm')
        method = "Kolmogorov-Smirnov"
    return method, stat, p_value

def describe_data(data, column, normality_result):
    if normality_result["p_value"] > 0.05:
        mean = data[column].mean()
        std = data[column].std()
        return f"{mean:.2f} ± {std:.2f}"
    else:
        q1 = data[column].quantile(0.25)
        q3 = data[column].quantile(0.75)
        return f"({q1:.2f} , {q3:.2f})"

def generate_three_line_table(data, group_column, quantitative_columns, categorical_columns):
    groups = sorted(data[group_column].dropna().unique())
    results = []

    # 分组变量不作为分析变量
    quantitative_columns = [col for col in quantitative_columns if col != group_column]
    categorical_columns = [col for col in categorical_columns if col != group_column]

    # 定量变量分析
    for value_column in quantitative_columns:
        row = {"variable": value_column}
        method, stat, p_value_normal = normality_test(data, value_column)
        is_normal = p_value_normal > 0.05

        for group in groups:
            group_data = data[data[group_column] == group][value_column]
            if is_normal:
                mean = group_data.mean()
                std = group_data.std()
                row[str(group)] = f"{mean:.2f} ± {std:.2f}"
            else:
                q1 = group_data.quantile(0.25)
                q3 = group_data.quantile(0.75)
                row[str(group)] = f"({q1:.2f}, {q3:.2f})"

        if len(groups) == 2:
            group1_data = data[data[group_column] == groups[0]][value_column].dropna()
            group2_data = data[data[group_column] == groups[1]][value_column].dropna()
            if is_normal:
                test_stat, p_val = ttest_ind(group1_data, group2_data, equal_var=False)
                test_method = "T-test"
            else:
                test_stat, p_val = kstest(group1_data, group2_data)
                test_method = "Kolmogorov-Smirnov"
        else:
            group_data_list = [data[data[group_column] == group][value_column].dropna() for group in groups]
            if is_normal:
                test_stat, p_val = f_oneway(*group_data_list)
                test_method = "ANOVA"
            else:
                test_stat, p_val = kruskal(*group_data_list)
                test_method = "Kruskal-Wallis"

        row["p-vaule"] = f"{p_val:.4f}"
        row["methods"] = test_method
        results.append(row)

    # 定型变量处理
    for value_column in categorical_columns:
        # 总览行：合并为“总数 (100.0%)”
        total_row = {"variable": f"{value_column} (Total)"}
        for group in groups:
            group_data = data[data[group_column] == group][value_column]
            total = group_data.notna().sum()
            total_row[str(group)] = f"{total} (100.0%)"
        contingency_table = pd.crosstab(data[group_column], data[value_column])
        chi2_stat, p_val, dof, expected = chi2_contingency(contingency_table)
        total_row["p-vaule"] = f"{p_val:.4f}"
        total_row["methods"] = "Chi-square"
        results.append(total_row)

        # 子类别行
        categories = sorted(data[value_column].dropna().unique())
        for category in categories:
            row = {"variable": f"{value_column} = {category}"}
            for group in groups:
                group_data = data[(data[group_column] == group) & (data[value_column] == category)]
                count = len(group_data)
                total = len(data[data[group_column] == group])
                percentage = (count / total) * 100 if total > 0 else 0
                row[str(group)] = f"{count} ({percentage:.2f}%)"
            row["p-vaule"] = ""
            row["methods"] = ""
            results.append(row)

    return results

# 文件上传或生成测试数据
uploaded_file = st.file_uploader("上传数据文件（CSV格式）", type=["csv"])
if uploaded_file is None:
    st.write("未上传文件，使用测试数据进行演示。")
    data = generate_test_data()
else:
    data = pd.read_csv(uploaded_file)

st.write("数据预览：")
st.write(data.head())

# 用户选择定量变量
st.write("### 选择定量变量")
quantitative_columns = st.multiselect("请选择定量变量列", data.columns, key="quantitative")

# 自动识别未被选为定量的列为分类变量
auto_categorical_columns = [col for col in data.columns if col not in quantitative_columns]

# 过滤可作为“分组变量”的分类变量（类别数>=2）
group_candidates = [col for col in auto_categorical_columns if data[col].nunique() >= 2]

# 正态性检验
if quantitative_columns:
    st.write("### 正态性检验")
    for value_column in quantitative_columns:
        method, stat, p_value = normality_test(data, value_column)
        st.write(f"{value_column}：{method} 检验，统计量 = {stat:.4f}, p-vaule = {p_value:.4f}")

# 选择分组变量与分析变量
st.write("### 分组与分析设置")
group_column = st.selectbox("选择分组变量（只能选择分类变量）", group_candidates)
#analysis_columns = st.multiselect("选择分析数据列", quantitative_columns + auto_categorical_columns)

# 合法性检查
if group_column in quantitative_columns:
    st.error("分组变量不能为定量变量！")
#elif group_column in analysis_columns:
  #  st.error("分组变量不能同时是分析变量！")
#elif len(analysis_columns) == 0:
 #   st.error("请至少选择一个分析变量")
else:
    # 三线表结果
    st.write("### 三线表结果")
    # 自动识别分析变量（排除分组变量）
    analysis_quantitative = [col for col in quantitative_columns if col != group_column]
    analysis_categorical = [col for col in auto_categorical_columns if col != group_column]
    result_table = generate_three_line_table(data, group_column, analysis_quantitative, analysis_categorical)
    styled_table = pd.DataFrame(result_table).style.applymap(highlight_p_value, subset=["p-vaule"])
    st.dataframe(styled_table)

    # 差异性分析
  #  st.write("### 差异性分析结果")
  #  analysis_result = difference_analysis(data, group_column, quantitative_columns, auto_categorical_columns)
  #  if analysis_result:
  #      st.dataframe(pd.DataFrame(analysis_result))


    # 下载
    st.write("### 下载结果")
    csv = pd.DataFrame(result_table).to_csv(index=False, encoding='utf-8-sig')
    st.download_button("下载分析结果", data=csv, file_name="difference_analysis.csv", mime="text/csv;charset=utf-8-sig")
