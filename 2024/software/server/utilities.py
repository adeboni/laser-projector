import platform
import subprocess
import pyautogui

def ping(host: str) -> bool:
    """Returns True if host responds to a ping request"""

    if platform.system().lower() == 'windows':
        command = f'ping -n 1 {host}'
        window_creation_flag = 0x08000000  # CREATE_NO_WINDOW
        process = subprocess.Popen(command, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   creationflags=window_creation_flag)
    else:
        command = ['ping', '-c 1', host]
        process = subprocess.Popen(command, 
                                   stdin=subprocess.PIPE, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)

    console_out = str(process.communicate()[0])
    ret_code = process.poll()

    if (ret_code != 0) or ("expired" in console_out) or ("unreachable" in console_out): 
        return False
    else:
        return True

def focus(win_name) -> None:
    if platform.system().lower() == 'windows':
        try:
            w = pyautogui.getWindowsWithTitle(win_name)
            if len(w) > 0:
                pyautogui.click()
                w[0].activate()
        except:
            pass
