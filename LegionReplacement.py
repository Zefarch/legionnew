import tkinter as tk
from tkinter import ttk
import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse


class NmapGui:
    def __init__(self, master, nmap_output):
        self.master = master
        self.master.title("Nmap Service Viewer")

        # Allow the window to resize
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        # Parse the Nmap XML output
        self.services_by_port, self.services_by_host = self.parse_nmap_output(nmap_output)

        # A dictionary to keep track of checked ports by IP (keyed by IP and port)
        self.checked_ports = defaultdict(lambda: defaultdict(bool))

        # Create the notebook (tabs)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Create Port View tab
        self.port_view_frame = ttk.Frame(self.notebook)
        self.port_view_frame.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(self.port_view_frame, text="Port View")

        # Create Host View tab
        self.host_view_frame = ttk.Frame(self.notebook)
        self.host_view_frame.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(self.host_view_frame, text="Host View")

        # Allow frames to resize
        for frame in [self.port_view_frame, self.host_view_frame]:
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

        # Create the tables for both views
        self.create_port_view_table(self.port_view_frame)
        self.create_host_view_table(self.host_view_frame)

    def parse_nmap_output(self, nmap_output):
        """
        Parse the Nmap XML output and organize services by port and by host.
        """
        services_by_port = defaultdict(list)
        services_by_host = defaultdict(list)

        # Parse XML
        tree = ET.ElementTree(ET.fromstring(nmap_output))
        root = tree.getroot()

        # Iterate through all hosts in the Nmap output
        for host in root.findall("host"):
            ip = host.find("address").get("addr")
            for port in host.findall(".//port"):
                port_id = port.get("portid")
                service = port.find("service")
                if service is not None:
                    service_name = service.get("name")
                    service_product = service.get("product", "N/A")
                    service_version = service.get("version", "N/A")
                    # Store the service information by port and by host
                    services_by_port[port_id].append((ip, service_name, service_product, service_version))
                    services_by_host[ip].append((port_id, service_name, service_product, service_version))

        return services_by_port, services_by_host

    def create_port_view_table(self, parent_frame):
        """
        Create the Port View table-like structure in tkinter to display services grouped by port.
        """
        # Define columns
        columns = ("Port", "Host IP", "Service", "Product", "Version", "Checked", "Comments")

        # Create a treeview widget
        self.tree_port = ttk.Treeview(parent_frame, columns=columns, show="headings")
        self.tree_port.grid(row=0, column=0, sticky="nsew")

        # Add column headings
        for col in columns:
            self.tree_port.heading(col, text=col)

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree_port.yview)
        self.tree_port.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure resizing behavior for the parent frame
        parent_frame.grid_rowconfigure(0, weight=1)  # Allow the Treeview to expand vertically
        parent_frame.grid_columnconfigure(0, weight=1)  # Allow the Treeview to expand horizontally

        # Define styles for bold and normal rows
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Helvetica", 10))
        self.style.configure("Treeview.Bold", font=("Helvetica", 10, "bold"))

        # Insert data grouped by port
        for port, hosts in sorted(self.services_by_port.items(), key=lambda x: int(x[0])):
            # Insert the bolded port row
            parent_item = self.tree_port.insert(
                "", "end", text=f"Port {port}", values=(port, "", "", "", "", "", ""), tags=("bold",)
            )

            # Add each associated host and its details as a normal row
            for host in hosts:
                ip, service_name, service_product, service_version = host
                checked = self.checked_ports[ip][port]
                self.tree_port.insert(
                    parent_item,
                    "end",
                    values=("", ip, service_name, service_product, service_version, "✔" if checked else "", ""),
                    tags=("normal",),
                )

            # Expand the parent item (port) so that its child rows (hosts/services) are visible by default
            self.tree_port.item(parent_item, open=True)

        # Apply tags for bold and normal rows
        self.tree_port.tag_configure("bold", font=("Helvetica", 10, "bold"))
        self.tree_port.tag_configure("normal", font=("Helvetica", 10))


    def create_host_view_table(self, parent_frame):
        """
        Create the Host View table-like structure in tkinter to display hosts as bold rows,
        followed by their associated data (ports, services, etc.) as child rows.
        """
        # Define columns for the child rows
        columns = ("Host IP", "Port", "Service", "Product", "Version", "Checked", "Comments")

        # Create a treeview widget
        self.tree_host = ttk.Treeview(parent_frame, columns=columns, show="headings")
        self.tree_host.grid(row=0, column=0, sticky="nsew")

        # Add column headings
        for col in columns:
            self.tree_host.heading(col, text=col)

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree_host.yview)
        self.tree_host.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure resizing behavior for the parent frame
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        # Define styles for bold and normal rows
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Helvetica", 10))
        self.style.configure("Treeview.Bold", font=("Helvetica", 10, "bold"))

        # Insert data grouped by host
        for host, ports in sorted(self.services_by_host.items()):
            # Insert the bolded host row
            parent_item = self.tree_host.insert(
                "", "end", values=(host, "", "", "", "", "", ""), tags=("bold",)
            )

            # Add each associated port and its details as a normal row
            for port in ports:
                port_id, service_name, service_product, service_version = port
                checked = self.checked_ports[host][port_id]
                self.tree_host.insert(
                    parent_item,
                    "end",
                    values=("", port_id, service_name, service_product, service_version, "✔" if checked else "", ""),
                    tags=("normal",),
                )

            # Expand the parent item (host) so that its child rows (ports/services) are visible by default
            self.tree_host.item(parent_item, open=True)

        # Apply tags for bold and normal rows
        self.tree_host.tag_configure("bold", font=("Helvetica", 10, "bold"))
        self.tree_host.tag_configure("normal", font=("Helvetica", 10))



def read_nmap_output(file_path):
    """
    Read the Nmap XML output from a file.
    """
    with open(file_path, "r") as file:
        return file.read()


def main():
    # Setup command-line argument parsing
    parser = argparse.ArgumentParser(description="Nmap Service Viewer")
    parser.add_argument("nmap_file", help="Path to the Nmap XML output file")
    args = parser.parse_args()

    # Read the Nmap output from the specified file
    nmap_output = read_nmap_output(args.nmap_file)

    # Create the main window
    root = tk.Tk()

    # Create the Nmap GUI and display the results
    app = NmapGui(root, nmap_output)

    # Run the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()
