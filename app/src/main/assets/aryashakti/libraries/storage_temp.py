import os
import tempfile
from import_export.tmp_storages import TempFolderStorage

class CustomTmpStorage(TempFolderStorage):
    def __init__(self, *, name=None, read_mode="rb", encoding=None):
        """
        Custom temporary storage that overrides TempFolderStorage.
        Ensures a specific directory is used for temporary files.
        """
        self.temp_dir = "/code/tmp"  # Define the custom directory
        os.makedirs(self.temp_dir, exist_ok=True)  # Ensure directory exists
        
        self.name = name  # Store file name
        self.read_mode = read_mode  # Store read mode
        self.encoding = encoding  # Store encoding if needed

        print(f"[DEBUG] Temp storage directory set to: {self.temp_dir}")
        print(f"[DEBUG] Directory exists: {os.path.exists(self.temp_dir)}")

        super().__init__(name=self.name, read_mode=self.read_mode, encoding=self.encoding)

    def save(self, data):
        """Save data to a temporary file."""
        if not self.name:
            _, self.name = tempfile.mkstemp(dir=self.temp_dir)  # Generate a unique temp file
        
        file_path = os.path.join(self.temp_dir, self.name)

        try:
            # Ensure data is bytes before writing
            if isinstance(data, bytes):
                file_data = data
            else:
                file_data = data.read()  # Read file-like object as bytes

            with open(file_path, "wb") as f:
                f.write(file_data)

            print(f"[SUCCESS] File saved successfully at {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save file: {e}")
            raise

    def read(self):
        """Read the temporary file."""
        if not self.name:
            raise FileNotFoundError("[ERROR] No file name set to read.")

        file_path = os.path.join(self.temp_dir, self.name)

        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"[DEBUG] Opening file: {file_path}")
        with open(file_path, self.read_mode, encoding=self.encoding) as f:
            return f.read()

    def remove(self):
        """Remove the temporary file."""
        if not self.name:
            return
        
        file_path = os.path.join(self.temp_dir, self.name)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[SUCCESS] File deleted: {file_path}")
            else:
                print(f"[WARNING] File already deleted or not found: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to delete file: {e}")

    def get_full_path(self):
        """Return the full path of the temporary file."""
        if not self.name:
            return None
        return os.path.join(self.temp_dir, self.name)
