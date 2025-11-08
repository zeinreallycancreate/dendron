"""
Device name generator - creates memorable single-word names for devices
"""

import hashlib


class DeviceNameGenerator:
    """
    Generates unique, memorable single-word names for devices
    Based on MAC address hash for consistency
    """
    
    # Curated lists of words for generating names
    ADJECTIVES = [
        "Swift", "Bright", "Silent", "Bold", "Quick", "Calm", "Wise", "Noble",
        "Brave", "Fierce", "Gentle", "Mighty", "Rapid", "Sturdy", "Clever",
        "Swift", "Agile", "Sharp", "Keen", "Vivid", "Elegant", "Graceful",
        "Nimble", "Vibrant", "Radiant", "Daring", "Robust", "Sleek", "Smart",
        "Lively", "Blazing", "Crystal", "Dynamic", "Epic", "Flash", "Golden",
        "Heroic", "Iconic", "Jolly", "Kinetic", "Lunar", "Mystic", "Nordic"
    ]
    
    NOUNS = [
        "Phoenix", "Dragon", "Eagle", "Wolf", "Tiger", "Falcon", "Hawk",
        "Lion", "Bear", "Panther", "Raven", "Cobra", "Lynx", "Jaguar",
        "Puma", "Cheetah", "Leopard", "Orca", "Shark", "Dolphin", "Whale",
        "Thunder", "Lightning", "Storm", "Comet", "Meteor", "Star", "Moon",
        "Sun", "Nova", "Pulsar", "Nebula", "Galaxy", "Cosmos", "Aurora",
        "Horizon", "Zenith", "Summit", "Peak", "Crest", "Crown", "Throne",
        "Atlas", "Orion", "Perseus", "Titan", "Olympus", "Valhalla", "Asgard"
    ]
    
    SINGLE_WORDS = [
        # Technology themed
        "Nexus", "Vector", "Cipher", "Matrix", "Prism", "Quantum", "Pulse",
        "Echo", "Signal", "Beacon", "Relay", "Node", "Circuit", "Binary",
        "Digital", "Photon", "Electron", "Proton", "Neutron", "Atom",
        
        # Nature themed
        "Cascade", "Breeze", "Ripple", "Tide", "Wave", "Current", "Stream",
        "River", "Ocean", "Mountain", "Valley", "Forest", "Desert", "Tundra",
        "Glacier", "Volcano", "Canyon", "Mesa", "Prairie", "Savanna",
        
        # Space themed
        "Voyager", "Pioneer", "Explorer", "Odyssey", "Quest", "Journey",
        "Venture", "Expedition", "Discovery", "Frontier", "Horizon", "Beyond",
        
        # Abstract
        "Essence", "Spirit", "Soul", "Mind", "Vision", "Dream", "Hope",
        "Faith", "Truth", "Honor", "Glory", "Victory", "Triumph", "Champion",
        "Legend", "Myth", "Saga", "Epic", "Tale", "Story"
    ]
    
    @staticmethod
    def generate_name(mac_address: str) -> str:
        """
        Generate a consistent single-word name based on MAC address
        Same MAC always gets the same name
        """
        # Create hash of MAC address
        mac_hash = hashlib.sha256(mac_address.encode()).hexdigest()
        
        # Convert to number
        hash_int = int(mac_hash[:16], 16)
        
        # Choose from single words (70% chance)
        if hash_int % 10 < 7:
            word_index = hash_int % len(DeviceNameGenerator.SINGLE_WORDS)
            name = DeviceNameGenerator.SINGLE_WORDS[word_index]
        else:
            # Combine adjective + noun (30% chance)
            adj_index = hash_int % len(DeviceNameGenerator.ADJECTIVES)
            noun_index = (hash_int // len(DeviceNameGenerator.ADJECTIVES)) % len(DeviceNameGenerator.NOUNS)
            name = f"{DeviceNameGenerator.ADJECTIVES[adj_index]}{DeviceNameGenerator.NOUNS[noun_index]}"
        
        return name
