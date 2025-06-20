import json
import os

from utils.loadconfig import load_config

config = load_config()

FILENAME = config['Audio']['AudiosJson']

def load_data():
    if os.path.exists(FILENAME):
        with open(FILENAME, 'r') as file:
            data = json.load(file)
            return data
    return {}

def save_data(data):
    with open(FILENAME, 'w') as file:
        json.dump(data, file, indent=4)

def add_channel(guild_id: int, channel_id: int, duration: int, audio_duration: int = None, provability: int = 50, explicit: bool = False):
    """Add a new Audio Channel to bot Enter
    
    ### Atributtes:
    Guild Id : Int
    Channel Id : Int
    Duration : Int
    Audio Duration : Int or None
    Provability : Int
    Explicit : Bool
    """
    data = load_data()
    if str(guild_id) not in data:
        data[str(guild_id)] = {}
    data[str(guild_id)][str(channel_id)] = {
        "duration": duration,
        "audio_duration": audio_duration,
        "provability": provability,
        "explicit": explicit
    }
    save_data(data)

def remove_channel(guild_id: int, channel_id: int):
    """Remove a Audio Channel to bot not enter
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    
    ### Returns:
    True if success
    False if fail"""
    data = load_data()
    if str(guild_id) in data and str(channel_id) in data[str(guild_id)]:
        del data[str(guild_id)][str(channel_id)]
        save_data(data)
        return True
    else:
        return False

def channel_exists(guild_id: int, channel_id: int) -> bool:
    """Verifica se o canal já está no sistema.
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    
    ### Returns:
    True se o canal existe, False caso contrário."""
    data = load_data()
    return str(guild_id) in data and str(channel_id) in data[str(guild_id)]

def modify_duration(guild_id: int, channel_id: int, new_duration: int):
    """Modify duration of a Audio Channel to bot enter
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    New Duration : int
    
    ### Returns:
    True if success
    False if fail"""
    data = load_data()
    if str(guild_id) in data and str(channel_id) in data[str(guild_id)]:
        data[str(guild_id)][str(channel_id)]["duration"] = new_duration
        save_data(data)
        return True
    else:
        return False

def modify_audio_duration(guild_id: int, channel_id: int, new_audio_duration: int):
    """Modify audio duration of a Audio Channel
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    New Audio Duration : int or None
    
    ### Returns:
    True if success
    False if fail"""
    data = load_data()
    if str(guild_id) in data and str(channel_id) in data[str(guild_id)]:
        data[str(guild_id)][str(channel_id)]["audio_duration"] = new_audio_duration
        save_data(data)
        return True
    else:
        return False

def modify_provability(guild_id: int, channel_id: int, new_provability: int):
    """Modify provability of a Audio Channel
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    New Provability : int
    
    ### Returns:
    True if success
    False if fail"""
    data = load_data()
    if str(guild_id) in data and str(channel_id) in data[str(guild_id)]:
        data[str(guild_id)][str(channel_id)]["provability"] = new_provability
        save_data(data)
        return True
    else:
        return False
    
def modify_explicit(guild_id: int, channel_id: int, explicit: bool):
    """Modify explicit flag of a Audio Channel
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    Explicit : bool
    
    ### Returns:
    True if success
    False if fail"""
    data = load_data()
    if str(guild_id) in data and str(channel_id) in data[str(guild_id)]:
        data[str(guild_id)][str(channel_id)]["explicit"] = explicit
        save_data(data)
        return True
    else:
        return False

async def get_channel_duration(guild_id: int, channel_id: int):
    """Get time of a Audio Channel to bot enter
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    
    ### Returns:
    Duration if success.
    None if fail"""
    data = load_data()
    if str(guild_id) in data:
        if str(channel_id) in data[str(guild_id)]:
            duration = data[str(guild_id)][str(channel_id)]["duration"]
            return int(duration)
        else:
            return None
    else:
        return None

async def get_audio_duration(guild_id: int, channel_id: int):
    """Get audio duration of a Audio Channel
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    
    ### Returns:
    Audio Duration if success.
    None if fail"""
    data = load_data()
    if str(guild_id) in data:
        if str(channel_id) in data[str(guild_id)]:
            audio_duration = data[str(guild_id)][str(channel_id)]["audio_duration"]
            return audio_duration
        else:
            return None
    else:
        return None

async def get_provability(guild_id: int, channel_id: int):
    """Get provability of a Audio Channel
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    
    ### Returns:
    Provability if success.
    None if fail"""
    data = load_data()
    if str(guild_id) in data:
        if str(channel_id) in data[str(guild_id)]:
            provability = data[str(guild_id)][str(channel_id)]["provability"]
            return int(provability)
        else:
            return None
    else:
        return None

async def get_channel_ids(guild_id: int):
    """Returns all ids in guild
    
    ### Atrbuttes:
    Guild Id: int 
    ### Returns:
    List of Ids or None"""
    data = load_data()
    if str(guild_id) in data:
        return list(data[str(guild_id)].keys())
    else:
        return None

def is_explicit(guild_id: int, channel_id: int) -> bool:
    """Check if the channel is marked as explicit.
    
    ### Atributtes:
    Guild Id : int
    Channel Id : int
    
    ### Returns:
    True if explicit, False otherwise.
    """
    data = load_data()
    if str(guild_id) in data and str(channel_id) in data[str(guild_id)]:
        return data[str(guild_id)][str(channel_id)].get("explicit", False)
    return False