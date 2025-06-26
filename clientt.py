
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import requests
import json

class PDFComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Comparator")
        self.root.geometry("900x600")
        
        self.server_url = "http://localhost:5001"
        self.timeout = 10
        
        self.style = ttk.Style()
        self.style.configure('TFrame', padding=5)
        self.style.configure('TButton', padding=5)
        
        self.create_widgets()
        self.load_documents_list()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Upload PDF", command=self.upload_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Delete Selected", command=self.delete_selected_document, style='Danger.TButton').pack(side=tk.RIGHT, padx=5)
        self.style.configure('Danger.TButton', foreground='red')
        
        # Documents list
        list_frame = ttk.LabelFrame(main_frame, text="Documents")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(list_frame, columns=('id', 'filename', 'date'), show='headings', selectmode='browse')
        self.tree.heading('id', text='ID', anchor=tk.CENTER)
        self.tree.heading('filename', text='Filename')
        self.tree.heading('date', text='Upload Date')
        
        self.tree.column('id', width=50, anchor=tk.CENTER)
        self.tree.column('filename', width=400)
        self.tree.column('date', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Comparison
        compare_frame = ttk.Frame(main_frame)
        compare_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(compare_frame, text="Document 1:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.doc1_combo = ttk.Combobox(compare_frame, state='readonly', width=50)
        self.doc1_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(compare_frame, text="Document 2:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.doc2_combo = ttk.Combobox(compare_frame, state='readonly', width=50)
        self.doc2_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Button(compare_frame, text="Compare", command=self.compare_documents).grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky=tk.NS)
        
        # Results
        result_frame = ttk.LabelFrame(main_frame, text="Results")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.result_text = ScrolledText(result_frame, wrap=tk.WORD, font=('Courier', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def load_documents_list(self):
        try:
            response = requests.get(
                f"{self.server_url}/documents",
                timeout=self.timeout
            )
            data = response.json()
            
            if data.get('success'):
                self.update_documents_tree(data['documents'])
                self.update_comboboxes(data['documents'])
            else:
                messagebox.showerror("Error", data.get('error', 'Unknown error'))
        
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid server response")
    
    def update_documents_tree(self, documents):
        self.tree.delete(*self.tree.get_children())
        for doc in documents:
            self.tree.insert('', tk.END, values=(
                doc['id'],
                doc['filename'],
                doc['upload_date']
            ))
    
    def update_comboboxes(self, documents):
        doc_list = [f"{doc['id']} - {doc['filename']}" for doc in documents]
        self.doc1_combo['values'] = doc_list
        self.doc2_combo['values'] = doc_list
        
        if doc_list:
            self.doc1_combo.current(0)
            if len(doc_list) > 1:
                self.doc2_combo.current(1)
    
    def upload_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not filepath:
            return
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath.split('/')[-1], f, 'application/pdf')}
                response = requests.post(
                    f"{self.server_url}/upload",
                    files=files,
                    timeout=self.timeout
                )
            
            data = response.json()
            if data.get('success'):
                messagebox.showinfo("Success", data.get('message', 'Uploaded'))
                self.load_documents_list()
            else:
                messagebox.showerror("Error", data.get('error', 'Upload failed'))
        
        except Exception as e:
            messagebox.showerror("Error", f"Upload error: {str(e)}")
    
    def compare_documents(self):
        doc1_str = self.doc1_combo.get()
        doc2_str = self.doc2_combo.get()
        
        if not doc1_str or not doc2_str:
            messagebox.showwarning("Warning", "Select two documents")
            return
        
        try:
            doc1_id = int(doc1_str.split(' - ')[0])
            doc2_id = int(doc2_str.split(' - ')[0])
            
            response = requests.post(
                f"{self.server_url}/compare",
                json={'doc1_id': doc1_id, 'doc2_id': doc2_id},
                timeout=self.timeout
            )
            
            data = response.json()
            if data.get('success'):
                self.show_results(data)
            else:
                messagebox.showerror("Error", data.get('error', 'Comparison failed'))
        
        except Exception as e:
            messagebox.showerror("Error", f"Comparison error: {str(e)}")
    
    def show_results(self, data):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "=== Results ===\n\n")
        self.result_text.insert(tk.END, f"Document 1: {data['doc1']}\n")
        self.result_text.insert(tk.END, f"Document 2: {data['doc2']}\n\n")
        self.result_text.insert(tk.END, f"Similarity: {data['similarity']:.2f}%\n")
        
        # Color coding
        similarity = data['similarity']
        if similarity > 75:
            color = 'green'
        elif similarity > 50:
            color = 'blue'
        elif similarity > 25:
            color = 'orange'
        else:
            color = 'red'
        
        self.result_text.tag_configure('similarity', foreground=color, font=('Courier', 10, 'bold'))
        self.result_text.tag_add('similarity', "4.0", "4.20")
    
    def delete_selected_document(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a document")
            return
        
        doc_id = self.tree.item(selected[0], 'values')[0]
        
        if messagebox.askyesno("Confirm", f"Delete document {doc_id}?"):
            try:
                response = requests.delete(
                    f"{self.server_url}/delete/{doc_id}",
                    timeout=self.timeout
                )
                
                data = response.json()
                if data.get('success'):
                    self.load_documents_list()
                else:
                    messagebox.showerror("Error", data.get('error', 'Delete failed'))
            
            except Exception as e:
                messagebox.showerror("Error", f"Delete error: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = PDFComparatorApp(root)
    root.mainloop()
