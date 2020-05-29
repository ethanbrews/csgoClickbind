# Python auto clickbind for CS:GO

## How to set up

1. Install python 3.7 or newer
2. Install auto hot key
3. Clone this repository
4. Copy `gamestate_integration_clickbind.cfg` to the CS:GO config directory (probably at `C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\cfg`)
5. Run `pip3 install -r requirements.txt`
6. Run `python3 csgo_listener.py`

If you don't want the CS:GO integration, or want to use this for other games, you can skip step 4 then, instead of step 6, run `python3 simple_bind.py`

## How to use

Run the program before starting CS:GO. The script will detect which weapons you have enabled and for most non-automatic weapons the clickbind will be enabled.
To manually disable the clickbind, the default key is *F8*

## Editing the config

The config is stored as variables in `csgo_listener.py`.
To edit the weapons for which the bind is enabled, simply add or remove them from `WEAPONS_WITH_AUTO_FIRE_ENABLED`.
To change the address or port the HTTP server listens at, change the `SERVER_ADDRESS` variable in `csgo_listener.py` as well as modifying `gamestate_integration_clickbind.cfg`.
