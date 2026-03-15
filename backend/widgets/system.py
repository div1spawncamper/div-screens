"""System data source: CPU, RAM, Disk, Network metrics via psutil."""

import os
import platform
import subprocess
import time
from datetime import datetime
from typing import Optional

import psutil


class SystemDataSource:
    """Gathers system metrics. All methods return current values."""

    def __init__(self):
        self._prev_net_sent = 0
        self._prev_net_recv = 0
        self._prev_time = time.time()
        self._drive_labels: dict[str, str] = {}

        # Prime CPU counters
        psutil.cpu_percent(interval=0.1)
        psutil.cpu_percent(interval=0, percpu=True)

        # Fetch drive labels on init (Windows via WSL or native)
        self._fetch_drive_labels()

    def _fetch_drive_labels(self):
        """Try to get Windows drive labels (works on native Windows and WSL)."""
        if platform.system() == "Windows":
            import ctypes
            for letter in "CDEFGHIJ":
                try:
                    buf = ctypes.create_unicode_buffer(256)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        f"{letter}:\\", buf, 256, None, None, None, None, 0
                    )
                    if buf.value:
                        self._drive_labels[letter] = buf.value
                except:
                    pass
        else:
            # WSL or Linux: try cmd.exe for Windows drives
            for letter in "CDEFGHIJ":
                mnt = f"/mnt/{letter.lower()}"
                if os.path.isdir(mnt):
                    try:
                        result = subprocess.run(
                            ["cmd.exe", "/c", f"vol {letter}:"],
                            capture_output=True, timeout=5,
                        )
                        out = result.stdout.decode("cp850", errors="replace")
                        for line in out.splitlines():
                            line = line.strip()
                            if " es " in line:
                                label = line.split(" es ")[-1].strip()
                                if "no tiene etiqueta" not in label:
                                    self._drive_labels[letter] = label
                                break
                            elif " is " in line:
                                label = line.split(" is ")[-1].strip()
                                if "has no label" not in label:
                                    self._drive_labels[letter] = label
                                break
                    except:
                        pass

    def get(self, source: str):
        """Get a metric value by dotted source name (e.g. 'cpu.percent')."""
        parts = source.split(".")
        if not parts:
            return None

        category = parts[0]

        if category == "cpu":
            return self._get_cpu(parts[1] if len(parts) > 1 else "percent")
        elif category == "ram":
            return self._get_ram(parts[1] if len(parts) > 1 else "percent")
        elif category == "disk":
            drive = parts[1] if len(parts) > 1 else "C"
            metric = parts[2] if len(parts) > 2 else "percent"
            return self._get_disk(drive, metric)
        elif category == "net":
            return self._get_net(parts[1] if len(parts) > 1 else "upload_speed")
        elif category == "sys":
            return self._get_sys(parts[1] if len(parts) > 1 else "uptime")

        return None

    def _get_cpu(self, metric: str):
        if metric == "percent":
            return psutil.cpu_percent(interval=0)
        elif metric == "percent_per_core":
            return psutil.cpu_percent(interval=0, percpu=True)
        elif metric == "frequency":
            freq = psutil.cpu_freq()
            return f"{freq.current / 1000:.2f}" if freq else "N/A"
        elif metric == "cores":
            return psutil.cpu_count()
        elif metric == "cores_physical":
            return psutil.cpu_count(logical=False)
        return None

    def _get_ram(self, metric: str):
        mem = psutil.virtual_memory()
        if metric == "percent":
            return mem.percent
        elif metric == "used":
            return f"{mem.used / 1024 ** 3:.1f}"
        elif metric == "total":
            return f"{mem.total / 1024 ** 3:.0f}"
        elif metric == "used_gb":
            return mem.used / 1024 ** 3
        elif metric == "total_gb":
            return mem.total / 1024 ** 3
        return None

    def _get_disk(self, drive: str, metric: str):
        # Determine mount point
        if platform.system() == "Windows":
            mount = f"{drive.upper()}:\\"
        else:
            mount = f"/mnt/{drive.lower()}"
            if not os.path.isdir(mount):
                mount = "/" if drive.upper() == "C" else None

        if not mount:
            return None

        try:
            usage = psutil.disk_usage(mount)
        except:
            return None

        if metric == "percent":
            return usage.percent
        elif metric == "used":
            return f"{usage.used / 1024 ** 3:.0f}"
        elif metric == "total":
            return f"{usage.total / 1024 ** 3:.0f}"
        elif metric == "label":
            return self._drive_labels.get(drive.upper(), f"{drive.upper()}:")
        return None

    def _get_net(self, metric: str):
        net = psutil.net_io_counters()
        now = time.time()
        dt = max(now - self._prev_time, 0.1)

        up_speed = (net.bytes_sent - self._prev_net_sent) / dt if self._prev_net_sent else 0
        dn_speed = (net.bytes_recv - self._prev_net_recv) / dt if self._prev_net_recv else 0
        self._prev_net_sent = net.bytes_sent
        self._prev_net_recv = net.bytes_recv
        self._prev_time = now

        if metric == "upload_speed":
            return up_speed
        elif metric == "download_speed":
            return dn_speed
        elif metric == "upload_speed_fmt":
            return self._format_speed(up_speed)
        elif metric == "download_speed_fmt":
            return self._format_speed(dn_speed)
        elif metric == "total_sent":
            return f"{net.bytes_sent / 1024 ** 3:.1f}"
        elif metric == "total_recv":
            return f"{net.bytes_recv / 1024 ** 3:.1f}"
        return None

    def _get_sys(self, metric: str):
        if metric == "uptime":
            boot = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot
            days = uptime.days
            hours = int((uptime.total_seconds() % 86400) // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            return f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"
        elif metric == "processes":
            return len(psutil.pids())
        elif metric == "load":
            try:
                l1, l5, l15 = os.getloadavg()
                return f"{l1:.1f} {l5:.1f} {l15:.1f}"
            except:
                return "N/A"
        return None

    @staticmethod
    def _format_speed(b: float) -> str:
        if b < 1024:
            return f"{b:.0f} B/s"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB/s"
        else:
            return f"{b / 1024 / 1024:.1f} MB/s"
