#!/usr/bin/env python3
"""
SSH Tunnel Manager

A comprehensive cross-platform GUI tool for creating and managing SSH tunnels including:

- Create SSH tunnels through bastion hosts
- Manage multiple tunnels simultaneously
- Save and load tunnel configurations
- Automatic configuration loading on startup
- Real-time tunnel status monitoring
- Cross-platform support (Windows, Linux, macOS)
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import json
import time
from pathlib import Path


class TunnelManager:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH Tunnel Manager")
        self.root.geometry("800x700")
        
        self.tunnels = []  # Store active tunnel processes
        self.setup_ui()
        
    def setup_ui(self):
        # Configure root window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Create main tab for tunnel configuration
        main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab, text="Tunnel Configuration")
        
        # Create instructions tab
        instructions_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(instructions_tab, text="Instructions")
        
        # Create author information tab
        author_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(author_tab, text="Author Information")
        
        # Setup main tab
        self.setup_main_tab(main_tab)
        
        # Setup instructions tab
        self.setup_instructions_tab(instructions_tab)
        
        # Setup author information tab
        self.setup_author_tab(author_tab)
        
        # Auto-load latest configuration after UI is ready
        self.root.after(100, self.auto_load_latest_config)
    
    def setup_main_tab(self, main_frame):
        """Setup the main tunnel configuration tab"""
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="SSH Tunnel Configuration", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Bastion Host Configuration
        bastion_frame = ttk.LabelFrame(main_frame, text="Bastion Host Configuration", padding="10")
        bastion_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        bastion_frame.columnconfigure(1, weight=1)
        
        # Bastion Host
        ttk.Label(bastion_frame, text="Bastion Host:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bastion_host = tk.StringVar(value="")
        ttk.Entry(bastion_frame, textvariable=self.bastion_host, width=40).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Key File
        ttk.Label(bastion_frame, text="Private Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        key_frame = ttk.Frame(bastion_frame)
        key_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        key_frame.columnconfigure(0, weight=1)
        
        # No default key file - user must select
        self.key_file = tk.StringVar(value="")
        ttk.Entry(key_frame, textvariable=self.key_file, width=35).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(key_frame, text="Browse...", command=self.browse_key_file).grid(
            row=0, column=1)
        
        # Tunnel Configuration
        tunnel_frame = ttk.LabelFrame(main_frame, text="Tunnel Configuration", padding="10")
        tunnel_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        tunnel_frame.columnconfigure(1, weight=1)
        tunnel_frame.columnconfigure(3, weight=1)
        
        # Local Port
        ttk.Label(tunnel_frame, text="Local Port:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.local_port = tk.StringVar(value="")
        ttk.Entry(tunnel_frame, textvariable=self.local_port, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Remote IP
        ttk.Label(tunnel_frame, text="Remote IP:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=5)
        self.remote_ip = tk.StringVar(value="")
        ttk.Entry(tunnel_frame, textvariable=self.remote_ip, width=15).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Remote Port
        ttk.Label(tunnel_frame, text="Remote Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.remote_port = tk.StringVar(value="")
        ttk.Entry(tunnel_frame, textvariable=self.remote_port, width=15).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Buttons - Row 1
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.create_btn = ttk.Button(button_frame, text="Create Tunnel", 
                                     command=self.create_tunnel, width=18)
        self.create_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_tunnel_btn = ttk.Button(button_frame, text="Stop Tunnel", 
                                           command=self.stop_selected_tunnel, width=18)
        self.stop_tunnel_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_all_btn = ttk.Button(button_frame, text="Stop All Tunnels", 
                                       command=self.stop_all_tunnels, width=18)
        self.stop_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_log_btn = ttk.Button(button_frame, text="Clear Log", 
                                        command=self.clear_log, width=18)
        self.clear_log_btn.pack(side=tk.LEFT, padx=5)
        
        # Config buttons - Row 2
        config_btn_frame = ttk.Frame(main_frame)
        config_btn_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.save_config_btn = ttk.Button(config_btn_frame, text="Save Configuration", 
                                          command=self.save_configuration, width=18)
        self.save_config_btn.pack(side=tk.LEFT, padx=5)
        
        self.load_config_btn = ttk.Button(config_btn_frame, text="Load Configuration", 
                                          command=self.load_configuration, width=18)
        self.load_config_btn.pack(side=tk.LEFT, padx=5)
        
        # Active Tunnels List
        tunnels_list_frame = ttk.LabelFrame(main_frame, text="Active Tunnels", padding="10")
        tunnels_list_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        tunnels_list_frame.columnconfigure(0, weight=1)
        tunnels_list_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Treeview for tunnels
        columns = ("Local Port", "Remote", "Status", "PID")
        self.tunnels_tree = ttk.Treeview(tunnels_list_frame, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.tunnels_tree.heading(col, text=col)
            self.tunnels_tree.column(col, width=150)
        
        scrollbar_tunnels = ttk.Scrollbar(tunnels_list_frame, orient=tk.VERTICAL, 
                                         command=self.tunnels_tree.yview)
        self.tunnels_tree.configure(yscrollcommand=scrollbar_tunnels.set)
        
        self.tunnels_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_tunnels.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Context menu for tunnels
        self.tunnel_menu = tk.Menu(self.root, tearoff=0)
        self.tunnel_menu.add_command(label="Stop Tunnel", command=self.stop_selected_tunnel)
        # Right-click: Button-3 on Windows/Linux, Button-2 on macOS
        if sys.platform == "darwin":
            self.tunnels_tree.bind("<Button-2>", self.show_tunnel_menu)
            self.tunnels_tree.bind("<Control-Button-1>", self.show_tunnel_menu)  # Also support Ctrl+Click
        else:
            self.tunnels_tree.bind("<Button-3>", self.show_tunnel_menu)
        
        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def setup_instructions_tab(self, instructions_frame):
        """Setup the instructions tab"""
        instructions_frame.columnconfigure(0, weight=1)
        
        # Overview Section
        overview_frame = ttk.LabelFrame(instructions_frame, text="Overview", padding="15")
        overview_frame.pack(fill='x', pady=(0, 15))
        
        overview_text = """This application helps you create and manage SSH tunnels to connect to remote servers 
