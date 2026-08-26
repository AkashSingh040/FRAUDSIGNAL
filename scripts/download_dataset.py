import kagglehub
import os
import shutil
import zipfile

def main():
    print("Downloading IEEE-CIS Fraud Detection dataset via kagglehub...")
    try:
        path = kagglehub.competition_download('ieee-fraud-detection')
        print("Path to competition files:", path)
        
        # Check what files are inside the downloaded path
        raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        os.makedirs(raw_dir, exist_ok=True)
        
        for filename in os.listdir(path):
            filepath = os.path.join(path, filename)
            if filename.endswith(".zip"):
                print(f"Extracting {filename}...")
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(raw_dir)
            elif filename.endswith(".csv"):
                print(f"Copying {filename}...")
                shutil.copy(filepath, os.path.join(raw_dir, filename))
                
        print("Data download and extraction complete.")
        print("Contents of data/raw:")
        for f in os.listdir(raw_dir):
            print(f" - {f}")
    except kagglehub.exceptions.UnauthenticatedError:
        print("\nERROR: Kaggle authentication required.")
        print("Please authenticate using one of the following methods:")
        print("1. Set environment variables KAGGLE_USERNAME and KAGGLE_KEY")
        print("2. Run kagglehub.login() in an interactive Python session first.")
        print("Then try running this script again.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
