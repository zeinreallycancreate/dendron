# Automatic IP Configuration Guide

The setup scripts now automatically configure IP addresses based on your installation type. No manual config editing required!

## How It Works

### Option 1: Client Only Setup

When you run `setup_ubuntu.sh`, it will ask:
```
Setup Type:
  1) Client only (will connect to remote server)
  2) Server + Client (this Pi runs both)

Choose setup type (1 or 2):
```

**Choose 1** for a regular scanner node.

It will then ask:
```
Enter server IP address (e.g., 192.168.1.100):
```

Enter the IP of your server Pi, and the script will:
- Automatically create/update the config file
- Set `server_url: "http://YOUR_IP:5000"`
- No manual editing needed!

### Option 2: Server + Client Setup

**Choose 2** for the Pi that runs both server and scanner.

The script will:
- Automatically set `server_url: "http://localhost:5000"`
- Create the config file with correct settings
- Guide you to install server dependencies next

## Complete Setup Examples

### Example 1: 2-Pi Setup (1 Dual-Role + 1 Client)

**On Pi #1 (Server + Scanner):**
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts

# Install client deps with automatic config
sudo ./setup_ubuntu.sh
# Choose: 2 (Server + Client)
# Choose node: 1

# Install server deps
sudo ./setup_server.sh
# Choose: 2 (Server + Scanner)

# Start both
sudo ./start_server_and_node.sh ../configs/node1_config.yml
```

**On Pi #2 (Client Only):**
```bash
git clone https://github.com/zeinreallycancreate/dendron.git
cd dendron/scripts

# Install with automatic config
sudo ./setup_ubuntu.sh
# Choose: 1 (Client only)
# Enter server IP: 192.168.1.100 (Pi #1's IP)
# Choose node: 2

# Start scanner
sudo ./start_node2.sh
```

### Example 2: 3-Pi Setup (1 Dual-Role + 2 Clients)

**On Pi #1 (Server + Scanner):**
```bash
sudo ./setup_ubuntu.sh
# Choose: 2 (Server + Client)
# Node: 1

sudo ./setup_server.sh
# Choose: 2 (Server + Scanner)

sudo ./start_server_and_node.sh ../configs/node1_config.yml
```

**On Pi #2 (Client Only):**
```bash
sudo ./setup_ubuntu.sh
# Choose: 1 (Client only)
# Server IP: 192.168.1.100
# Node: 2

sudo ./start_node2.sh
```

**On Pi #3 (Client Only):**
```bash
sudo ./setup_ubuntu.sh
# Choose: 1 (Client only)
# Server IP: 192.168.1.100
# Node: 3

sudo ./start_node3.sh
```

## What Gets Configured Automatically

The setup scripts now handle:

1. **Server IP**: Automatically set to `localhost` for dual-role or entered IP for clients
2. **Config File Creation**: Creates `configs/nodeX_config.yml` if it doesn't exist
3. **Config File Update**: Updates existing configs with new server IP
4. **Node Number**: Uses your chosen node number in config
5. **Next Steps**: Shows appropriate commands based on setup type

## Manual Override

If you need to change the server IP later:

```bash
nano configs/node1_config.yml
# Change: server_url: "http://NEW_IP:5000"
```

Or run setup again - it will update the existing config file.

## Benefits

✅ **No manual config editing** - scripts do it for you
✅ **No mistakes** - automatic configuration is error-free  
✅ **Faster setup** - skip the manual IP entry step
✅ **Beginner friendly** - just answer a few questions
✅ **Flexible** - still supports manual overrides if needed

## Finding Your Server IP

If you need to find the server Pi's IP address for client nodes:

**On the server Pi:**
```bash
hostname -I
```

Or check the output from `setup_server.sh` - it displays the IP automatically.

## Troubleshooting

### Wrong IP Configured?

Just run setup again:
```bash
sudo ./setup_ubuntu.sh
```

It will detect the existing config and update it with the new IP.

### Config File Missing?

The setup script creates it automatically. If deleted, run:
```bash
sudo ./setup_ubuntu.sh
```

### Need Different Node Number?

Run setup again and choose a different node number. It will create a new config file for that node.

---

**No more manual IP configuration - the scripts handle everything!** 🎉