through a bastion host. SSH tunnels forward local ports to remote servers, allowing 
you to access services as if they were running locally."""
        
        overview_label = ttk.Label(overview_frame, text=overview_text, justify='left', wraplength=700)
        overview_label.pack(anchor='w')
        
        # Getting Started Section
        getting_started_frame = ttk.LabelFrame(instructions_frame, text="Getting Started", padding="15")
        getting_started_frame.pack(fill='x', pady=(0, 15))
        
        getting_started_text = """1. CONFIGURE BASTION HOST
   - Enter your bastion host in the format: username@hostname
   - Example: ec2-user@YOUR_BASTION_IP
   - The bastion host is the jump server that will forward your connections

2. SELECT PRIVATE KEY
   - Click "Browse..." to select your SSH private key file (.pem)
   - This key must have access to the bastion host
   - Make sure the key file has correct permissions (on Linux/macOS: chmod 600)

3. CONFIGURE TUNNEL
   - Local Port: The port on your local machine (e.g., 3391)
   - Remote IP: The IP address of the target server (e.g., 10.0.1.158)
   - Remote Port: The port on the target server (e.g., 3389 for RDP)

4. CREATE TUNNEL
   - Click "Create Tunnel" to establish the connection
   - The tunnel will appear in the "Active Tunnels" list
   - Check the log output for status messages"""
        
        getting_started_label = ttk.Label(getting_started_frame, text=getting_started_text, justify='left')
        getting_started_label.pack(anchor='w')
        
        # Using Tunnels Section
        using_tunnels_frame = ttk.LabelFrame(instructions_frame, text="Using Tunnels", padding="15")
        using_tunnels_frame.pack(fill='x', pady=(0, 15))
        
        using_tunnels_text = """After creating a tunnel, you can connect to the remote service using:
  localhost:<local_port>

For example, if you created a tunnel with:
  - Local Port: 3391
  - Remote IP: 10.0.1.158
  - Remote Port: 3389

