import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import requests
from concurrent.futures import ThreadPoolExecutor

class LawTrackerClient:
    def __init__(self, root):
        self.root = root
        self.api_url = "http://localhost:5000/api"
        self.executor = ThreadPoolExecutor(4)
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("LawTracker v1.0")
        self.root.geometry("1000x800")
        
        # Control panel
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Загрузить документ", 
                command=self.upload_document).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Сравнить", 
                command=self.compare_documents).pack(side=tk.LEFT, padx=5)
        
        # Document list
        self.tree = ttk.Treeview(self.root, columns=("ID", "Filename"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Filename", text="Имя файла")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Result area
        self.result_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.status_var, bd=1, 
                relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)
    
    def upload_document(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Documents", "*.pdf *.docx *.txt")]
        )
        if filepath:
            future = self.executor.submit(
                self._upload_task, filepath
            )
            future.add_done_callback(self._upload_complete)
            self.status_var.set("Загрузка документа...")
    
    def _upload_task(self, filepath):
        with open(filepath, 'rb') as f:
            response = requests.post(
                f"{self.api_url}/upload",
                files={'file': f}
            )
        return response.json()
    
    def _upload_complete(self, future):
        try:
            result = future.result()
            self.tree.insert("", tk.END, values=(result['id'], result['filename']))
            self.status_var.set("Документ загружен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self.status_var.set("Ошибка загрузки")
    
    def compare_documents(self):
        selected = self.tree.selection()
        if len(selected) != 2:
            messagebox.showwarning("Ошибка", "Выберите 2 документа")
            return
            
        doc1_id = self.tree.item(selected[0])['values'][0]
        doc2_id = self.tree.item(selected[1])['values'][0]
        
        future = self.executor.submit(
            self._compare_task, doc1_id, doc2_id
        )
        future.add_done_callback(self._compare_complete)
        self.status_var.set("Сравнение документов...")
    
    def _compare_task(self, doc1_id, doc2_id):
        response = requests.post(
            f"{self.api_url}/compare",
            json={'doc1_id': doc1_id, 'doc2_id': doc2_id}
        )
        return response.json()
    
    def _compare_complete(self, future):
        try:
            result = future.result()
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result['html_diff'])
            self.status_var.set("Сравнение завершено")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self.status_var.set("Ошибка сравнения")

if __name__ == "__main__":
    root = tk.Tk()
    app = LawTrackerClient(root)
    root.mainloop()
