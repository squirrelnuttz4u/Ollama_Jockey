import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from tkinter.simpledialog import askstring
import threading
import time
import psutil
import json
import requests
import sqlite3
from datetime import datetime
import itertools
import os

# --- Optional GPU Monitoring ---
try:
    import pynvml
    pynvml.nvmlInit()
    PYNML_AVAILABLE = True
except (ImportError, pynvml.NVMLError):
    PYNML_AVAILABLE = False

# --- Optional Excel Export ---
try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

# --- Optional Charting ---
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# --- Configuration for Themes ---
THEMES = {
    "Light": {
        "bg": "#FFFFFF", "fg": "#000000", "notebook_bg": "#F0F0F0",
        "button_bg": "#E0E0E0", "button_fg": "#000000", "text_bg": "#FFFFFF",
        "text_fg": "#000000", "accent": "#3b82f6", "selected_fg": "#FFFFFF"
    },
    "Dark": { # Overhauled for better contrast
        "bg": "#1e1e1e", "fg": "#d4d4d4", "notebook_bg": "#252526",
        "button_bg": "#3e3e42", "button_fg": "#ffffff", "text_bg": "#1e1e1e",
        "text_fg": "#d4d4d4", "accent": "#007acc", "selected_fg": "#FFFFFF"
    },
    "Midnight Copper": {
        "bg": "#1a140f", "fg": "#e6dcd1", "notebook_bg": "#2a241f",
        "button_bg": "#b87333", "button_fg": "#000000", "text_bg": "#0d0d0d",
        "text_fg": "#d7a98c", "accent": "#d7a98c", "selected_fg": "#000000"
    },
    "Patriotic": {
        "bg": "#f8fafc", "fg": "#111827", "notebook_bg": "#E0E0E0",
        "button_bg": "#B22234", "button_fg": "#FFFFFF", "text_bg": "#FFFFFF",
        "text_fg": "#3C3B6E", "accent": "#1d4ed8", "selected_fg": "#FFFFFF"
    },
    "Obsidian": {
        "bg": "#0f0f12", "fg": "#f0f0f5", "notebook_bg": "#1a1c1e",
        "button_bg": "#3b444b", "button_fg": "#e1e1e1", "text_bg": "#101214",
        "text_fg": "#d1d1d1", "accent": "#8b5cf6", "selected_fg": "#FFFFFF"
    },
    "Pastel Pink": {
        "bg": "#fdf2f8", "fg": "#500724", "notebook_bg": "#fce4ec",
        "button_bg": "#f48fb1", "button_fg": "#000000", "text_bg": "#fff8f9",
        "text_fg": "#3e2723", "accent": "#db2777", "selected_fg": "#FFFFFF"
    },
    "Neon Stalker": {
        "bg": "#0a0f21", "fg": "#e0e0ff", "notebook_bg": "#101531",
        "button_bg": "#ff00ff", "button_fg": "#000000", "text_bg": "#050A1A",
        "text_fg": "#00ffff", "accent": "#00ffff", "selected_fg": "#000000"
    },
    "Vintage Terminal": {
        "bg": "#000000", "fg": "#33ff33", "notebook_bg": "#111111",
        "button_bg": "#222222", "button_fg": "#33ff33", "text_bg": "#080808",
        "text_fg": "#33ff33", "accent": "#55ff55", "selected_fg": "#000000"
    }
}