You can connect via RDP to: localhost:3391"""
        
        using_tunnels_label = ttk.Label(using_tunnels_frame, text=using_tunnels_text, justify='left')
        using_tunnels_label.pack(anchor='w')
        
        # Managing Tunnels Section
        managing_frame = ttk.LabelFrame(instructions_frame, text="Managing Tunnels", padding="15")
        managing_frame.pack(fill='x', pady=(0, 15))
        
        managing_text = """STOP TUNNEL
- Select a tunnel from the "Active Tunnels" list
- Click "Stop Tunnel" to close that specific tunnel
- Or right-click on a tunnel and select "Stop Tunnel"

STOP ALL TUNNELS
- Click "Stop All Tunnels" to close all active tunnels at once
- Useful when you're done with all connections

ACTIVE TUNNELS LIST
- Shows all currently running tunnels
- Displays: Local Port, Remote IP:Port, Status, and Process ID
- Right-click on any tunnel for quick actions"""
        
        managing_label = ttk.Label(managing_frame, text=managing_text, justify='left')
        managing_label.pack(anchor='w')
        
        # Saving and Loading Section
        config_frame = ttk.LabelFrame(instructions_frame, text="Saving and Loading Configurations", padding="15")
        config_frame.pack(fill='x', pady=(0, 15))
        
        config_text = """SAVE CONFIGURATION
- Click "Save Configuration" to save all active tunnels to a JSON file
- The saved file includes:
  * Bastion host
  * Key file path
  * All tunnel configurations (ports and IPs)
- Useful for saving your tunnel setup for later use

LOAD CONFIGURATION
- Click "Load Configuration" to load a previously saved configuration
- Select a JSON configuration file
- The application will:
  * Update bastion host and key file fields
  * Ask if you want to create all tunnels from the config
  * If you choose "No", it will load the first tunnel into the form fields

AUTO-LOAD ON STARTUP
- The application automatically loads the latest saved configuration on startup
- Searches for configuration files in common locations
- Automatically creates all tunnels from the loaded configuration
- Check the log output to see what was loaded"""
        
        config_label = ttk.Label(config_frame, text=config_text, justify='left')
        config_label.pack(anchor='w')
        
        # Example Workflow Section
        workflow_frame = ttk.LabelFrame(instructions_frame, text="Example Workflow", padding="15")
        workflow_frame.pack(fill='x', pady=(0, 15))
        
        workflow_text = """1. First Time Setup:
   - Enter bastion host: ec2-user@YOUR_BASTION_IP
   - Browse and select your private key file
   - Configure tunnel: Local Port 3391, Remote IP 10.0.1.158, Remote Port 3389
   - Click "Create Tunnel"
   - Connect to localhost:3391 via RDP

2. Creating Multiple Tunnels:
   - After creating first tunnel, change the Local Port and Remote IP
   - Click "Create Tunnel" again for each additional tunnel
   - All tunnels will appear in the Active Tunnels list

3. Saving Your Setup:
   - After creating all tunnels, click "Save Configuration"
   - Save the file (e.g., my_tunnels.json)
   - Next time you start the application, tunnels will be loaded automatically"""
        
        workflow_label = ttk.Label(workflow_frame, text=workflow_text, justify='left')
        workflow_label.pack(anchor='w')
        
        # Tips and Troubleshooting Section
        tips_frame = ttk.LabelFrame(instructions_frame, text="Tips and Troubleshooting", padding="15")
        tips_frame.pack(fill='x', pady=(0, 15))
        
        tips_text = """PORT CONFLICTS
- Each tunnel must use a unique local port
- If a port is already in use, you'll get an error
- Check the Active Tunnels list to see which ports are in use

KEY FILE PERMISSIONS
- On Linux/macOS, ensure your key file has correct permissions:
  chmod 600 /path/to/your/key.pem
- On Windows, this is usually not an issue

SSH CONNECTION ISSUES
- Verify your bastion host is accessible
- Check that your private key is correct
- Ensure your network allows SSH connections
- Check the log output for detailed error messages

TUNNEL NOT WORKING
- Verify the tunnel appears in Active Tunnels with "Active" status
- Check that the remote IP and port are correct
- Ensure the remote service is running on the target server
- Try connecting to localhost:<local_port> to test

