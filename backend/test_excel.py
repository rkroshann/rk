import requests
import pandas as pd
import io

def test_excel_export():
    try:
        # Test the Excel export endpoint
        response = requests.get('http://localhost:5000/export_excel')
        
        if response.status_code == 200:
            print("✅ Excel export successful!")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")
            
            # Try to read the Excel file
            try:
                excel_data = io.BytesIO(response.content)
                excel_file = pd.ExcelFile(excel_data)
                
                print(f"Excel sheets: {excel_file.sheet_names}")
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_data, sheet_name=sheet_name)
                    print(f"\nSheet '{sheet_name}':")
                    print(f"  Rows: {len(df)}")
                    print(f"  Columns: {list(df.columns)}")
                    if len(df) > 0:
                        print(f"  First row: {df.iloc[0].to_dict()}")
                    else:
                        print("  (Empty sheet)")
                        
            except Exception as e:
                print(f"❌ Error reading Excel file: {e}")
                
        else:
            print(f"❌ Excel export failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_csv_export():
    try:
        # Test the CSV export endpoint
        response = requests.get('http://localhost:5000/export_csv')
        
        if response.status_code == 200:
            print("\n✅ CSV export successful!")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")
            print(f"CSV content:\n{response.text[:500]}...")
        else:
            print(f"\n❌ CSV export failed with status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to backend for CSV export")
    except Exception as e:
        print(f"\n❌ CSV export error: {e}")

if __name__ == "__main__":
    print("Testing Excel and CSV export functionality...")
    test_excel_export()
    test_csv_export() 