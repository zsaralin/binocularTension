import pyrealsense2 as rs

def get_device_info():
    """
    Returns a list of dictionaries containing information about connected RealSense devices.
    Each dictionary contains the serial number, name, and product line.
    """
    ctx = rs.context()
    devices_info = []
    for d in ctx.query_devices():
        device_info = {
            'serial_number': d.get_info(rs.camera_info.serial_number),
            'name': d.get_info(rs.camera_info.name),
            'product_line': d.get_info(rs.camera_info.product_line)
        }
        devices_info.append(device_info)
        print(f"Found device: {device_info}")
    return devices_info

get_device_info()