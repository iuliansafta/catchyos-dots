source /usr/share/cachyos-fish-config/cachyos-config.fish

# overwrite greeting
# potentially disabling fastfetch
#function fish_greeting
#    # smth smth
#end

# Pi
fish_add_path "/home/iulian/.local/share/pi-node/node-v22.22.3-linux-x64/bin"

# bun
set --export BUN_INSTALL "$HOME/.bun"
set --export PATH $BUN_INSTALL/bin $PATH

# Solana CLI (Agave installer)
fish_add_path "$HOME/.local/share/solana/install/active_release/bin"

alias solana-usbc="/home/iulian/.local/share/solana-usbc/bin/solana"