# --- Database Manager ---
class DatabaseManager:
    """Handles all SQLite database operations."""
    def __init__(self, db_name="llama_jockey.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                parameters TEXT,
                ttft_ms REAL,
                tps REAL,
                total_tokens INTEGER,
                total_time_s REAL,
                quality_score REAL,
                telemetry_snapshot TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS arena_battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_a TEXT NOT NULL,
                model_b TEXT NOT NULL,
                prompt TEXT,
                winner TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_ratings (
                model_name TEXT PRIMARY KEY,
                rating INTEGER NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT,
                UNIQUE(name, version)
            )
        """)
        self.conn.commit()

    def add_benchmark_log(self, data):
        try:
            self.cursor.execute("""
                INSERT INTO benchmarks (timestamp, model, parameters, ttft_ms, tps, total_tokens, total_time_s, quality_score, telemetry_snapshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['timestamp'], data['model'], data['parameters'], data.get('ttft_ms'),
                data.get('tps'), data.get('total_tokens'), data.get('total_time_s'),
                data.get('quality_score'), data['telemetry_snapshot']
            ))
            self.conn.commit()
        except Exception as e:
            print(f"DATABASE ERROR: Failed to write benchmark log: {e}")


    def add_arena_log(self, model_a, model_b, prompt, winner):
        self.cursor.execute("""
            INSERT INTO arena_battles (timestamp, model_a, model_b, prompt, winner)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), model_a, model_b, prompt, winner))
        self.conn.commit()
    
    def get_all_benchmarks(self):
        self.cursor.execute("SELECT id, timestamp, model, parameters, ttft_ms, tps, total_tokens, total_time_s, quality_score FROM benchmarks ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def get_optimal_setting(self, objective):
        if objective == "Maximize TPS":
            query = "SELECT * FROM benchmarks WHERE tps IS NOT NULL ORDER BY tps DESC LIMIT 1"
        elif objective == "Minimize TTFT":
            query = "SELECT * FROM benchmarks WHERE ttft_ms IS NOT NULL AND ttft_ms > 0 ORDER BY ttft_ms ASC LIMIT 1"
        else:
            return None
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def get_rating(self, model_name):
        self.cursor.execute("SELECT rating FROM model_ratings WHERE model_name = ?", (model_name,))
        result = self.cursor.fetchone()
        return result[0] if result else 1000 # Default Elo rating

    def update_ratings(self, model_a, rating_a, model_b, rating_b):
        self.cursor.execute("INSERT OR REPLACE INTO model_ratings (model_name, rating) VALUES (?, ?)", (model_a, rating_a))
        self.cursor.execute("INSERT OR REPLACE INTO model_ratings (model_name, rating) VALUES (?, ?)", (model_b, rating_b))
        self.conn.commit()
        
    def get_all_ratings(self):
        self.cursor.execute("SELECT model_name, rating FROM model_ratings ORDER BY rating DESC")
        return self.cursor.fetchall()

    def get_all_prompts(self):
        self.cursor.execute("SELECT id, name, version FROM prompts ORDER BY name, version")
        return self.cursor.fetchall()
    
    def get_prompt_content(self, prompt_id):
        self.cursor.execute("SELECT content FROM prompts WHERE id = ?", (prompt_id,))
        result = self.cursor.fetchone()
        return result[0] if result else ""
        
    def save_prompt(self, name, version, content, prompt_id=None):
        if prompt_id:
            self.cursor.execute("UPDATE prompts SET name = ?, content = ? WHERE id = ?", (name, content, prompt_id))
        else:
            self.cursor.execute("INSERT INTO prompts (name, version, content) VALUES (?, ?, ?)", (name, version, content))
        self.conn.commit()

    def get_latest_prompt_version(self, name):
        self.cursor.execute("SELECT MAX(version) FROM prompts WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] is not None else 0

    def delete_prompt(self, prompt_id):
        self.cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        self.conn.commit()

    def clear_all_data(self):
        """Drops all tables and recreates them."""
        self.cursor.execute("DROP TABLE IF EXISTS benchmarks")
        self.cursor.execute("DROP TABLE IF EXISTS arena_battles")
        self.cursor.execute("DROP TABLE IF EXISTS model_ratings")
        self.cursor.execute("DROP TABLE IF EXISTS prompts")
        self.conn.commit()
        self.setup_tables()

    def close(self):
        self.conn.close()

# --- Ollama Client ---
class OllamaClient:
    """A client for interacting with an Ollama server."""
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def list_models(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return response.json().get("models", [])
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return None

    def generate(self, model_name, prompt, options=None):
        payload = {"model": model_name, "prompt": prompt, "stream": True}
        if options:
            payload["options"] = options
        try:
            with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        yield json.loads(line.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            yield {"error": f"Failed to generate: {e}"}


class LlamaJockeyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Colt's LLama Jockey v1.0 beta - © 2025 Colt McVey")
        self.config_file = "jockey_config.json"
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.geometry(config.get("geometry", "1200x800"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.geometry("1200x800")


        self.db = DatabaseManager()

        self.ollama_server = tk.StringVar(value="http://localhost:11434")
        self.current_theme = tk.StringVar(value="Dark")
        self.selected_model = tk.StringVar()
        self.benchmark_suite = tk.StringVar(value="Raw Performance")
        self.arena_model_a = tk.StringVar()
        self.arena_model_b = tk.StringVar()
        self.jockeys_edge_objective = tk.StringVar(value="Maximize TPS")
        
        self.param_temperature = tk.StringVar(value="0.7")
        self.param_num_ctx = tk.StringVar(value="2048")
        self.param_top_k = tk.StringVar(value="40")
        self.param_top_p = tk.StringVar(value="0.9")
        self.param_num_thread = tk.StringVar(value="")
        self.param_num_gpu = tk.StringVar(value="")
        self.param_num_batch = tk.StringVar(value="")
        self.param_num_predict = tk.StringVar(value="")
        self.param_mmap = tk.StringVar(value="Default")

        self.analysis_model = tk.StringVar()
        self.analysis_x_axis = tk.StringVar(value="temperature")
        self.analysis_y_axis = tk.StringVar(value="TPS")

        self.is_benchmarking = False
        self.is_generating = False
        self.is_in_arena_battle = False
        
        self.current_telemetry = {}
        self.ollama_client = OllamaClient(self.ollama_server.get())
        self.style = ttk.Style(self)
        self.setup_tabs()
        self.setup_telemetry_display()
        self.apply_theme()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.stop_telemetry_event = threading.Event()
        self.stop_benchmark_event = threading.Event()
        self.telemetry_thread = threading.Thread(target=self.update_telemetry, daemon=True)
        self.telemetry_thread.start()

        self.after(100, lambda: self.refresh_models(show_error_popup=False))

    def setup_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        self.benchmark_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)
        self.arena_tab = ttk.Frame(self.notebook)
        self.leaderboard_tab = ttk.Frame(self.notebook)
        self.prompt_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.benchmark_tab, text='Benchmarking')
        self.notebook.add(self.history_tab, text='History Viewer')
        self.notebook.add(self.analysis_tab, text='Analysis')
        self.notebook.add(self.arena_tab, text='Arena')
        self.notebook.add(self.leaderboard_tab, text='Leaderboard')
        self.notebook.add(self.prompt_tab, text='Prompt Paddock')
        self.notebook.add(self.settings_tab, text='Settings')
        self.populate_benchmark_tab()
        self.populate_history_tab()
        self.populate_analysis_tab()
        self.populate_arena_tab()
        self.populate_leaderboard_tab()
        self.populate_prompt_tab()
        self.populate_settings_tab()

    def populate_benchmark_tab(self):
        main_frame = ttk.Frame(self.benchmark_tab, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        controls_frame = ttk.LabelFrame(main_frame, text="Test Configuration")
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=5)
        
        ttk.Label(controls_frame, text="Test Suite:").pack(side="left", padx=5, pady=5)
        ttk.OptionMenu(controls_frame, self.benchmark_suite, "Raw Performance", "Raw Performance", "Reasoning Test", "Instruction Following").pack(side="left", padx=5, pady=5)
        
        ttk.Label(controls_frame, text="Model:").pack(side="left", padx=5, pady=5)
        self.model_menu = ttk.OptionMenu(controls_frame, self.selected_model, "No models found")
        self.model_menu.pack(side="left", padx=5, pady=5)
        self.refresh_button = ttk.Button(controls_frame, text="Refresh Models", command=lambda: self.refresh_models(show_error_popup=True))
        self.refresh_button.pack(side="left", padx=5, pady=5)
        self.run_button = ttk.Button(controls_frame, text="Run Test", command=self.start_benchmark_thread)
        self.run_button.pack(side="left", padx=20, pady=5)
        self.stop_button = ttk.Button(controls_frame, text="Stop Test", command=self.stop_benchmark_thread, state="disabled")
        self.stop_button.pack(side="left", padx=5, pady=5)

        param_frame = ttk.LabelFrame(main_frame, text="Parameter Matrix (use comma-separated values for numeric fields)")
        param_frame.grid(row=1, column=0, sticky="ew", pady=(0,10), padx=5)
        param_frame.columnconfigure(1, weight=1)
        param_frame.columnconfigure(3, weight=1)
        
        ttk.Label(param_frame, text="Temperature:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_temperature).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Context Window (num_ctx):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_num_ctx).grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Top K:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_top_k).grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Top P:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_top_p).grid(row=1, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Threads (num_thread):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_num_thread).grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="GPU Layers (num_gpu):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_num_gpu).grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Batch Size (num_batch):").grid(row=2, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_num_batch).grid(row=2, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Max Tokens (num_predict):").grid(row=3, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(param_frame, textvariable=self.param_num_predict).grid(row=3, column=3, padx=5, pady=2, sticky="ew")
        ttk.Label(param_frame, text="Memory Map (mmap):").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        ttk.OptionMenu(param_frame, self.param_mmap, "Default", "Default", "Enabled", "Disabled").grid(row=4, column=1, padx=5, pady=2, sticky="w")
        ttk.Button(param_frame, text="Help with Parameters", command=self.show_help_window).grid(row=4, column=3, padx=5, pady=5, sticky="e")
        
        edge_frame = ttk.LabelFrame(main_frame, text="Jockey's Edge Recommender")
        edge_frame.grid(row=2, column=0, sticky="ew", pady=(0,10), padx=5)
        edge_frame.columnconfigure(2, weight=1)

        ttk.Label(edge_frame, text="Optimization Goal:").pack(side="left", padx=5, pady=5)
        objectives = ["Maximize TPS", "Minimize TTFT"]
        ttk.OptionMenu(edge_frame, self.jockeys_edge_objective, objectives[0], *objectives).pack(side="left", padx=5, pady=5)
        ttk.Button(edge_frame, text="Find Optimal Setting", command=self.run_jockeys_edge_analysis).pack(side="left", padx=5, pady=5)
        self.jockeys_edge_result = scrolledtext.ScrolledText(edge_frame, wrap=tk.WORD, height=4, state="disabled")
        self.jockeys_edge_result.pack(side="left", expand=True, fill="x", padx=5, pady=5)

        results_frame = ttk.LabelFrame(main_frame, text="Benchmark Log")
        results_frame.grid(row=3, column=0, sticky="nsew", padx=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        export_md_button = ttk.Button(results_frame, text="Export to Markdown", command=lambda: self.export_benchmarks('md'))
        export_md_button.pack(side="right", anchor="ne", padx=5, pady=5)
        export_excel_button = ttk.Button(results_frame, text="Export to Excel", command=lambda: self.export_benchmarks('xlsx'))
        export_excel_button.pack(side="right", anchor="ne", padx=5, pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, state="disabled")
        self.results_text.pack(expand=True, fill="both", padx=5, pady=(0,5))
        
        self.progress_bar = ttk.Progressbar(results_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=(0,5))


    def populate_history_tab(self):
        main_frame = ttk.Frame(self.history_tab, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(controls_frame, text="Refresh History", command=self.load_history_data).pack(side="left")

        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("ID", "Timestamp", "Model", "Parameters", "TTFT (ms)", "TPS", "Tokens", "Time (s)", "Quality (%)")
        self.history_tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
        
        for col in cols:
            self.history_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.history_tree, c, False))
            self.history_tree.column(col, width=100, anchor="center")
        
        self.history_tree.column("Parameters", width=200, anchor="w")
        self.history_tree.column("Timestamp", width=150, anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.history_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew')
        self.history_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.history_tree.grid(row=0, column=0, sticky="nsew")

        self.after(200, self.load_history_data)

    def load_history_data(self):
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)
        
        records = self.db.get_all_benchmarks()
        for row in records:
            formatted_row = list(row)
            formatted_row[4] = f"{row[4]:.2f}" if row[4] is not None else "N/A"
            formatted_row[5] = f"{row[5]:.2f}" if row[5] is not None else "N/A"
            formatted_row[8] = f"{row[8]:.2f}" if row[8] is not None else "N/A"
            self.history_tree.insert("", "end", values=formatted_row)

    def populate_analysis_tab(self):
        main_frame = ttk.Frame(self.analysis_tab, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(main_frame, text="Matplotlib is not installed. Please run 'pip install matplotlib' to enable charting.", style="Error.TLabel").pack(pady=20)
            return

        controls_frame = ttk.LabelFrame(main_frame, text="Chart Configuration")
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(controls_frame, text="Model:").pack(side="left", padx=5, pady=5)
        self.analysis_model_menu = ttk.OptionMenu(controls_frame, self.analysis_model, "Select Model")
        self.analysis_model_menu.pack(side="left", padx=5, pady=5)

        ttk.Label(controls_frame, text="X-Axis (Parameter):").pack(side="left", padx=5, pady=5)
        x_options = ["temperature", "num_ctx", "top_k", "top_p", "num_thread", "num_gpu", "num_batch", "num_predict", "mmap"]
        ttk.OptionMenu(controls_frame, self.analysis_x_axis, x_options[0], *x_options).pack(side="left", padx=5, pady=5)

        ttk.Label(controls_frame, text="Y-Axis (Metric):").pack(side="left", padx=5, pady=5)
        y_options = ["TPS", "TTFT", "Quality Score"]
        ttk.OptionMenu(controls_frame, self.analysis_y_axis, y_options[0], *y_options).pack(side="left", padx=5, pady=5)

        ttk.Button(controls_frame, text="Generate Chart", command=self.generate_analysis_chart).pack(side="left", padx=20, pady=5)
        
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.grid(row=1, column=0, sticky="nsew")
        self.chart_canvas = None

    def generate_analysis_chart(self):
        if not MATPLOTLIB_AVAILABLE: return

        model = self.analysis_model.get()
        x_param = self.analysis_x_axis.get()
        y_metric = self.analysis_y_axis.get()
        
        if not model or model == "Select Model":
            messagebox.showerror("Error", "Please select a model to analyze.")
            return

        records = self.db.get_all_benchmarks()
        
        x_data, y_data = [], []
        y_col_map = {"TPS": 5, "TTFT": 4, "Quality Score": 8}
        y_col_idx = y_col_map[y_metric]

        for row in records:
            if row[2] == model and row[y_col_idx] is not None:
                try:
                    params = json.loads(row[3])
                    if x_param in params:
                        x_data.append(params[x_param])
                        y_data.append(row[y_col_idx])
                except (json.JSONDecodeError, KeyError):
                    continue
        
        if not x_data or not y_data:
            messagebox.showinfo("No Data", f"No data found for model '{model}' with parameter '{x_param}' and metric '{y_metric}'.")
            return

        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.scatter(x_data, y_data)
        
        ax.set_title(f"{y_metric} vs. {x_param} for {model}")
        ax.set_xlabel(x_param)
        ax.set_ylabel(y_metric)
        fig.tight_layout()

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.apply_theme() # Re-apply theme to chart elements

    def populate_leaderboard_tab(self):
        main_frame = ttk.Frame(self.leaderboard_tab, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(controls_frame, text="Refresh Leaderboard", command=self.load_leaderboard_data).pack(side="left")

        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("Rank", "Model", "Elo Rating")
        self.leaderboard_tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
        
        for col in cols:
            self.leaderboard_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.leaderboard_tree, c, False))
            self.leaderboard_tree.column(col, width=150, anchor="center")
        
        self.leaderboard_tree.column("Model", anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.leaderboard_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.leaderboard_tree.configure(yscrollcommand=vsb.set)
        self.leaderboard_tree.grid(row=0, column=0, sticky="nsew")

        self.after(200, self.load_leaderboard_data)

    def load_leaderboard_data(self):
        for i in self.leaderboard_tree.get_children():
            self.leaderboard_tree.delete(i)
        
        ratings = self.db.get_all_ratings()
        for i, (model, rating) in enumerate(ratings):
            self.leaderboard_tree.insert("", "end", values=(i + 1, model, rating))

    def sort_treeview(self, tree, col, reverse):
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)

        for index, (val, item) in enumerate(data):
            tree.move(item, '', index)

        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))


    def populate_arena_tab(self):
        main_frame = ttk.Frame(self.arena_tab, padding="10")
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        prompt_frame = ttk.LabelFrame(main_frame, text="Battle Prompt")
        prompt_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        prompt_frame.columnconfigure(0, weight=1)
        self.arena_prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=5)
        self.arena_prompt_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.run_battle_button = ttk.Button(prompt_frame, text="Run Battle", command=self.start_arena_battle)
        self.run_battle_button.grid(row=0, column=1, padx=10)
        arena_panes = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        arena_panes.grid(row=1, column=0, sticky="nsew")
        model_a_frame = self._create_arena_pane(arena_panes, "Model A", self.arena_model_a)
        self.arena_model_a_menu = model_a_frame['menu']
        self.arena_output_a = model_a_frame['text']
        arena_panes.add(model_a_frame['frame'], weight=1)
        model_b_frame = self._create_arena_pane(arena_panes, "Model B", self.arena_model_b)
        self.arena_model_b_menu = model_b_frame['menu']
        self.arena_output_b = model_b_frame['text']
        arena_panes.add(model_b_frame['frame'], weight=1)
        voting_frame = ttk.Frame(main_frame)
        voting_frame.grid(row=2, column=0, pady=10)
        self.vote_button_a = ttk.Button(voting_frame, text="Model A is Better", command=lambda: self.record_vote("A"), state="disabled")
        self.vote_button_a.pack(side="left", padx=5)
        self.vote_button_b = ttk.Button(voting_frame, text="Model B is Better", command=lambda: self.record_vote("B"), state="disabled")
        self.vote_button_b.pack(side="left", padx=5)
        self.vote_button_tie = ttk.Button(voting_frame, text="Both are Good (Tie)", command=lambda: self.record_vote("Tie"), state="disabled")
        self.vote_button_tie.pack(side="left", padx=5)
        self.vote_button_bad = ttk.Button(voting_frame, text="Both are Bad", command=lambda: self.record_vote("Bad"), state="disabled")
        self.vote_button_bad.pack(side="left", padx=5)

    def _create_arena_pane(self, parent, name, model_var):
        frame = ttk.LabelFrame(parent, text=name)
        frame.pack(expand=True, fill="both")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        menu = ttk.OptionMenu(controls, model_var, "Select Model")
        menu.pack(side="left")
        text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state="disabled")
        text_widget.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        return {"frame": frame, "menu": menu, "text": text_widget}


    def populate_prompt_tab(self):
        main_frame = ttk.Frame(self.prompt_tab, padding="10")
        main_frame.pack(expand=True, fill="both")

        # Main layout using PanedWindow
        main_panes = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_panes.pack(expand=True, fill="both")

        # --- Left Pane: Prompt Library ---
        library_frame = ttk.LabelFrame(main_panes, text="Prompt Library")
        library_frame.columnconfigure(0, weight=1)
        library_frame.rowconfigure(1, weight=1)
        main_panes.add(library_frame, weight=1)

        lib_controls = ttk.Frame(library_frame)
        lib_controls.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(lib_controls, text="Load", command=self.load_selected_prompt).pack(side="left", padx=2)
        ttk.Button(lib_controls, text="Delete", command=self.delete_selected_prompt).pack(side="left", padx=2)
        
        cols = ("ID", "Name", "Ver.")
        self.prompt_tree = ttk.Treeview(library_frame, columns=cols, show='headings')
        self.prompt_tree.heading("ID", text="ID")
        self.prompt_tree.column("ID", width=40, anchor="center")
        self.prompt_tree.heading("Name", text="Name")
        self.prompt_tree.column("Name", width=150)
        self.prompt_tree.heading("Ver.", text="Ver.")
        self.prompt_tree.column("Ver.", width=40, anchor="center")
        self.prompt_tree.grid(row=1, column=0, sticky="nsew")
        
        # --- Right Pane: Editor and Output ---
        right_pane = ttk.Frame(main_panes)
        right_pane.columnconfigure(0, weight=1)
        right_pane.rowconfigure(1, weight=1)
        main_panes.add(right_pane, weight=3)

        controls_frame = ttk.Frame(right_pane)
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        prompt_model_label = ttk.Label(controls_frame, text="Model:")
        prompt_model_label.pack(side="left", padx=(0, 5))
        self.prompt_model_menu = ttk.OptionMenu(controls_frame, self.selected_model, "No models found")
        self.prompt_model_menu.pack(side="left", padx=5)
        self.run_prompt_button = ttk.Button(controls_frame, text="Run Prompt", command=self.start_prompt_generation)
        self.run_prompt_button.pack(side="left", padx=20)

        paddock_panes = ttk.PanedWindow(right_pane, orient=tk.VERTICAL)
        paddock_panes.grid(row=1, column=0, sticky="nsew")

        prompt_input_frame = ttk.LabelFrame(paddock_panes, text="Your Prompt")
        prompt_input_frame.columnconfigure(0, weight=1)
        prompt_input_frame.rowconfigure(1, weight=1)
        paddock_panes.add(prompt_input_frame, weight=1)
        
        prompt_btn_frame = ttk.Frame(prompt_input_frame)
        prompt_btn_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(prompt_btn_frame, text="Save/Update", command=self.save_prompt).pack(side="left", padx=2)
        ttk.Button(prompt_btn_frame, text="Save as New Version", command=self.save_prompt_as_new_version).pack(side="left", padx=2)
        ttk.Button(prompt_btn_frame, text="Clear Editor", command=self.clear_prompt_editor).pack(side="left", padx=2)

        self.prompt_input_text = scrolledtext.ScrolledText(prompt_input_frame, wrap=tk.WORD, height=10)
        self.prompt_input_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.current_prompt_id = None # To track which prompt is loaded

        prompt_output_frame = ttk.LabelFrame(paddock_panes, text="Model Response")
        prompt_output_frame.columnconfigure(0, weight=1)
        prompt_output_frame.rowconfigure(0, weight=1)
        self.prompt_output_text = scrolledtext.ScrolledText(prompt_output_frame, wrap=tk.WORD, state="disabled")
        self.prompt_output_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        paddock_panes.add(prompt_output_frame, weight=2)

        self.after(200, self.load_prompt_library)


    def populate_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Server Settings
        server_frame = ttk.LabelFrame(settings_frame, text="Connection")
        server_frame.pack(fill=tk.X, padx=5, pady=5)
        server_label = ttk.Label(server_frame, text="Ollama Server Address:")
        server_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        server_entry = ttk.Entry(server_frame, textvariable=self.ollama_server, width=50)
        server_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        apply_button = ttk.Button(server_frame, text="Apply & Refresh", command=self.update_ollama_client)
        apply_button.grid(row=0, column=2, padx=10, pady=5)

        # Theme Settings
        theme_frame = ttk.LabelFrame(settings_frame, text="Appearance")
        theme_frame.pack(fill=tk.X, padx=5, pady=5)
        theme_label = ttk.Label(theme_frame, text="UI Theme:")
        theme_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.theme_menu = ttk.OptionMenu(theme_frame, self.current_theme, self.current_theme.get(), *THEMES.keys(), command=self.apply_theme)
        self.theme_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Config Management
        config_frame = ttk.LabelFrame(settings_frame, text="Configuration Management")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(config_frame, text="Import Settings", command=self.import_settings).pack(side="left", padx=5, pady=5)
        ttk.Button(config_frame, text="Export Settings", command=self.export_settings).pack(side="left", padx=5, pady=5)

        # Data Management
        data_frame = ttk.LabelFrame(settings_frame, text="Data Management")
        data_frame.pack(fill=tk.X, padx=5, pady=5)
        clear_db_button = ttk.Button(data_frame, text="Clear All Data", command=self.clear_database, style="Danger.TButton")
        clear_db_button.pack(side="left", padx=5, pady=5)
        self.style.configure("Danger.TButton", foreground="red", font=("Helvetica", 10, "bold"))


    def setup_telemetry_display(self):
        self.telemetry_frame = ttk.Frame(self, padding="5")
        self.telemetry_frame.pack(side="bottom", fill="x")
        self.cpu_label = ttk.Label(self.telemetry_frame, text="CPU: -- %")
        self.cpu_label.pack(side="left", padx=10)
        self.ram_label = ttk.Label(self.telemetry_frame, text="RAM: -- / -- GB")
        self.ram_label.pack(side="left", padx=10)
        self.disk_label = ttk.Label(self.telemetry_frame, text="Disk R/W: -- / -- MB/s")
        self.disk_label.pack(side="left", padx=10)
        self.gpu_label = ttk.Label(self.telemetry_frame, text="GPU: N/A")
        self.gpu_label.pack(side="left", padx=10)

    def update_telemetry(self):
        last_disk_io = psutil.disk_io_counters()
        while not self.stop_telemetry_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory()
                current_disk_io = psutil.disk_io_counters()
                read_speed = (current_disk_io.read_bytes - last_disk_io.read_bytes) / (1024**2)
                write_speed = (current_disk_io.write_bytes - last_disk_io.write_bytes) / (1024**2)
                last_disk_io = current_disk_io
                
                self.current_telemetry = {
                    "cpu_usage": f"{cpu_percent:.1f}%",
                    "ram_usage": f"{ram.used / (1024**3):.2f}/{ram.total / (1024**3):.2f} GB",
                    "disk_io": f"{read_speed:.2f}/{write_speed:.2f} MB/s",
                    "gpu_usage": self.get_gpu_info() if PYNML_AVAILABLE else "N/A"
                }
                
                self.cpu_label.config(text=f"CPU: {self.current_telemetry['cpu_usage']}")
                self.ram_label.config(text=f"RAM: {self.current_telemetry['ram_usage']}")
                self.disk_label.config(text=f"Disk R/W: {self.current_telemetry['disk_io']}")
                if PYNML_AVAILABLE: self.gpu_label.config(text=f"GPU: {self.current_telemetry['gpu_usage']}")
                
                time.sleep(1)
            except tk.TclError:
                print("Telemetry thread: TclError, likely due to application closing.")
                break
            except Exception as e:
                print(f"Error in telemetry thread: {e}")


    def get_gpu_info(self):
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            gpu_infos = []
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                gpu_infos.append(f"GPU{i}: {util.gpu}%|Mem:{mem.used/(1024**3):.2f}/{mem.total/(1024**3):.2f}GB|{temp}°C")
            return " | ".join(gpu_infos) if gpu_infos else "No NVIDIA devices found"
        except pynvml.NVMLError as e:
            return f"NVML Error ({e})"

    def refresh_models(self, show_error_popup=False):
        models = self.ollama_client.list_models()
        
        menu_var_map = [
            (self.model_menu, self.selected_model),
            (self.prompt_model_menu, self.selected_model),
            (self.analysis_model_menu, self.analysis_model),
            (self.arena_model_a_menu, self.arena_model_a),
            (self.arena_model_b_menu, self.arena_model_b)
        ]

        for menu, _ in menu_var_map:
            if hasattr(self, menu.winfo_name().replace("!optionmenu", "")):
                menu['menu'].delete(0, 'end')

        if models:
            model_names = [m['name'] for m in models]
            if model_names:
                for menu, var in menu_var_map:
                    for name in model_names:
                        menu['menu'].add_command(label=name, command=lambda v=name, s_var=var: s_var.set(v))
                
                self.selected_model.set(model_names[0])
                self.analysis_model.set(model_names[0])
                self.arena_model_a.set(model_names[0])
                self.arena_model_b.set(model_names[1] if len(model_names) > 1 else model_names[0])
            else:
                for _, var in menu_var_map: var.set("No models found")
        else:
            for _, var in menu_var_map: var.set("Connection failed")
            if show_error_popup:
                messagebox.showerror("Connection Error", f"Could not connect to Ollama server at {self.ollama_server.get()}.")


    def start_benchmark_thread(self):
        if self.is_any_task_running(): return
        if not self.is_model_selected(self.selected_model): return
        
        try:
            param_map = {
                'temperature': (self.param_temperature.get(), float),
                'num_ctx': (self.param_num_ctx.get(), int),
                'top_k': (self.param_top_k.get(), int),
                'top_p': (self.param_top_p.get(), float),
                'num_thread': (self.param_num_thread.get(), int),
                'num_gpu': (self.param_num_gpu.get(), int),
                'num_batch': (self.param_num_batch.get(), int),
                'num_predict': (self.param_num_predict.get(), int)
            }
            job_params = {}
            for name, (val_str, type_converter) in param_map.items():
                if val_str.strip():
                    job_params[name] = [type_converter(v.strip()) for v in val_str.split(',')]
            
            # Handle mmap separately
            mmap_choice = self.param_mmap.get()
            if mmap_choice != "Default":
                job_params['mmap'] = [True] if mmap_choice == "Enabled" else [False]

            param_names = list(job_params.keys())
            param_values = list(job_params.values())
            job_list = [dict(zip(param_names, combo)) for combo in itertools.product(*param_values)]
            
            if not job_list:
                messagebox.showerror("Invalid Parameters", "Please enter at least one value for one parameter.")
                return

        except ValueError as e:
            messagebox.showerror("Invalid Parameter Value", f"Please check your parameter values. They must be comma-separated numbers.\n\nError: {e}")
            return

        self.is_benchmarking = True
        self.run_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.stop_benchmark_event.clear()
        
        test_suite = self.benchmark_suite.get()
        target_func = self.run_benchmark_matrix
        if test_suite == "Reasoning Test":
            target_func = self.run_reasoning_test
        elif test_suite == "Instruction Following":
            target_func = self.run_instruction_following_test

        benchmark_thread = threading.Thread(target=target_func, args=(job_list,), daemon=True)
        benchmark_thread.start()

    def stop_benchmark_thread(self):
        self.stop_benchmark_event.set()
        self.log_to_widget(self.results_text, "\n--- CANCELLING BENCHMARK RUN ---\n")


    def run_benchmark_matrix(self, job_list):
        model = self.selected_model.get()
        prompt = "Describe the theory of relativity in 500 words."
        total_jobs = len(job_list)
        
        self.log_to_widget(self.results_text, f"--- Starting Raw Performance Test for: {model} ---\n")
        self.log_to_widget(self.results_text, f"Found {total_jobs} parameter combinations to test.\n" + "="*40 + "\n")

        for i, params in enumerate(job_list):
            if self.stop_benchmark_event.is_set():
                self.log_to_widget(self.results_text, "Benchmark run cancelled by user.\n")
                break
            
            self.after(0, self.update_progress, i + 1, total_jobs)
            self.log_to_widget(self.results_text, f"Running Test {i+1}/{total_jobs} with parameters: {json.dumps(params)}\n")
            try:
                start_time = time.time()
                first_token_time = None
                token_count = 0
                ttft = -1.0
                for chunk in self.ollama_client.generate(model, prompt, options=params):
                    if self.stop_benchmark_event.is_set(): break
                    if chunk.get("error"):
                        self.log_to_widget(self.results_text, f"ERROR: {chunk['error']}\n"); break
                    if first_token_time is None and "response" in chunk:
                        first_token_time = time.time()
                        ttft = (first_token_time - start_time) * 1000
                        self.log_to_widget(self.results_text, f"  - Time to first token: {ttft:.2f} ms\n")
                    if chunk.get("done"):
                        end_time = time.time()
                        total_duration = end_time - start_time
                        tps = token_count / (end_time - first_token_time) if first_token_time and token_count > 0 else 0
                        log_data = {
                            "timestamp": datetime.now().isoformat(), "model": model,
                            "parameters": json.dumps(params), "ttft_ms": ttft, "tps": tps,
                            "total_tokens": token_count, "total_time_s": total_duration,
                            "telemetry_snapshot": json.dumps(self.current_telemetry)
                        }
                        self.after(0, self.db.add_benchmark_log, log_data)
                        self.log_to_widget(self.results_text, f"  - Tokens per second (TPS): {tps:.2f}\n")
                        self.log_to_widget(self.results_text, f"  - Test complete and logged.\n" + "-"*40 + "\n")
                    else:
                        token_count += 1
            except Exception as e:
                self.log_to_widget(self.results_text, f"\nAn unexpected error occurred: {e}\n" + "-"*40 + "\n")
        
        self.log_to_widget(self.results_text, "--- All Benchmark Tests Complete ---\n\n")
        self.is_benchmarking = False
        self.after(0, self.on_benchmark_complete)

    def run_reasoning_test(self, job_list):
        # This is a small, representative sample of HellaSwag-style questions.
        questions = [
            {
                "context": "A man is putting on his socks. He then puts on his shoes and",
                "endings": ["ties the laces.", "eats a sandwich.", "flies a kite.", "reads a book."],
                "correct": "A"
            },
            {
                "context": "The woman is slicing a tomato for a salad. She carefully cuts it into thin slices and then",
                "endings": ["paints the wall.", "arranges them on the lettuce.", "starts the car.", "sings an opera."],
                "correct": "B"
            },
            {
                "context": "A child is building a tower with wooden blocks. He stacks one block on top of another until the tower is very tall. Suddenly, he",
                "endings": ["bakes a cake.", "writes a letter.", "knocks it over.", "goes for a swim."],
                "correct": "C"
            }
        ]
        model = self.selected_model.get()
        total_jobs = len(job_list)
        
        self.log_to_widget(self.results_text, f"--- Starting Reasoning Test for: {model} ---\n")
        self.log_to_widget(self.results_text, f"Found {total_jobs} parameter combinations to test with {len(questions)} questions each.\n" + "="*40 + "\n")

        for i, params in enumerate(job_list):
            if self.stop_benchmark_event.is_set():
                self.log_to_widget(self.results_text, "Benchmark run cancelled by user.\n")
                break
            
            self.after(0, self.update_progress, i + 1, total_jobs)
            self.log_to_widget(self.results_text, f"Running Test {i+1}/{total_jobs} with parameters: {json.dumps(params)}\n")
            correct_answers = 0
            
            for q_idx, q in enumerate(questions):
                if self.stop_benchmark_event.is_set(): break
                
                prompt = (
                    f"Given the context, which is the most logical ending? Respond with only the letter (A, B, C, or D).\n\n"
                    f"Context: {q['context']}\n\n"
                    f"A) {q['endings'][0]}\n"
                    f"B) {q['endings'][1]}\n"
                    f"C) {q['endings'][2]}\n"
                    f"D) {q['endings'][3]}\n\n"
                    f"Answer:"
                )
                
                full_response = ""
                for chunk in self.ollama_client.generate(model, prompt, options=params):
                    if chunk.get("error"):
                        full_response = "ERROR"
                        break
                    if "response" in chunk:
                        full_response += chunk["response"]
                    if chunk.get("done"):
                        break
                
                answer = full_response.strip().upper()
                if answer.startswith(q["correct"]):
                    correct_answers += 1
                self.log_to_widget(self.results_text, f"  - Q{q_idx+1}: Model answered '{answer}', Correct: '{q['correct']}'\n")

            quality_score = (correct_answers / len(questions)) * 100
            log_data = {
                "timestamp": datetime.now().isoformat(), "model": model,
                "parameters": json.dumps(params), "quality_score": quality_score,
                "telemetry_snapshot": json.dumps(self.current_telemetry)
            }
            self.after(0, self.db.add_benchmark_log, log_data)
            self.log_to_widget(self.results_text, f"  - Quality Score: {quality_score:.2f}%\n" + "-"*40 + "\n")
        
        self.log_to_widget(self.results_text, "--- All Reasoning Tests Complete ---\n\n")
        self.is_benchmarking = False
        self.after(0, self.on_benchmark_complete)

    def run_instruction_following_test(self, job_list):
        # A small, representative sample of instruction-following tasks.
        questions = [
            {
                "prompt": "Provide a response in valid JSON format. The JSON object must contain two keys: 'name' with the value 'John Doe', and 'age' with the value 30.",
                "validator": lambda r: json.loads(r) == {"name": "John Doe", "age": 30},
                "desc": "JSON Formatting"
            },
            {
                "prompt": "Write a sentence that is exactly 10 words long about the planet Mars.",
                "validator": lambda r: abs(len(r.split()) - 10) <= 1, # Allow a small tolerance
                "desc": "Word Count"
            },
            {
                "prompt": "Describe a sunny day at the beach without using the word 'sun'.",
                "validator": lambda r: 'sun' not in r.lower(),
                "desc": "Negative Constraint"
            }
        ]
        model = self.selected_model.get()
        total_jobs = len(job_list)
        
        self.log_to_widget(self.results_text, f"--- Starting Instruction Following Test for: {model} ---\n")
        self.log_to_widget(self.results_text, f"Found {total_jobs} parameter combinations to test with {len(questions)} questions each.\n" + "="*40 + "\n")

        for i, params in enumerate(job_list):
            if self.stop_benchmark_event.is_set():
                self.log_to_widget(self.results_text, "Benchmark run cancelled by user.\n")
                break
            
            self.after(0, self.update_progress, i + 1, total_jobs)
            self.log_to_widget(self.results_text, f"Running Test {i+1}/{total_jobs} with parameters: {json.dumps(params)}\n")
            correct_answers = 0
            
            for q_idx, q in enumerate(questions):
                if self.stop_benchmark_event.is_set(): break
                
                full_response = ""
                for chunk in self.ollama_client.generate(model, q["prompt"], options=params):
                    if chunk.get("error"):
                        full_response = "ERROR"; break
                    if "response" in chunk:
                        full_response += chunk["response"]
                    if chunk.get("done"):
                        break
                
                passed = False
                try:
                    if q["validator"](full_response.strip()):
                        passed = True
                        correct_answers += 1
                except Exception:
                    passed = False
                
                self.log_to_widget(self.results_text, f"  - Task '{q['desc']}': {'PASS' if passed else 'FAIL'}\n")

            quality_score = (correct_answers / len(questions)) * 100
            log_data = {
                "timestamp": datetime.now().isoformat(), "model": model,
                "parameters": json.dumps(params), "quality_score": quality_score,
                "telemetry_snapshot": json.dumps(self.current_telemetry)
            }
            self.after(0, self.db.add_benchmark_log, log_data)
            self.log_to_widget(self.results_text, f"  - Quality Score: {quality_score:.2f}%\n" + "-"*40 + "\n")
        
        self.log_to_widget(self.results_text, "--- All Instruction Following Tests Complete ---\n\n")
        self.is_benchmarking = False
        self.after(0, self.on_benchmark_complete)


    def on_benchmark_complete(self):
        self.run_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.load_history_data() # Refresh history view automatically
        self.update_progress(0, 1) # Reset progress bar
        self.title("Colt's LLama Jockey v1.0 beta - © 2025 Colt McVey") # Reset title

    def update_progress(self, current, total):
        self.progress_bar['value'] = current
        self.progress_bar['maximum'] = total
        if self.is_benchmarking:
            self.title(f"[Testing {current}/{total}] Colt's LLama Jockey v1.0 beta - © 2025 Colt McVey")


    def start_prompt_generation(self):
        if self.is_any_task_running(): return
        if not self.is_model_selected(self.selected_model): return
        prompt = self.prompt_input_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("No Prompt", "Please enter a prompt to run.")
            return
        self.is_generating = True
        self.run_prompt_button.config(state="disabled")
        self.clear_and_enable_widget(self.prompt_output_text)
        generation_thread = threading.Thread(target=self._generate_and_log, args=(self.selected_model.get(), prompt, self.prompt_output_text, "is_generating", self.run_prompt_button), daemon=True)
        generation_thread.start()

    def start_arena_battle(self):
        if self.is_any_task_running(): return
        if not self.is_model_selected(self.arena_model_a, "Model A"): return
        if not self.is_model_selected(self.arena_model_b, "Model B"): return
        prompt = self.arena_prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("No Prompt", "Please enter a battle prompt.")
            return
        self.is_in_arena_battle = True
        self.run_battle_button.config(state="disabled")
        for btn in [self.vote_button_a, self.vote_button_b, self.vote_button_tie, self.vote_button_bad]:
            btn.config(state="disabled")
        self.clear_and_enable_widget(self.arena_output_a)
        self.clear_and_enable_widget(self.arena_output_b)
        thread_a = threading.Thread(target=self._generate_and_log, args=(self.arena_model_a.get(), prompt, self.arena_output_a), daemon=True)
        thread_b = threading.Thread(target=self._generate_and_log, args=(self.arena_model_b.get(), prompt, self.arena_output_b, "is_in_arena_battle", self.run_battle_button), daemon=True)
        thread_a.start()
        thread_b.start()

    def _generate_and_log(self, model, prompt, widget, flag_name=None, button=None):
        try:
            for chunk in self.ollama_client.generate(model, prompt):
                if chunk.get("error"): self.log_to_widget(widget, f"ERROR: {chunk['error']}\n"); break
                if response_part := chunk.get("response"): self.log_to_widget(widget, response_part)
        except Exception as e:
            self.log_to_widget(widget, f"\nAn unexpected error occurred: {e}\n")
        finally:
            if flag_name and button:
                if flag_name == "is_in_arena_battle": self.after(0, self.end_arena_battle)
                else:
                    setattr(self, flag_name, False)
                    self.after(0, lambda: button.config(state="normal"))

    def end_arena_battle(self):
        self.is_in_arena_battle = False
        self.run_battle_button.config(state="normal")
        for btn in [self.vote_button_a, self.vote_button_b, self.vote_button_tie, self.vote_button_bad]:
            btn.config(state="normal")
        self.load_leaderboard_data()

    def log_to_widget(self, widget, message):
        def _update():
            widget.config(state="normal")
            widget.insert(tk.END, message)
            widget.see(tk.END)
            widget.config(state="disabled")
        self.after(0, _update)

    def clear_and_enable_widget(self, widget):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.config(state="disabled")

    def update_ollama_client(self, *args):
        self.ollama_client = OllamaClient(self.ollama_server.get())
        self.refresh_models(show_error_popup=True)

    def is_any_task_running(self):
        if self.is_benchmarking or self.is_generating or self.is_in_arena_battle:
            messagebox.showwarning("In Progress", "Another task is already running.")
            return True
        return False

    def is_model_selected(self, model_var, model_name=""):
        model = model_var.get()
        if not model or "failed" in model or "found" in model:
            messagebox.showerror("No Model Selected", f"Please select a valid model for {model_name}." if model_name else "Please select a valid model.")
            return False
        return True
    
    def _calculate_elo(self, r_a, r_b, outcome):
        K = 32
        e_a = 1 / (1 + 10**((r_b - r_a) / 400))
        e_b = 1 / (1 + 10**((r_a - r_b) / 400))
        
        if outcome == "A":
            s_a, s_b = 1.0, 0.0
        elif outcome == "B":
            s_a, s_b = 0.0, 1.0
        else: # Tie
            s_a, s_b = 0.5, 0.5
            
        new_r_a = r_a + K * (s_a - e_a)
        new_r_b = r_b + K * (s_b - e_b)
        
        return round(new_r_a), round(new_r_b)

    def record_vote(self, winner):
        model_a_name = self.arena_model_a.get()
        model_b_name = self.arena_model_b.get()
        prompt = self.arena_prompt_text.get("1.0", tk.END).strip()
        
        # Log the battle first
        self.db.add_arena_log(model_a_name, model_b_name, prompt, winner)
        
        # Update Elo ratings
        rating_a = self.db.get_rating(model_a_name)
        rating_b = self.db.get_rating(model_b_name)
        
        new_rating_a, new_rating_b = self._calculate_elo(rating_a, rating_b, winner)
        
        self.db.update_ratings(model_a_name, new_rating_a, model_b_name, new_rating_b)
        
        messagebox.showinfo("Vote Recorded", f"Your vote for '{winner}' has been logged and ratings have been updated.")
        for btn in [self.vote_button_a, self.vote_button_b, self.vote_button_tie, self.vote_button_bad]:
            btn.config(state="disabled")
        
        self.load_leaderboard_data() # Refresh leaderboard view
    
    def run_jockeys_edge_analysis(self):
        objective = self.jockeys_edge_objective.get()
        result = self.db.get_optimal_setting(objective)
        
        self.clear_and_enable_widget(self.jockeys_edge_result)

        if result:
            recommendation = (
                f"Optimal setting for '{objective}':\n"
                f"  - Model: {result[2]}\n"
                f"  - Parameters: {result[3]}\n"
                f"  - Achieved TPS: {result[5]:.2f}\n"
                f"  - Achieved TTFT: {result[4]:.2f} ms\n"
                f"  - Test run on: {result[1]}"
            )
            self.log_to_widget(self.jockeys_edge_result, recommendation)
        else:
            self.log_to_widget(self.jockeys_edge_result, "No benchmark data found for this objective. Please run some tests first.")


    def export_benchmarks(self, format_type):
        benchmarks = self.db.get_all_benchmarks()
        if not benchmarks:
            messagebox.showinfo("No Data", "There are no benchmark results to export.")
            return
        if format_type == 'md':
            file_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")])
            if not file_path: return
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Colt's LLama Jockey - Benchmark Report\n\n")
                    f.write(f"Report generated on: {datetime.now().isoformat()}\n\n")
                    f.write("| ID | Timestamp | Model | Parameters | TTFT (ms) | TPS | Tokens | Total Time (s) | Quality (%) |\n")
                    f.write("|---|---|---|---|---|---|---|---|---|\n")
                    for row in benchmarks:
                        f.write(f"| {row[0]} | {row[1]} | {row[2]} | `{row[3]}` | {row[4]:.2f} | {row[5]:.2f} | {row[6]} | {row[7]:.2f} | {row[8]:.2f} |\n")
                messagebox.showinfo("Export Successful", f"Report saved to {file_path}")
            except Exception as e: messagebox.showerror("Export Error", f"Failed to write Markdown file: {e}")
        elif format_type == 'xlsx':
            if not XLSXWRITER_AVAILABLE:
                messagebox.showerror("Missing Library", "Install 'xlsxwriter' for Excel export: pip install xlsxwriter")
                return
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Workbook", "*.xlsx")])
            if not file_path: return
            try:
                workbook = xlsxwriter.Workbook(file_path)
                worksheet = workbook.add_worksheet("Benchmark Results")
                headers = ["ID", "Timestamp", "Model", "Parameters", "TTFT (ms)", "TPS", "Total Tokens", "Total Time (s)", "Quality Score (%)"]
                worksheet.write_row('A1', headers)
                for row_num, row_data in enumerate(benchmarks):
                    worksheet.write_row(row_num + 1, 0, row_data)
                workbook.close()
                messagebox.showinfo("Export Successful", f"Report saved to {file_path}")
            except Exception as e: messagebox.showerror("Export Error", f"Failed to write Excel file: {e}")

    def export_settings(self):
        settings = {
            "ollama_server": self.ollama_server.get(),
            "current_theme": self.current_theme.get(),
            "param_temperature": self.param_temperature.get(),
            "param_num_ctx": self.param_num_ctx.get(),
            "param_top_k": self.param_top_k.get(),
            "param_top_p": self.param_top_p.get(),
            "param_num_thread": self.param_num_thread.get(),
            "param_num_gpu": self.param_num_gpu.get(),
            "param_num_batch": self.param_num_batch.get(),
            "param_num_predict": self.param_num_predict.get()
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file_path: return
        try:
            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=4)
            messagebox.showinfo("Export Successful", "Settings exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export settings: {e}")

    def import_settings(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file_path: return
        try:
            with open(file_path, 'r') as f:
                settings = json.load(f)
            
            # Update all StringVars from the loaded settings
            for key, value in settings.items():
                if hasattr(self, key):
                    getattr(self, key).set(value)
            
            self.apply_theme()
            self.update_ollama_client()
            messagebox.showinfo("Import Successful", "Settings imported successfully. Ollama client updated.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import settings: {e}")

    def clear_database(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to permanently delete all benchmark history and model ratings? This action cannot be undone."):
            try:
                self.db.clear_all_data()
                self.load_history_data()
                self.load_leaderboard_data()
                self.load_prompt_library()
                messagebox.showinfo("Success", "All data has been cleared.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear database: {e}")


    def apply_theme(self, *args):
        theme_name = self.current_theme.get()
        theme = THEMES.get(theme_name, THEMES["Dark"])
        
        # Define fonts
        font_family = "Segoe UI" if os.name == 'nt' else "Helvetica"
        ui_font = (font_family, 10)
        bold_font = (font_family, 10, "bold")
        text_font = ("Courier New", 10) if theme_name == "Vintage Terminal" else ("Consolas", 10)

        self.configure(bg=theme["bg"])
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"], font=ui_font)
        self.style.configure("TButton", font=bold_font, padding=5)
        self.style.map("TButton",
            background=[('active', theme["accent"]), ('!disabled', theme["button_bg"])],
            foreground=[('!disabled', theme["button_fg"])]
        )
        self.style.configure("TNotebook", background=theme["notebook_bg"])
        self.style.configure("TNotebook.Tab", font=ui_font, padding=[10, 5], borderwidth=1)
        self.style.map("TNotebook.Tab", 
                       background=[("selected", theme["accent"])], 
                       foreground=[("selected", theme["selected_fg"])],
                       font=[("selected", bold_font)])
        self.style.configure("TLabelframe", background=theme["bg"], foreground=theme["fg"], borderwidth=1, relief="solid")
        self.style.configure("TLabelframe.Label", background=theme["bg"], foreground=theme["fg"], font=bold_font)
        
        # Style Treeview
        self.style.configure("Treeview", background=theme["text_bg"], foreground=theme["text_fg"], fieldbackground=theme["text_bg"], font=ui_font, rowheight=25)
        self.style.configure("Treeview.Heading", font=bold_font, background=theme["button_bg"], foreground=theme["button_fg"], padding=5)
        self.style.map("Treeview.Heading", background=[('active', theme["accent"])])

        widget_names = ["results_text", "prompt_input_text", "prompt_output_text", "arena_prompt_text", "arena_output_a", "arena_output_b", "jockeys_edge_result"]
        for name in widget_names:
            if hasattr(self, name):
                getattr(self, name).config(background=theme["text_bg"], foreground=theme["text_fg"], font=text_font, insertbackground=theme["fg"], relief="solid", bd=1)

        # Theme matplotlib chart
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'chart_canvas') and self.chart_canvas:
            fig = self.chart_canvas.figure
            fig.patch.set_facecolor(theme["bg"])
            ax = fig.axes[0]
            ax.set_facecolor(theme["text_bg"])
            ax.tick_params(axis='x', colors=theme["fg"])
            ax.tick_params(axis='y', colors=theme["fg"])
            ax.spines['bottom'].set_color(theme["fg"])
            ax.spines['top'].set_color(theme["fg"]) 
            ax.spines['right'].set_color(theme["fg"])
            ax.spines['left'].set_color(theme["fg"])
            ax.title.set_color(theme["fg"])
            ax.xaxis.label.set_color(theme["fg"])
            ax.yaxis.label.set_color(theme["fg"])
            self.chart_canvas.draw()


    def on_closing(self):
        self.stop_telemetry_event.set()
        
        # Save window geometry
        with open(self.config_file, 'w') as f:
            json.dump({"geometry": self.geometry()}, f)

        self.db.close()
        if PYNML_AVAILABLE: pynvml.nvmlShutdown()
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            
    # --- Prompt Paddock Methods ---
    def load_prompt_library(self):
        for i in self.prompt_tree.get_children():
            self.prompt_tree.delete(i)
        prompts = self.db.get_all_prompts()
        for p in prompts:
            self.prompt_tree.insert("", "end", values=p)

    def load_selected_prompt(self):
        selected_item = self.prompt_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a prompt from the library to load.")
            return
        
        item_values = self.prompt_tree.item(selected_item)['values']
        prompt_id = item_values[0]
        content = self.db.get_prompt_content(prompt_id)
        
        self.prompt_input_text.delete("1.0", tk.END)
        self.prompt_input_text.insert("1.0", content)
        self.current_prompt_id = prompt_id

    def save_prompt(self):
        content = self.prompt_input_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showerror("Error", "Prompt editor is empty.")
            return

        if self.current_prompt_id:
            # Update existing prompt
            selected_item = self.prompt_tree.focus()
            item_values = self.prompt_tree.item(selected_item)['values']
            name = item_values[1]
            self.db.save_prompt(name, None, content, self.current_prompt_id)
            messagebox.showinfo("Success", f"Prompt '{name}' updated successfully.")
        else:
            # Save new prompt
            name = askstring("Prompt Name", "Enter a name for this new prompt:")
            if name:
                self.db.save_prompt(name, 1, content)
                self.load_prompt_library()
                messagebox.showinfo("Success", f"Prompt '{name}' saved.")

    def save_prompt_as_new_version(self):
        content = self.prompt_input_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showerror("Error", "Prompt editor is empty.")
            return

        selected_item = self.prompt_tree.focus()
        if not selected_item:
            name = askstring("Prompt Name", "No prompt is loaded. Enter a name for this new prompt:")
            if not name: return
            version = 1
        else:
            item_values = self.prompt_tree.item(selected_item)['values']
            name = item_values[1]
            latest_version = self.db.get_latest_prompt_version(name)
            version = latest_version + 1
        
        self.db.save_prompt(name, version, content)
        self.load_prompt_library()
        messagebox.showinfo("Success", f"Prompt '{name}' saved as new version (v{version}).")


    def delete_selected_prompt(self):
        selected_item = self.prompt_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a prompt to delete.")
            return
        
        item_values = self.prompt_tree.item(selected_item)['values']
        prompt_id = item_values[0]
        name = item_values[1]
        version = item_values[2]

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name} v{version}'?"):
            self.db.delete_prompt(prompt_id)
            self.load_prompt_library()
            messagebox.showinfo("Success", "Prompt deleted.")

    def clear_prompt_editor(self):
        self.prompt_input_text.delete("1.0", tk.END)
        self.current_prompt_id = None

    def show_help_window(self):
        help_win = tk.Toplevel(self)
        help_win.title("Parameter Help")
        help_win.geometry("800x600")
        
        # Apply theme to the new window
        theme_name = self.current_theme.get()
        theme = THEMES.get(theme_name, THEMES["Dark"])
        help_win.configure(bg=theme["bg"])

        text_widget = scrolledtext.ScrolledText(help_win, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(expand=True, fill="both")
        text_widget.config(background=theme["text_bg"], foreground=theme["text_fg"], font=("Segoe UI", 10), relief="flat")

        help_text = """
Parameter Explanations & Guidance
=================================

This guide explains the key Ollama parameters you can tune in Colt's LLama Jockey and their impact on performance and system resources.

---

### Temperature
- **What it is:** Controls the randomness of the model's output.
- **Values:** A float, typically between 0.0 and 2.0.
- **High Temperature (e.g., 1.2):** More random, creative, and sometimes nonsensical outputs. Good for brainstorming or creative writing.
- **Low Temperature (e.g., 0.2):** More deterministic and focused outputs. Good for factual recall, summarization, or coding.
- **Resource Impact:** Negligible. This is a mathematical adjustment to the final probability distribution and does not significantly affect VRAM, CPU, or TPS.

---

### Context Window (num_ctx)
- **What it is:** The number of tokens the model considers when generating the next token. This defines the model's "short-term memory."
- **Values:** An integer (e.g., 2048, 4096, 8192).
- **Impact:** A larger context window allows the model to understand and remember more of the preceding conversation or document, leading to more coherent long-form text. However, it comes at a significant performance cost.
- **Resource Impact:**
    - **VRAM/RAM:** This is the BIGGEST consumer of memory. The memory required scales linearly with the context window size. `VRAM Usage ≈ (Model Size) + (num_ctx * Per-Token-Memory)`. Doubling `num_ctx` can dramatically increase VRAM usage. If VRAM is exceeded, layers are offloaded to system RAM, drastically slowing down inference.
    - **TPS:** As `num_ctx` increases, the time to process the initial prompt (prefill stage) also increases, which can lower the overall effective TPS for short generations.

---

### Top K
- **What it is:** Narrows the model's choices to the `K` most likely next tokens.
- **Values:** An integer (e.g., 40, 50). A value of 0 disables it.
- **Impact:** Prevents the model from picking highly improbable words, which can reduce gibberish. A lower `K` makes the output more predictable and less diverse.
- **Resource Impact:** Negligible.

---

### Top P (Nucleus Sampling)
- **What it is:** Narrows the model's choices to a cumulative probability mass. It selects the smallest set of tokens whose cumulative probability is greater than `P`.
- **Values:** A float between 0.0 and 1.0 (e.g., 0.9).
- **Impact:** More dynamic than Top K. For a given `P`, it might select many tokens in high-certainty situations and few tokens in low-certainty situations. Often preferred over Top K for balancing creativity and coherence.
- **Resource Impact:** Negligible.

---

### Threads (num_thread)
- **What it is:** The number of CPU threads to use for prompt processing.
- **Values:** An integer. Leave blank to let Ollama decide (often optimal).
- **Impact:** Can speed up the initial prompt processing phase (prefill). The ideal number often corresponds to the number of physical (not logical) CPU cores.
- **Resource Impact:**
    - **CPU:** Directly controls CPU usage during prompt processing. Setting it too high on a CPU with few cores can cause contention and slow things down.
    - **Performance:** Finding the sweet spot can improve TTFT, especially for large prompts. It has less effect on TPS after the prompt is processed.

---

### GPU Layers (num_gpu)
- **What it is:** The number of model layers to offload to the GPU's VRAM.
- **Values:** An integer.
- **Impact:** This is the most critical performance parameter. The more layers you can fit on the GPU, the faster the model will run.
- **Resource Impact:**
    - **VRAM:** Directly proportional. Each layer consumes a chunk of VRAM. You should aim to offload as many layers as possible without exceeding your GPU's VRAM capacity. If you exceed it, the model will fail to load.
    - **TPS:** Performance scales directly with the number of layers on the GPU. Even one layer on the GPU is much faster than zero. The goal is to maximize this value.

---

### Batch Size (num_batch)
- **What it is:** The number of tokens to process in parallel during the initial prompt evaluation.
- **Values:** An integer, often a power of 2 (e.g., 512, 1024).
- **Impact:** A larger batch size can speed up the processing of very long prompts by utilizing the GPU more efficiently.
- **Resource Impact:**
    - **VRAM:** Increasing `num_batch` significantly increases the VRAM required during prompt processing. It must be small enough for the model and context to fit in memory.

---

### Max Tokens (num_predict)
- **What it is:** The maximum number of tokens to generate in the response.
- **Values:** An integer (e.g., 512, 1024). -1 means infinite.
- **Impact:** Limits the length of the output.
- **Resource Impact:** Negligible on its own, but a higher limit allows for longer generations, which naturally take more time.

---

### Memory Map (mmap)
- **What it is:** Controls whether the model's weights are memory-mapped from the file on disk.
- **Values:** Enabled, Disabled, Default.
- **Impact:**
    - **Enabled:** Can lead to faster model load times, especially on subsequent loads, as the OS can page in the model from disk as needed. It may also allow you to load models that are larger than your available RAM.
    - **Disabled:** The entire model is loaded into RAM upfront. This can have a slower initial load time but may lead to more consistent performance afterward, as there's no risk of waiting for the OS to page in parts of the model from a slow disk.
- **Resource Impact:** Primarily affects RAM usage patterns and model load times. Test both to see which is faster for your specific hardware (SSD vs. HDD) and RAM configuration.
"""
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")


if __name__ == "__main__":
    app = LlamaJockeyApp()
    app.mainloop()
