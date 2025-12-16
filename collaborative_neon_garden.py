# ⋆⋆⋆ LAN AUTO-DISCOVERY COLLABORATIVE NEON GARDEN ⋆⋆⋆

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import random
import sounddevice as sd
import threading
import socket
import json
import tkinter as tk
import mido
import sys
import netifaces
import time

# ─── CONFIG ─────────────────────────────
LAYERS = 17
GRID_SIZE = 30
SIGILS = ["⊱","⟡","⚚","⩀","⦿"]
EMOJIS = ["🌸","✨","🫧","🌼","💫","🍃","🌙","⚡","🪞"]

layers = [np.random.rand(GRID_SIZE, GRID_SIZE)*0.3 for _ in range(LAYERS)]
memory_ghosts = [np.zeros((GRID_SIZE, GRID_SIZE)) for _ in range(LAYERS)]
observer_attention = [0.0 for _ in range(LAYERS)]
audio_level = 0.0

midi_triggered_layers = []
remote_commands = []
client_connections = []

# ─── PERFORMANCE VARIABLES ─────────────
bloom_intensity = 0.5
glitch_speed = 0.05
audio_reactive = True
neon_glow = True

# ─── NETWORK CONFIG ────────────────────
HOST = '0.0.0.0'
PORT = 5000
DISCOVERY_PORT = 5001
DISCOVERY_INTERVAL = 1.0  # seconds

def get_local_ip():
    try:
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for link in addrs[netifaces.AF_INET]:
                    ip = link['addr']
                    if ip != '127.0.0.1':
                        return ip
    except: pass
    return '127.0.0.1'

# ─── NETWORK FUNCTIONS ─────────────────
def handle_client(conn, addr):
    global remote_commands, client_connections
    client_connections.append(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data: break
            try:
                cmd = json.loads(data.decode())
                remote_commands.append(cmd)
            except:
                pass
    finally:
        client_connections.remove(conn)
        conn.close()

def broadcast_command(cmd):
    for conn in client_connections:
        try:
            conn.send(json.dumps(cmd).encode())
        except:
            pass

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {get_local_ip()}:{PORT}")
    threading.Thread(target=udp_broadcast_thread, daemon=True).start()
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# ─── UDP BROADCAST FOR AUTO-DISCOVERY ──
def udp_broadcast_thread():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = get_local_ip().encode()
    while True:
        s.sendto(message, ('<broadcast>', DISCOVERY_PORT))
        time.sleep(DISCOVERY_INTERVAL)

def listen_for_host():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', DISCOVERY_PORT))
    s.settimeout(10)
    try:
        data, addr = s.recvfrom(1024)
        host_ip = data.decode()
        print(f"Discovered host at {host_ip}")
        return host_ip
    except:
        print("No host discovered on LAN.")
        return None

def connect_to_server(server_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, PORT))
    return s

# ─── AUDIO STREAM ───────────────────────
def audio_callback(indata, frames, time, status):
    global audio_level
    if audio_reactive:
        audio_level = np.linalg.norm(indata)

stream = sd.InputStream(callback=audio_callback)
stream.start()

# ─── FIGURE FULLSCREEN ─────────────────
fig, axes = plt.subplots(1, LAYERS, figsize=(24,4))
plt.subplots_adjust(wspace=0,hspace=0)
for ax in axes: ax.axis('off')
cmap = plt.cm.magma_r

# ─── LAYER FUNCTIONS ───────────────────
def collapse_layer(layer_index):
    layers[layer_index] = np.random.rand(GRID_SIZE, GRID_SIZE)
    memory_ghosts[layer_index] = np.zeros((GRID_SIZE, GRID_SIZE))

def overlay_symbols(ax, layer_data, layer_index, frame):
    num_symbols = random.randint(5,18)
    for _ in range(num_symbols):
        x, y = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
        symbol = random.choice(SIGILS + EMOJIS)
        alpha = 0.5 + random.random()*0.5
        if neon_glow:
            alpha += np.sin(random.random()*frame*0.1)*0.2
        color = (0.2,1.0,1.0) if symbol in SIGILS else (1.0,0.8,0.2)
        ax.text(y, x, symbol, color=color, fontsize=14, ha='center', va='center', alpha=min(alpha,1.0))

# ─── MIDI INPUT ─────────────────────────
def midi_listener(send_global=False):
    global midi_triggered_layers
    try:
        inport = mido.open_input()
        for msg in inport.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                layer_index = msg.note % LAYERS
                midi_triggered_layers.append(layer_index)
                if send_global:
                    broadcast_command({'type':'midi','layer':layer_index})
    except Exception as e:
        print("MIDI input unavailable:", e)

def start_midi_thread(send_global=False):
    threading.Thread(target=midi_loop, args=(send_global,), daemon=True).start()

def midi_loop(send_global):
    while True:
        midi_listener(send_global)

