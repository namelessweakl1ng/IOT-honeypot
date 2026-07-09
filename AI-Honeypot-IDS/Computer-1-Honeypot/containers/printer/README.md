# Printer honeypot
Two surfaces:
- Web UI on **8087** → 5000 (default creds `admin/admin`, `/admin?file=` path traversal, `/status` recon)
- Raw PJL/JetDirect on **9100** (accepts `@PJL` commands, logs every raw payload)

Logs both HTTP and PJL interactions as canonical JSON.
