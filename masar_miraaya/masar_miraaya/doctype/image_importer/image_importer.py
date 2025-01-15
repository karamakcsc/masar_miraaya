import frappe
from frappe.model.document import Document
import zipfile
import os

class ImageImporter(Document):
    @frappe.whitelist()
    def execute(self):
        if self.attach:
            file_path = self.get_file_path()
            extract_to = self.unzip_file(file_path)
            done_folder_path = self.find_done_folder(extract_to)
            if done_folder_path:
                self.process_files_in_done_folder(done_folder_path)
            else:
                frappe.throw("The 'Done' folder was not found in the unzipped directory.")
            self.delete_unzipped_folder(extract_to)

    def get_file_path(self):
        file_doc = frappe.get_doc("File", {"file_url": self.attach})
        return file_doc.get_full_path()

    def unzip_file(self, zip_path):
        extract_to = os.path.join(frappe.get_site_path(), 'public', 'files', 'unzipped_files')
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return extract_to
    
    def find_done_folder(self, extract_to):
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    return root 
        return None

    def process_files_in_done_folder(self, done_folder_path):
        files_in_done = os.listdir(done_folder_path)
        if not files_in_done:
            frappe.throw("The 'Done' folder is empty.")
            return
        item_code_images = {}
        target_directory = os.path.join(frappe.get_site_path(), 'public', 'files')
        for file_name in files_in_done:
            source_file_path = os.path.join(done_folder_path, file_name)
            target_file_path = os.path.join(target_directory, file_name)
            if "_" in file_name:
                item_code, suffix = file_name.split("_", 1)
                suffix = suffix.split(".")[0] 
            else:
                frappe.throw(f"Invalid file name format: {file_name}. Expected format: 'ITEMCODE_SUFFIX.jpg'")
                continue

            if frappe.db.exists(self.upload_to, item_code):
                if item_code not in item_code_images:
                    item_code_images[item_code] = []
                
                item_code_images[item_code].append({
                    "suffix": suffix,
                    "file_path": source_file_path
                })
        for item_code, images in item_code_images.items():
            for image in images:
                file_url = self.attach_file_to_item(item_code, image["file_path"])
                
                if image["suffix"] == "1":
                    frappe.db.set_value(self.upload_to, item_code, "image", file_url)
    def attach_file_to_item(self, item_code, file_path ):
        with open(file_path, "rb") as file:
            file_content = file.read()
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_path.split("/")[-1]  ,
            "attached_to_doctype": "Item",
            "attached_to_name": item_code,
            "folder": "Home/Attachments",
            "custom_magento_sync": 1,
            "is_private": 0,
            "content":file_content
        })
        file_doc.insert(ignore_permissions=True)    
        return file_doc.file_url        
    def delete_unzipped_folder(self, extract_to):
        if os.path.exists(extract_to):
            for root, dirs, files in os.walk(extract_to, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if os.path.exists(dir_path):
                        os.rmdir(dir_path)
            os.rmdir(extract_to)   
    