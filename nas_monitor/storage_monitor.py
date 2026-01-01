import subprocess
import json

class StorageMonitor:
    def __init__(self):
        # Карта {Серийный_Номер: Имя_Пула}
        self.serial_to_pool = {}

    def _get_sys_mapping(self):
        """Использует lsblk для связи системных имен с серийными номерами"""
        mapping = {} # {dev_name: serial}
        cmd = ["lsblk", "-dno", "NAME,SERIAL"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 2:
                mapping[parts[0]] = parts[1]
        return mapping

    def get_zfs_data(self):
        """Сбор данных ZFS и построение карты серийных номеров"""
        # 1. Сводные данные по пулам
        cmd_list = ["zpool", "list", "-H", "-p", "-o", "name,size,free,alloc,frag,health"]
        res_list = subprocess.run(cmd_list, capture_output=True, text=True)
        
        pools = {}
        for line in res_list.stdout.strip().split('\n'):
            if not line: continue
            parts = line.split()
            name, size, free = parts[0], int(parts[1]), int(parts[2])
            pools[name] = {
                "name": name,
                "total_gb": round(size / (1024**3), 2),
                "free_percent": round((free / size * 100), 1) if size > 0 else 0,
                "frag": parts[4],
                "health": parts[5],
                "resilver": None
            }

        # 2. Детальный статус для маппинга дисков
        cmd_status = ["zpool", "status"]
        res_status = subprocess.run(cmd_status, capture_output=True, text=True)
        
        current_pool = None
        for line in res_status.stdout.split('\n'):
            line = line.strip()
            if line.startswith("pool:"):
                current_pool = line.split(":")[1].strip()
            elif "scan:" in line and current_pool:
                if "resilver" in line:
                    pools[current_pool]["resilver"] = line.replace("scan:", "").strip()
            
            # Ищем строки дисков (содержат серийник в составе имени by-id)
            elif any(s in line for s in ["ONLINE", "FAULTED", "DEGRADED"]):
                parts = line.split()
                vdev_name = parts[0]
                if vdev_name == current_pool or "raidz" in vdev_name or "mirror" in vdev_name:
                    continue
                
                # Извлекаем серийник из имени (например, из ata-HGST_..._V9K278PL)
                # Обычно серийник - это всё, что после последнего подчеркивания
                serial_candidate = vdev_name.split('_')[-1].split('-part')[0]
                self.serial_to_pool[serial_candidate] = current_pool

        return list(pools.values())

    def get_smart_data(self):
        """Сбор данных SMART с сопоставлением через серийный номер"""
        scan_cmd = ["smartctl", "--scan", "--json"]
        scan_res = subprocess.run(scan_cmd, capture_output=True, text=True)
        devices = json.loads(scan_res.stdout).get("devices", [])

        smart_results = []
        for dev in devices:
            path = dev['name']
            cmd_smart = ["smartctl", "-a", path, "--json"]
            res_smart = subprocess.run(cmd_smart, capture_output=True, text=True)
            data = json.loads(res_smart.stdout)

            serial = data.get("serial_number", "").strip()
            # Пытаемся найти пул по серийнику
            pool_name = self.serial_to_pool.get(serial, "---")
            
            # Если не нашли по серийнику напрямую, ищем вхождение серийника в ключи карты
            if pool_name == "---":
                for s_key, p_val in self.serial_to_pool.items():
                    if s_key in serial or serial in s_key:
                        pool_name = p_val
                        break

            # Метрики
            temp = data.get("temperature", {}).get("current", "N/A")
            errs = 0
            if "nvme_smart_health_information_log" in data:
                nvme = data["nvme_smart_health_information_log"]
                temp = nvme.get("temperature", temp)
                errs = nvme.get("media_errors", 0)
            else:
                errs = data.get("ata_smart_error_log", {}).get("summary", {}).get("count", 0)

            smart_results.append({
                "dev": path,
                "pool": pool_name,
                "model": data.get("model_name", "Unknown"),
                "sn": serial,
                "temp": temp,
                "errs": errs,
                "ok": data.get("smart_status", {}).get("passed", False)
            })
        return smart_results

# --- ВЫВОД ---

if __name__ == "__main__":
    mon = StorageMonitor()
    pools = mon.get_zfs_data()
    disks = mon.get_smart_data()

    print(f"\n{'[ ZFS POOLS ]':^90}")
    print(f"{'-'*90}")
    print(f"{'NAME':<12} | {'HEALTH':<10} | {'TOTAL GB':<10} | {'FREE %':<8} | {'FRAG':<6} | {'STATUS'}")
    for p in pools:
        st = p['resilver'] if p['resilver'] else "Healthy"
        print(f"{p['name']:<12} | {p['health']:<10} | {p['total_gb']:<10} | {p['free_percent']:<8} | {p['frag']:<6} | {st}")

    print(f"\n{'[ PHYSICAL DISKS SMART ]':^90}")
    print(f"{'-'*90}")
    print(f"{'DEV':<10} | {'POOL':<12} | {'TEMP':<5} | {'ERRS':<6} | {'SMART':<8} | {'SERIAL':<15} | {'MODEL'}")
    for d in disks:
        health = "OK" if d['ok'] else "FAIL"
        print(f"{d['dev']:<10} | {d['pool']:<12} | {d['temp']:<3}°C | {d['errs']:<6} | {health:<8} | {d['sn']:<15} | {d['model']}")

    from pprint import pprint
    pprint(pools)
    pprint(disks)