CLOSING THE APPLICATION
- If you have active tunnels, you'll be prompted to stop them before closing
- Always stop tunnels properly to avoid leaving connections open"""
        
        tips_label = ttk.Label(tips_frame, text=tips_text, justify='left')
        tips_label.pack(anchor='w')
        
        # Keyboard Shortcuts Section
        shortcuts_frame = ttk.LabelFrame(instructions_frame, text="Keyboard Shortcuts", padding="15")
        shortcuts_frame.pack(fill='x', pady=(0, 15))
        
        shortcuts_text = """- Right-click (Windows/Linux) or Control+Click (macOS) on tunnels for context menu
- Use the log output to monitor tunnel operations"""
        
        shortcuts_label = ttk.Label(shortcuts_frame, text=shortcuts_text, justify='left')
        shortcuts_label.pack(anchor='w')
        
        # Support Section
        support_frame = ttk.LabelFrame(instructions_frame, text="Support", padding="15")
        support_frame.pack(fill='x')
        
        support_text = """For issues or questions:
- Check the log output for error messages
- Verify all configuration fields are filled correctly
- Ensure SSH client is installed and accessible in your PATH"""
        
        support_label = ttk.Label(support_frame, text=support_text, justify='left')
        support_label.pack(anchor='w')
    
    def setup_author_tab(self, author_frame):
        """Setup the author information tab"""
        author_frame.columnconfigure(0, weight=1)
        
        # Author Information
        author_info_frame = ttk.LabelFrame(author_frame, text="Author Information", padding="15")
        author_info_frame.pack(fill='x', pady=(0, 15))
        
        author_text = """👤 Created by: Oleh Sharudin