# ─── PERFORMANCE GUI ────────────────────
def create_gui(send_func=None):
    global bloom_intensity, glitch_speed, audio_reactive, neon_glow

    root = tk.Tk()
    root.title("Collaborative Garden Installer")

    tk.Label(root, text="Bloom Intensity").pack()
    bloom_slider = tk.Scale(root, from_=0.1, to=1.0, resolution=0.05, orient='horizontal',
                            command=lambda v: set_bloom(v))
    bloom_slider.set(bloom_intensity)
    bloom_slider.pack()

    tk.Label(root, text="Glitch Speed").pack()
    glitch_slider = tk.Scale(root, from_=0.01, to=0.2, resolution=0.01, orient='horizontal',
                             command=lambda v: set_glitch(v))
    glitch_slider.set(glitch_speed)
    glitch_slider.pack()

    audio_check = tk.Checkbutton(root, text="Audio Reactive", command=lambda: toggle_audio())
    audio_check.select()
    audio_check.pack()

    neon_check = tk.Checkbutton(root, text="Neon Glow", command=lambda: toggle_neon())
    neon_check.select()
    neon_check.pack()

    collapse_frame = tk.Frame(root)
    collapse_frame.pack()
    for i in range(LAYERS):
        tk.Button(collapse_frame, text=f"Collapse {i+1}", command=lambda l=i: collapse_layer_gui(l, send_func)).grid(row=i//4, column=i%4)

    tk.Button(root, text="Collapse All", command=lambda: collapse_all_gui(send_func), bg='red', fg='white').pack()

    def set_bloom(v):
        global bloom_intensity
        bloom_intensity = float(v)
        if send_func: send_func({'type':'adjust','param':'bloom','value':bloom_intensity})

    def set_glitch(v):
        global glitch_speed
        glitch_speed = float(v)
        if send_func: send_func({'type':'adjust','param':'glitch','value':glitch_speed})

    def toggle_audio():
        global audio_reactive
        audio_reactive = not audio_reactive
        if send_func: send_func({'type':'adjust','param':'audio_reactive','value':audio_reactive})

    def toggle_neon():
        global neon_glow
        neon_glow = not neon_glow
        if send_func: send_func({'type':'adjust','param':'neon_glow','value':neon_glow})

    def collapse_layer_gui(layer, send_func):
        collapse_layer(layer)
        if send_func: send_func({'type':'collapse','layer':layer})

    def collapse_all_gui(send_func):
        for i in range(LAYERS):
            collapse_layer(i)
            if send_func: send_func({'type':'collapse','layer':i})

    threading.Thread(target=root.mainloop, daemon=True).start()

# ─── MAIN LOOP ─────────────────────────
def update_layers(frame):
    global remote_commands, midi_triggered_layers
    for cmd in remote_commands:
        if cmd['type'] == 'midi':
            layer = cmd['layer'] % LAYERS
            midi_triggered_layers.append(layer)
        elif cmd['type'] == 'collapse':
            collapse_layer(cmd['layer'] % LAYERS)
        elif cmd['type'] == 'adjust':
            param = cmd['param']
            val = cmd['value']
            globals()[param] = val
    remote_commands = []

    for i in range(LAYERS):
        glitch = np.random.rand(GRID_SIZE,GRID_SIZE)*0.1*(1+audio_level*3)*glitch_speed
        layers[i] = np.clip(layers[i]+glitch+observer_attention[i]*0.3, 0,1)
        observer_attention[i] *= 0.95
        memory_ghosts[i] = np.clip(memory_ghosts[i]*0.95 + layers[i]*0.05,0,1)
        if i>0: layers[i-1] += memory_ghosts[i]*0.03
        if i<LAYERS-1: layers[i+1] += memory_ghosts[i]*0.03

        if i in midi_triggered_layers:
            layers[i] += np.random.rand(GRID_SIZE,GRID_SIZE)*bloom_intensity
            midi_triggered_layers.remove(i)

        depth_factor = 1.0 - i*0.03
        axes[i].imshow((layers[i]*0.8 + memory_ghosts[i]*0.2)*depth_factor, cmap=cmap, vmin=0,vmax=1)
        overlay_symbols(axes[i], layers[i], i, frame)
    return axes

# ─── LAUNCH INSTALLER ───────────────────
if __name__ == "__main__":
    print("Welcome to the Collaborative Neon Garden Installer!")
    mode = input("Select mode [host/client]: ").strip().lower()

    if mode == "host":
        local_ip = get_local_ip()
        print(f"Detected local IP: {local_ip}")
        threading.Thread(target=start_server, daemon=True).start()
        create_gui(send_func=broadcast_command)
        start_midi_thread(send_global=True)

    elif mode == "client":
        print("Searching for host on LAN...")
        host_ip = listen_for_host()
        if host_ip is None:
            host_ip = input("Enter host IP manually: ").strip()
        s = connect_to_server(host_ip)
        create_gui(send_func=lambda cmd: s.send(json.dumps(cmd).encode()))
        start_midi_thread(send_global=False)

    else:
        print("Invalid mode, exiting.")
        sys.exit()

    manager = plt.get_current_fig_manager()
    try: manager.full_screen_toggle()
    except: pass

    ani = animation.FuncAnimation(fig, update_layers, frames=2000, interval=50, blit=False)
    plt.show()
    stream.stop()
