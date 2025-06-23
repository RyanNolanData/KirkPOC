import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
from datetime import datetime
import re
import warnings
warnings.filterwarnings("ignore")

def parse_fixed_width_mmr(content):
    lines = content.strip().split('\n')
    data = []
    
    for line in lines:
        if not line.strip():
            continue
            
        
        pmt_date = line[0:6].strip()
        mbi = line[6:17].strip()
        ap_date_raw = line[17:].strip()
        ap_date = ap_date_raw[:10] if len(ap_date_raw) >= 10 else ""
        
        
        adj_rsn_cd = line[29:31].strip() if len(line) > 29 else ""
        
        
        if adj_rsn_cd:
            ma_raf = line[31:36].strip()
            risk_adj_pmt = line[36:50].strip()
            tot_ma_pmt = line[50:64].strip()
            rebates = line[64:78].strip()
        else:
            ma_raf = line[29:34].strip()
            risk_adj_pmt = line[34:48].strip()
            tot_ma_pmt = line[48:62].strip()
            rebates = line[62:76].strip()
        
        data.append({
            'PmtDate': pmt_date,
            'MBI': mbi,
            'APDate': ap_date,
            'AdjRsnCd': adj_rsn_cd,
            'MA_RAF': ma_raf,
            'RiskAdjPmt': risk_adj_pmt,
            'TotMAPmt': tot_ma_pmt,
            'Rebates': rebates
        })
    
    return pd.DataFrame(data)

def parse_pipe_delimited_mmr(content):
    df = pd.read_csv(StringIO(content), sep='|')
    return df

def format_date(date_str):
    """Format date to M/D/YYYY"""
    if not date_str or pd.isna(date_str):
        return ""
    
    
    date_str = str(date_str).strip()
    
    
    if ' ' in date_str:
        date_str = date_str.split(' ')[0]
    
    try:
    
        if '/' in date_str:
            dt = datetime.strptime(date_str, '%m/%d/%Y')
        else:
    
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        
        return f"{dt.month}/{dt.day}/{dt.year}"
    except:
        return date_str

def format_currency(amount):
    if not amount or pd.isna(amount) or str(amount).strip() == '':
        return "($ -  )"
    
    try:
        # Convert to float
        val = float(str(amount).replace(',', '').replace('$', '').replace('(', '').replace(')', '').strip())
        
        if val == 0:
            return "($ -  )"
        else:
            # Format with commas and 2 decimal places
            formatted = f"{val:,.2f}"
            return f"$ {formatted}"
    except:
        return "($ -  )"

def format_ma_raf(raf_value):
    """Format MA_RAF to 4 decimal places"""
    if not raf_value or pd.isna(raf_value):
        return ""
    
    try:
        val = float(str(raf_value).strip())
        return f"{val:.4f}"
    except:
        return str(raf_value)

def standardize_data(df):
    result_df = df.copy()
    
    result_df['APDate'] = result_df['APDate'].apply(format_date)
    
    result_df['MA_RAF'] = result_df['MA_RAF'].apply(format_ma_raf)

    result_df['RiskAdjPmt'] = result_df['RiskAdjPmt'].apply(format_currency)
    result_df['TotMAPmt'] = result_df['TotMAPmt'].apply(format_currency)
    result_df['Rebates'] = result_df['Rebates'].apply(format_currency)
   
    result_df = result_df.rename(columns={'TotMAPmt': 'TotalMAPmt'})
    
    result_df['AdjRsnCd'] = result_df['AdjRsnCd'].fillna('')
    
    return result_df

def main():
    st.title("MMR File Format Converter")
    st.write("Convert MMR files from different formats (Fixed-Width and Pipe-Delimited) to standardized output format")

    st.header("Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("MMR1 (Fixed-Width Format)")
        mmr1_file = st.file_uploader("Choose MMR1 file", type=['txt'], key="mmr1")
        
    with col2:
        st.subheader("MMR3 (Pipe-Delimited Format)")
        mmr3_file = st.file_uploader("Choose MMR3 file", type=['txt'], key="mmr3")
  
    converted_data = []
    
    if mmr1_file is not None:
        try:
            content = mmr1_file.read().decode('utf-8')
            df = parse_fixed_width_mmr(content)
            standardized_df = standardize_data(df)
            converted_data.append(("MMR1 (Fixed-Width)", standardized_df))
            st.success(f"✅ MMR1 file processed successfully! ({len(df)} records)")
        except Exception as e:
            st.error(f"❌ Error processing MMR1 file: {str(e)}")
    
    if mmr3_file is not None:
        try:
            content = mmr3_file.read().decode('utf-8')
            df = parse_pipe_delimited_mmr(content)
            standardized_df = standardize_data(df)
            converted_data.append(("MMR3 (Pipe-Delimited)", standardized_df))
            st.success(f"✅ MMR3 file processed successfully! ({len(df)} records)")
        except Exception as e:
            st.error(f"❌ Error processing MMR3 file: {str(e)}")
    
    # Display results
    if converted_data:
        st.header("Converted Data")
        
        for file_name, df in converted_data:
            st.subheader(f"{file_name}")
            st.dataframe(df, use_container_width=True)
            
            # Create Excel file in memory
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button(
                label=f"📥 Download {file_name} as Excel",
                data=buffer.getvalue(),
                file_name=f"{file_name.lower().replace(' ', '_')}_converted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Combined download if multiple files
        if len(converted_data) > 1:
            st.subheader("Combined Data")
            combined_df = pd.concat([df for _, df in converted_data], ignore_index=True)
            st.dataframe(combined_df, use_container_width=True)
            
            # Create combined Excel file in memory
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                combined_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Combined Data as Excel",
                data=buffer.getvalue(),
                file_name="mmr_combined_converted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with st.expander("📋 Instructions"):
        st.markdown("""
        ### How to use this tool:
        
        1. **Upload your MMR files** using the file uploaders above
           - **MMR1**: Fixed-width format file
           - **MMR3**: Pipe-delimited format file
        
        2. **View the converted data** in the standardized format below
        
        3. **Download the results** as Excel (XLSX) files
        
        ### Supported File Formats:
        - **Fixed-Width**: Data in fixed column positions
        - **Pipe-Delimited**: Data separated by | characters
        """)

if __name__ == "__main__":
    main()