📅 Date: December 10, 2025
💼 Role: DevOps Engineer
🔗 GitHub: YOUR_GITHUB_URL"""
        
        author_label = ttk.Label(author_info_frame, text=author_text, justify='left')
        author_label.pack(anchor='w')
        
    def browse_key_file(self):
        # Get initial directory from key file path or use home directory
        initial_dir = "."
        if self.key_file.get():
            key_path = Path(self.key_file.get())
            if key_path.exists():
                initial_dir = str(key_path.parent)
            elif key_path.parent.exists():
                initial_dir = str(key_path.parent)
            else:
                initial_dir = str(Path.home())
        
        filename = filedialog.askopenfilename(
            title="Select Private Key File",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if filename:
            self.key_file.set(filename)
            self.log(f"Selected key file: {filename}")
    
    def log(self, message):
        """Add message to log output"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log output"""
        self.log_text.delete(1.0, tk.END)
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.bastion_host.get().strip():
            messagebox.showerror("Error", "Please enter bastion host")
            return False
        
        if not self.key_file.get().strip():
            messagebox.showerror("Error", "Please select a private key file")
            return False
        
        if not os.path.exists(self.key_file.get()):
            messagebox.showerror("Error", f"Key file not found: {self.key_file.get()}")
            return False
        
        try:
            local_port = int(self.local_port.get())
            if local_port < 1 or local_port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            messagebox.showerror("Error", "Local port must be a number between 1 and 65535")
            return False
        
        if not self.remote_ip.get().strip():
            messagebox.showerror("Error", "Please enter remote IP address")
            return False
        
        try:
            remote_port = int(self.remote_port.get())
            if remote_port < 1 or remote_port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            messagebox.showerror("Error", "Remote port must be a number between 1 and 65535")
            return False
        
        # Check if local port is already in use
        local_port = int(self.local_port.get())
        for tunnel in self.tunnels:
            if tunnel['local_port'] == local_port:
                messagebox.showerror("Error", f"Port {local_port} is already in use by another tunnel")
                return False
        
        return True
    
    def create_tunnel(self):
        """Create SSH tunnel in background thread"""
        if not self.validate_inputs():
            return
        
        # Disable button during creation
        self.create_btn.config(state=tk.DISABLED)
        self.status_var.set("Creating tunnel...")
        
        def tunnel_thread():
            try:
                local_port = int(self.local_port.get())
                remote_ip = self.remote_ip.get().strip()
                remote_port = int(self.remote_port.get())
                key_path = self.key_file.get()
                bastion = self.bastion_host.get().strip()
                
                # Build SSH command
                ssh_cmd = [
                    "ssh",
                    "-i", key_path,
                    "-o", "StrictHostKeyChecking=accept-new",
                    "-L", f"{local_port}:{remote_ip}:{remote_port}",
                    "-N",  # No remote command
                    "-f",  # Background
                    bastion
                ]
                
                self.log(f"Creating tunnel: localhost:{local_port} -> {remote_ip}:{remote_port}")
                self.log(f"Command: {' '.join(ssh_cmd)}")
                
                # Start SSH process with platform-specific flags
                popen_kwargs = {
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.PIPE,
                }
                
                # Windows: hide console window
                if sys.platform == "win32":
                    # CREATE_NO_WINDOW constant (0x08000000) - prevents console window
                    try:
                        popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                    except AttributeError:
                        # For Python < 3.7, use the constant value directly
                        popen_kwargs['creationflags'] = 0x08000000
                # Unix/Linux/macOS: detach from terminal to run in background
                else:
                    popen_kwargs['start_new_session'] = True
                
                process = subprocess.Popen(ssh_cmd, **popen_kwargs)
                
                # Wait a moment to see if it fails immediately
                time.sleep(2)
                
                if process.poll() is not None:
                    # Process ended, likely an error
                    stdout, stderr = process.communicate()
                    error_msg = stderr.decode() if stderr else stdout.decode()
                    self.log(f"Error creating tunnel: {error_msg}")
                    messagebox.showerror("Tunnel Error", f"Failed to create tunnel:\n{error_msg}")
                    self.root.after(0, lambda: self.create_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.status_var.set("Ready"))
                    return
                
                # Tunnel created successfully
                tunnel_info = {
                    'process': process,
                    'local_port': local_port,
                    'remote_ip': remote_ip,
                    'remote_port': remote_port,
                    'bastion': bastion,
                    'pid': process.pid
                }
                self.tunnels.append(tunnel_info)
                
                # Add to treeview
                self.root.after(0, lambda: self.tunnels_tree.insert(
                    "", tk.END,
                    values=(local_port, f"{remote_ip}:{remote_port}", "Active", process.pid)
                ))
                
                self.log(f"✓ Tunnel created successfully on port {local_port} (PID: {process.pid})")
                self.root.after(0, lambda: self.status_var.set(f"Tunnel active on port {local_port}"))
                self.root.after(0, lambda: self.create_btn.config(state=tk.NORMAL))
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
                messagebox.showerror("Error", f"Failed to create tunnel:\n{str(e)}")
                self.root.after(0, lambda: self.create_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("Ready"))
        
        # Start tunnel in background thread
        thread = threading.Thread(target=tunnel_thread, daemon=True)
        thread.start()
    
    def stop_selected_tunnel(self):
        """Stop the selected tunnel"""
        selection = self.tunnels_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a tunnel from the Active Tunnels list")
            return
        
        item = selection[0]
        values = self.tunnels_tree.item(item, "values")
        local_port = int(values[0])
        
        # Find and stop the tunnel
        for i, tunnel in enumerate(self.tunnels):
            if tunnel['local_port'] == local_port:
                try:
                    tunnel['process'].terminate()
                    tunnel['process'].wait(timeout=5)
                except Exception:
                    tunnel['process'].kill()
                
                self.tunnels.remove(tunnel)
                self.tunnels_tree.delete(item)
                self.log(f"✓ Tunnel on port {local_port} stopped")
                self.status_var.set(f"Tunnel on port {local_port} stopped")
                break
    
    def stop_all_tunnels(self):
        """Stop all active tunnels"""
        if not self.tunnels:
            messagebox.showinfo("Info", "No active tunnels to stop")
            return
        
        count = len(self.tunnels)
        for tunnel in self.tunnels[:]:  # Copy list to iterate safely
            try:
                tunnel['process'].terminate()
                tunnel['process'].wait(timeout=5)
            except Exception:
                tunnel['process'].kill()
            
            self.tunnels.remove(tunnel)
        
        # Clear treeview
        for item in self.tunnels_tree.get_children():
            self.tunnels_tree.delete(item)
        
        self.log(f"✓ Stopped {count} tunnel(s)")
        self.status_var.set("All tunnels stopped")
    
    def show_tunnel_menu(self, event):
        """Show context menu for tunnel"""
        item = self.tunnels_tree.identify_row(event.y)
        if item:
            self.tunnels_tree.selection_set(item)
            self.tunnel_menu.post(event.x_root, event.y_root)
    
    def save_configuration(self):
        """Save current active tunnels configuration to a file"""
        if not self.tunnels:
            messagebox.showinfo("No Tunnels", "No active tunnels to save. Create tunnels first.")
            return
        
        # Prepare configuration data
        config = {
            'bastion_host': self.bastion_host.get(),
            'key_file': self.key_file.get(),
            'tunnels': []
        }
        
        # Add all active tunnel configurations
        for tunnel in self.tunnels:
            config['tunnels'].append({
                'local_port': tunnel['local_port'],
                'remote_ip': tunnel['remote_ip'],
                'remote_port': tunnel['remote_port']
            })
        
        # Ask user for save location
        filename = filedialog.asksaveasfilename(
            title="Save Tunnel Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="tunnel_config.json"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=4)
                self.log(f"✓ Configuration saved to: {filename}")
                self.log(f"  Saved {len(config['tunnels'])} tunnel(s)")
                self.status_var.set(f"Configuration saved ({len(config['tunnels'])} tunnels)")
                messagebox.showinfo("Success", f"Configuration saved successfully!\n\nSaved {len(config['tunnels'])} tunnel(s) to:\n{filename}")
            except Exception as e:
                self.log(f"✗ Error saving configuration: {str(e)}")
                messagebox.showerror("Save Error", f"Failed to save configuration:\n{str(e)}")
    
    def load_configuration(self):
        """Load tunnel configuration from a file"""
        # Ask user to select config file
        filename = filedialog.askopenfilename(
            title="Load Tunnel Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="tunnel_config.json"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            
            # Validate config structure
            if 'bastion_host' not in config or 'key_file' not in config or 'tunnels' not in config:
                raise ValueError("Invalid configuration file format")
            
            # Check if there are active tunnels
            if self.tunnels:
                response = messagebox.askyesno(
                    "Active Tunnels",
                    "There are active tunnels. Do you want to stop them and load the new configuration?\n\n"
                    "Click 'Yes' to stop current tunnels and load config.\n"
                    "Click 'No' to cancel."
                )
                if response:
                    self.stop_all_tunnels()
                else:
                    return
            
            # Update bastion host and key file
            self.bastion_host.set(config.get('bastion_host', ''))
            self.key_file.set(config.get('key_file', ''))
            
            # Validate key file exists
            if not os.path.exists(self.key_file.get()):
                messagebox.showwarning(
                    "Key File Not Found",
                    f"The key file in the configuration was not found:\n{self.key_file.get()}\n\n"
                    "Please select the correct key file location."
                )
                self.browse_key_file()
            
            # Log loaded configuration
            self.log(f"✓ Configuration loaded from: {filename}")
            self.log(f"  Bastion Host: {config['bastion_host']}")
            self.log(f"  Key File: {config['key_file']}")
            self.log(f"  Tunnels to create: {len(config['tunnels'])}")
            
            # Ask if user wants to create all tunnels
            if config['tunnels']:
                response = messagebox.askyesno(
                    "Create Tunnels",
                    f"Configuration loaded successfully!\n\n"
                    f"Found {len(config['tunnels'])} tunnel(s) in the configuration.\n\n"
                    "Do you want to create all tunnels now?"
                )
                
                if response:
                    self.create_tunnels_from_config(config['tunnels'])
                else:
                    # Just update the form with first tunnel config
                    if config['tunnels']:
                        first_tunnel = config['tunnels'][0]
                        self.local_port.set(str(first_tunnel['local_port']))
                        self.remote_ip.set(first_tunnel['remote_ip'])
                        self.remote_port.set(str(first_tunnel['remote_port']))
                    self.status_var.set(f"Configuration loaded ({len(config['tunnels'])} tunnels)")
            else:
                self.status_var.set("Configuration loaded (no tunnels)")
                messagebox.showinfo("Loaded", "Configuration loaded successfully, but no tunnels were found in the file.")
        
        except json.JSONDecodeError as e:
            self.log(f"✗ Error: Invalid JSON file: {str(e)}")
            messagebox.showerror("Load Error", f"Invalid JSON file:\n{str(e)}")
        except Exception as e:
            self.log(f"✗ Error loading configuration: {str(e)}")
            messagebox.showerror("Load Error", f"Failed to load configuration:\n{str(e)}")
    
    def create_tunnels_from_config(self, tunnels_config, auto_load=False):
        """Create multiple tunnels from configuration"""
        if not self.bastion_host.get().strip():
            if not auto_load:
                messagebox.showerror("Error", "Bastion host is not set")
            else:
                self.log("⚠ Bastion host is not set, cannot create tunnels")
            return
        
        if not self.key_file.get().strip() or not os.path.exists(self.key_file.get()):
            if not auto_load:
                messagebox.showerror("Error", "Key file is not set or does not exist")
            else:
                self.log("⚠ Key file is not set or does not exist, cannot create tunnels")
            return
        
        self.status_var.set(f"Creating {len(tunnels_config)} tunnel(s)...")
        if not auto_load:
            self.create_btn.config(state=tk.DISABLED)
        
        def create_all_thread():
            success_count = 0
            fail_count = 0
            
            for tunnel_config in tunnels_config:
                try:
                    local_port = tunnel_config['local_port']
                    remote_ip = tunnel_config['remote_ip']
                    remote_port = tunnel_config['remote_port']
                    key_path = self.key_file.get()
                    bastion = self.bastion_host.get().strip()
                    
                    # Check if port is already in use
                    port_in_use = False
                    for tunnel in self.tunnels:
                        if tunnel['local_port'] == local_port:
                            port_in_use = True
                            break
                    
                    if port_in_use:
                        self.log(f"⚠ Skipping port {local_port} (already in use)")
                        fail_count += 1
                        continue
                    
                    # Build SSH command
                    ssh_cmd = [
                        "ssh",
                        "-i", key_path,
                        "-o", "StrictHostKeyChecking=accept-new",
                        "-L", f"{local_port}:{remote_ip}:{remote_port}",
                        "-N",
                        "-f",
                        bastion
                    ]
                    
                    self.log(f"Creating tunnel: localhost:{local_port} -> {remote_ip}:{remote_port}")
                    
                    # Start SSH process
                    popen_kwargs = {
                        'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE,
                    }
                    
                    if sys.platform == "win32":
                        try:
                            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                        except AttributeError:
                            popen_kwargs['creationflags'] = 0x08000000
                    else:
                        popen_kwargs['start_new_session'] = True
                    
                    process = subprocess.Popen(ssh_cmd, **popen_kwargs)
                    
                    # Wait a moment to check if it fails
                    time.sleep(1.5)
                    
                    if process.poll() is not None:
                        stdout, stderr = process.communicate()
                        error_msg = stderr.decode() if stderr else stdout.decode()
                        self.log(f"✗ Failed: port {local_port} - {error_msg.strip()}")
                        fail_count += 1
                        continue
                    
                    # Success
                    tunnel_info = {
                        'process': process,
                        'local_port': local_port,
                        'remote_ip': remote_ip,
                        'remote_port': remote_port,
                        'bastion': bastion,
                        'pid': process.pid
                    }
                    self.tunnels.append(tunnel_info)
                    
                    # Add to active tunnels treeview
                    self.root.after(0, lambda lp=local_port, rip=remote_ip, rp=remote_port, pid=process.pid: 
                                   self.tunnels_tree.insert("", tk.END, 
                                   values=(lp, f"{rip}:{rp}", "Active", pid)))
                    
                    self.log(f"✓ Created: port {local_port} (PID: {process.pid})")
                    success_count += 1
                    
                    # Small delay between tunnel creations
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.log(f"✗ Error creating tunnel: {str(e)}")
                    fail_count += 1
            
            # Update status
            result_msg = f"Created {success_count} tunnel(s)"
            if fail_count > 0:
                result_msg += f", {fail_count} failed"
            self.log(f"\n{result_msg}")
            self.root.after(0, lambda msg=result_msg: self.status_var.set(msg))
            if not auto_load:
                self.root.after(0, lambda: self.create_btn.config(state=tk.NORMAL))
        
        # Start creation in background thread
        thread = threading.Thread(target=create_all_thread, daemon=True)
        thread.start()
    
    def find_latest_config_file(self):
        """Find the most recently modified configuration file"""
        # Common locations to search for config files
        search_dirs = [
            Path.home() / "Documents",
            Path.home(),
            Path.cwd(),  # Current working directory
        ]
        
        # Also check the directory where the script is located
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            script_dir = Path(sys.executable).parent
        else:
            # If running as script
            script_dir = Path(__file__).parent
        
        search_dirs.append(script_dir)
        
        config_files = []
        
        # Search for .json files in common locations
        for search_dir in search_dirs:
            if search_dir.exists():
                try:
                    # Look for files matching common config patterns
                    patterns = ["*tunnel*.json", "*config*.json", "*.json"]
                    for pattern in patterns:
                        for config_file in search_dir.glob(pattern):
                            if config_file.is_file():
                                try:
                                    # Try to validate it's a valid config file
                                    with open(config_file, 'r') as f:
                                        config = json.load(f)
                                        if 'bastion_host' in config and 'tunnels' in config:
                                            config_files.append(config_file)
                                except (json.JSONDecodeError, KeyError):
                                    continue
                except (PermissionError, OSError):
                    continue
        
        if not config_files:
            return None
        
        # Return the most recently modified file
        latest = max(config_files, key=lambda p: p.stat().st_mtime)
        return latest
    
    def auto_load_latest_config(self):
        """Automatically load the latest configuration file on startup"""
        try:
            latest_config = self.find_latest_config_file()
            
            if latest_config:
                self.log(f"Found latest configuration: {latest_config}")
                self.log("Auto-loading configuration...")
                
                try:
                    with open(latest_config, 'r') as f:
                        config = json.load(f)
                    
                    # Validate config structure
                    if 'bastion_host' not in config or 'key_file' not in config or 'tunnels' not in config:
                        self.log("⚠ Configuration file format is invalid, skipping auto-load")
                        return
                    
                    # Update bastion host and key file
                    self.bastion_host.set(config.get('bastion_host', ''))
                    self.key_file.set(config.get('key_file', ''))
                    
                    # Check if key file exists
                    if not os.path.exists(self.key_file.get()):
                        self.log(f"⚠ Key file not found: {self.key_file.get()}")
                        self.log("Please select the correct key file location")
                        # Don't auto-create tunnels if key file is missing
                        return
                    
                    # Check if there are tunnels to create
                    if config.get('tunnels') and len(config['tunnels']) > 0:
                        self.log(f"Found {len(config['tunnels'])} tunnel(s) in configuration")
                        self.log("Auto-creating tunnels...")
                        
                        # Automatically create all tunnels
                        self.create_tunnels_from_config(config['tunnels'], auto_load=True)
                    else:
                        self.log("Configuration loaded, but no tunnels found")
                        self.status_var.set("Configuration loaded (no tunnels)")
                
                except json.JSONDecodeError as e:
                    self.log(f"⚠ Error reading configuration file: {str(e)}")
                except Exception as e:
                    self.log(f"⚠ Error loading configuration: {str(e)}")
            else:
                self.log("No saved configuration found. Starting with empty configuration.")
        
        except Exception as e:
            self.log(f"⚠ Error during auto-load: {str(e)}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.tunnels:
            if messagebox.askokcancel("Quit", "There are active tunnels. Stop them and quit?"):
                self.stop_all_tunnels()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    # Check if tkinter is available
    try:
        root = tk.Tk()
    except tk.TclError as e:
        print(f"Error: Tkinter is not available. {e}")
        print("\nTo install tkinter:")
        if sys.platform == "linux":
            print("  Ubuntu/Debian: sudo apt-get install python3-tk")
            print("  Fedora/RHEL: sudo dnf install python3-tkinter")
            print("  Arch: sudo pacman -S tk")
        elif sys.platform == "darwin":
            print("  macOS: tkinter should be included with Python.")
            print("  If not, reinstall Python from python.org")
        else:
            print("  Windows: tkinter should be included with Python.")
        sys.exit(1)
    
    app = TunnelManager(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

