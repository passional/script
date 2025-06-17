import pandas as pd
import io
import streamlit as st # For potential error messages or logging

def parse_markdown_table_to_df(markdown_table_string: str):
    """
    Parses a Markdown table string into a Pandas DataFrame.
    Assumes the table has a header row and uses '|' delimiters.
    Handles potential empty lines or lines that are not part of the table.
    """
    if not markdown_table_string or not markdown_table_string.strip():
        return pd.DataFrame()

    lines = markdown_table_string.strip().split('\n')
    
    # Filter out lines that are not part of a typical markdown table structure
    # (e.g., separator lines like |---|---|)
    # and lines that don't contain the pipe character.
    table_lines = [line for line in lines if line.strip().startswith('|') and line.strip().endswith('|')]

    if not table_lines:
        # Fallback or attempt to read if it's a simple CSV-like structure within markdown
        try:
            # Try to read as if it's a CSV embedded in markdown, stripping pipes
            csv_like_lines = []
            for line in lines:
                if '|' in line: # A bit more lenient
                    cleaned_line = ",".join([cell.strip() for cell in line.strip().strip('|').split('|')])
                    csv_like_lines.append(cleaned_line)
            
            if csv_like_lines:
                # The first valid line is likely the header
                df = pd.read_csv(io.StringIO("\n".join(csv_like_lines)))
                # st.write("Debug: Parsed with CSV fallback", df) # For debugging
                return df
        except Exception as e:
            # st.error(f"Markdown table parsing (CSV fallback) failed: {e}") # For debugging
            pass # Fall through to simple split if CSV fails
        return pd.DataFrame() # Return empty if all attempts fail or no valid lines

    # Process lines that look like markdown table rows
    header = []
    data_rows = []

    # First valid table line is header
    header_line = table_lines.pop(0) # Remove header line
    header = [h.strip() for h in header_line.strip('|').split('|')]
    
    # Skip the separator line if present (usually the second line in table_lines if not filtered out)
    if table_lines and all(c in '-|: ' for c in table_lines[0]):
        table_lines.pop(0)

    for line in table_lines:
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if len(cells) == len(header): # Ensure row matches header length
            data_rows.append(cells)
        # else:
            # st.warning(f"Skipping malformed table row: {line}") # For debugging

    if not data_rows and not header: # If parsing failed to get any data
        return pd.DataFrame()
        
    try:
        df = pd.DataFrame(data_rows, columns=header)
    except Exception as e:
        # st.error(f"Error creating DataFrame from parsed table: {e}") # For debugging
        # Attempt to create DataFrame even if header is empty, pandas might handle it
        df = pd.DataFrame(data_rows) if data_rows else pd.DataFrame()
        
    return df

if __name__ == '__main__':
    # Example Usage for testing
    md_table1 = """
    | 画面序号 | 中文口播文案                     | 文生图提示词 (英文)                                  | 画面描述             |
    |----------|----------------------------------|------------------------------------------------------|----------------------|
    | 1        | 大家好，欢迎来到我的频道！         | "Friendly host waving hello, YouTube studio background" | 主播开场白           |
    | 2        | 今天我们来聊聊 Streamlit 的神奇之处。 | "Streamlit logo glowing, abstract tech background"     | 展示Streamlit Logo |
    """
    df1 = parse_markdown_table_to_df(md_table1)
    print("DF1:\n", df1)

    md_table2 = """
    | Header A | Header B |
    |---|---|
    | val1 | val2 |
    | val3 | val4 |
    """
    df2 = parse_markdown_table_to_df(md_table2)
    print("\nDF2:\n", df2)

    md_table3_no_separator = """
    | Col1 | Col2 | Col3 |
    |  A   |  B   |  C   |
    |  D   |  E   |  F   |
    """
    df3 = parse_markdown_table_to_df(md_table3_no_separator)
    print("\nDF3 (no separator):\n", df3)
    
    md_table4_malformed = """
    This is some text before the table.
    | Name  | Age |
    | Alice | 30  |
    | Bob   | 24  |Invalid Row
    | Carol | 29  | City   |  <- extra cell
    Another text after table.
    """
    df4 = parse_markdown_table_to_df(md_table4_malformed)
    print("\nDF4 (malformed):\n", df4) # Should try to parse valid rows

    md_table5_empty = ""
    df5 = parse_markdown_table_to_df(md_table5_empty)
    print("\nDF5 (empty):\n", df5)
    
    md_table6_only_header = "| H1 | H2 |\n|----|----|"
    df6 = parse_markdown_table_to_df(md_table6_only_header)
    print("\nDF6 (only header and separator):\n", df6)